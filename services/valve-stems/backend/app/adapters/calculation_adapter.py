import logging
from seuif97 import pt2h, ph2t

from app.schemas import (
    CalculationGlobals, ValveGroupInput, MultiCalculationResult,
    GroupCalculationDetails, TypeSummary, CalculationSummary, ValveInfo
)
from app.core.converter import converter
from app.domain.models import ValveGeometry, ThermoConditions
from app.domain.valve_physics_engine import ValvePhysicsEngine, PhysicsEngineError

logger = logging.getLogger(__name__)

class AdapterError(Exception):
    pass

class CalculationAdapter:
    
    @staticmethod
    def _process_single_group(
        group_in: ValveGroupInput, 
        valve_info: ValveInfo, 
        p_fresh_mpa: float, 
        t_start_c: float, 
        h_start_kj: float, 
        t_air_c: float, 
        p_lst_mpa: float
    ) -> tuple[GroupCalculationDetails, float, float]:
        
        raw_lengths = getattr(valve_info, "section_lengths", []) or []
        len_parts_m = [float(L) / 1000.0 for L in raw_lengths if L is not None]
        
        count_parts = len(len_parts_m)
        if count_parts < 2:
            raise AdapterError(f"Клапан {valve_info.name} должен иметь как минимум 2 участка.")

        geo = ValveGeometry(
            count_parts=count_parts,
            diameter_m=float(valve_info.diameter) / 1000.0,
            clearance_m=float(valve_info.clearance) / 1000.0,
            radius_rounding_m=float(valve_info.round_radius or 2.0) / 1000.0,
            len_parts_m=len_parts_m
        )

        # -------------------------------------------------------------------
        # ИДЕАЛЬНАЯ МАТЕМАТИКА РАСПРЕДЕЛЕНИЯ ДАВЛЕНИЙ
        # -------------------------------------------------------------------
        expected_user_inputs = max(0, count_parts - 2)

        if len(group_in.p_leak_offs) != expected_user_inputs:
            raise AdapterError(
                f"Для клапана с {count_parts} участками требуется ровно {expected_user_inputs} "
                f"промежуточных отсосов. Получено: {len(group_in.p_leak_offs)}."
            )

        # 1. Конвертируем пользовательские отсосы в МПа
        user_inputs_mpa = [
            converter.convert(p, from_unit=group_in.p_leak_offs_unit, to_unit="МПа", parameter_type="pressure") 
            for p in group_in.p_leak_offs
        ]

        # 2. Строим массив P_in для Ядра (Свежий пар + Промежуточные + Вакуум)
        p_in_mpa = [p_fresh_mpa] + user_inputs_mpa + [p_lst_mpa]

        # 3. Строим массив Отсосов для Ядра 
        # (Откидываем первый отсос - Деаэратор, остальные отдаем Эжекторам + глобальный Вакуум)
        p_suctions_mpa = user_inputs_mpa[1:] + [p_lst_mpa]
        # -------------------------------------------------------------------

        thermo = ThermoConditions(
            count_valves=1,
            p_in_mpa=p_in_mpa,
            t_start_c=t_start_c,
            h_start_kj_kg=h_start_kj,
            t_air_c=t_air_c,
            p_suctions_mpa=p_suctions_mpa
        )

        engine = ValvePhysicsEngine(geo=geo, thermo=thermo)
        raw = engine.execute()

        qty = group_in.quantity
        group_total_g = raw.gi_t_h[0] * qty
        h_part = raw.hi_kj_kg[0]

        pi_out = [converter.convert(p, from_unit="МПа", to_unit="кгс/см²", parameter_type="pressure") for p in raw.pi_in_mpa]
        dea_p_out = converter.convert(raw.dea_p_mpa, from_unit="МПа", to_unit="кгс/см²", parameter_type="pressure") if raw.dea_p_mpa else 0.0
        
        ej_props_out = []
        for ej in raw.ej_results:
            ej_p_out = converter.convert(ej["p_mpa"], from_unit="МПа", to_unit="кгс/см²", parameter_type="pressure") if ej["p_mpa"] else 0.0
            ej_props_out.append({"g": ej["g"] * qty, "t": ej["t"], "h": ej["h"], "p": ej_p_out})

        details = GroupCalculationDetails(
            valve_id=group_in.valve_id,
            type=group_in.type,
            valve_names=group_in.valve_names,
            quantity=qty,
            Gi=raw.gi_t_h,
            Pi_in=pi_out,
            Ti=raw.ti_c,
            Hi=raw.hi_kj_kg,
            deaerator_props=[raw.dea_g * qty, raw.dea_t, raw.dea_h, dea_p_out],
            ejector_props=ej_props_out,
            group_total_g=group_total_g
        )
        
        return details, group_total_g, h_part

    @staticmethod
    def run_multi_calculation(
        globals_data: CalculationGlobals, 
        groups_data: list[tuple[ValveGroupInput, ValveInfo]]
    ) -> MultiCalculationResult:
        try:
            p_fresh_mpa = converter.convert(globals_data.P_fresh, from_unit=globals_data.P_fresh_unit, to_unit="МПа", parameter_type="pressure")
            t_air_c = converter.convert(globals_data.T_air, from_unit=globals_data.T_air_unit, to_unit="°C", parameter_type="temperature")
            p_lst_mpa = converter.convert(globals_data.P_lst_leak_off, from_unit=globals_data.P_lst_leak_off_unit, to_unit="МПа", parameter_type="pressure")

            if globals_data.T_fresh is not None:
                t_start_c = converter.convert(globals_data.T_fresh, from_unit=globals_data.T_fresh_unit, to_unit="°C", parameter_type="temperature")
                h_start_kj = pt2h(p_fresh_mpa, t_start_c)
            elif globals_data.H_fresh is not None:
                h_start_kj = converter.convert(globals_data.H_fresh, from_unit=globals_data.H_fresh_unit, to_unit="кДж/кг", parameter_type="enthalpy")
                t_start_c = ph2t(p_fresh_mpa, h_start_kj)
            else:
                raise AdapterError("Не задана температура или энтальпия свежего пара.")

            details_list = []
            sk_g, sk_gh = 0.0, 0.0
            rk_g, rk_gh = 0.0, 0.0
            srk_g, srk_gh = 0.0, 0.0

            for group_in, valve_info in groups_data:
                details, total_g, h_part = CalculationAdapter._process_single_group(
                    group_in, valve_info, p_fresh_mpa, t_start_c, h_start_kj, t_air_c, p_lst_mpa
                )
                details_list.append(details)

                if "СРК" in group_in.type or "Стопорно-регулирующий" in group_in.type:
                    srk_g += total_g
                    srk_gh += total_g * h_part
                elif "СК" in group_in.type or "Стопорный" in group_in.type:
                    sk_g += total_g
                    sk_gh += total_g * h_part
                elif "РК" in group_in.type or "Регулирующий" in group_in.type:
                    rk_g += total_g
                    rk_gh += total_g * h_part

            sk_summary = TypeSummary(total_g=sk_g, mixed_h=(sk_gh / sk_g) if sk_g > 0 else 0.0)
            rk_summary = TypeSummary(total_g=rk_g, mixed_h=(rk_gh / rk_g) if rk_g > 0 else 0.0)
            srk_summary = TypeSummary(total_g=srk_g, mixed_h=(srk_gh / srk_g) if srk_g > 0 else 0.0)

            return MultiCalculationResult(details=details_list, summary=CalculationSummary(sk=sk_summary, rk=rk_summary, srk=srk_summary))

        except (PhysicsEngineError, AdapterError) as e:
            logger.error(f"Calculation Error: {e}")
            raise ValueError(str(e))
        except Exception as e:
            logger.exception("System error")
            raise ValueError(f"Системная ошибка: {e}")