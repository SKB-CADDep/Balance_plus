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
    def run_multi_calculation(
        globals_data: CalculationGlobals, 
        groups_data: list[tuple[ValveGroupInput, ValveInfo]]
    ) -> MultiCalculationResult:
        try:
            # 1. НОРМАЛИЗАЦИЯ ГЛОБАЛЬНЫХ ПАРАМЕТРОВ
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

            details = []
            
            # Переменные для агрегации (сумма G и числитель для энтальпии)
            sk_g, sk_gh = 0.0, 0.0
            rk_g, rk_gh = 0.0, 0.0

            # 2. ЦИКЛ ПО ГРУППАМ КЛАПАНОВ
            for group_in, valve_info in groups_data:
                # Геометрия
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

                # Термодинамика группы
                p_in_mpa = [converter.convert(p, from_unit=group_in.p_values_unit, to_unit="МПа", parameter_type="pressure") for p in group_in.p_values[:count_parts]]
                if not p_in_mpa:
                    p_in_mpa = [p_fresh_mpa] * count_parts # Фолбэк, если юзер не передал p_values

                p_suctions_mpa = [converter.convert(p, from_unit=group_in.p_leak_offs_unit, to_unit="МПа", parameter_type="pressure") for p in group_in.p_leak_offs]
                p_suctions_mpa.append(p_lst_mpa) # Глобальный отсос всегда последний!

                thermo = ThermoConditions(
                    count_valves=1, # Ядро считает для 1 штуки, умножаем потом
                    p_in_mpa=p_in_mpa,
                    t_start_c=t_start_c,
                    h_start_kj_kg=h_start_kj,
                    t_air_c=t_air_c,
                    p_suctions_mpa=p_suctions_mpa
                )

                # Вызов Ядра
                engine = ValvePhysicsEngine(geo=geo, thermo=thermo)
                raw = engine.execute()

                # Умножение на количество в группе
                qty = group_in.quantity
                group_total_g = raw.gi_t_h[0] * qty

                # Агрегация (Сводные таблицы)
                if "СК" in group_in.type:
                    sk_g += group_total_g
                    sk_gh += group_total_g * raw.hi_kj_kg[0]
                elif "РК" in group_in.type:
                    rk_g += group_total_g
                    rk_gh += group_total_g * raw.hi_kj_kg[0]

                # Формирование ответа по одной группе
                pi_out = [converter.convert(p, from_unit="МПа", to_unit="кгс/см²", parameter_type="pressure") for p in raw.pi_in_mpa]
                dea_p_out = converter.convert(raw.dea_p_mpa, from_unit="МПа", to_unit="кгс/см²", parameter_type="pressure") if raw.dea_p_mpa else 0.0
                
                ej_props_out = []
                for ej in raw.ej_results:
                    ej_p_out = converter.convert(ej["p_mpa"], from_unit="МПа", to_unit="кгс/см²", parameter_type="pressure") if ej["p_mpa"] else 0.0
                    ej_props_out.append({"g": ej["g"] * qty, "t": ej["t"], "h": ej["h"], "p": ej_p_out})

                details.append(GroupCalculationDetails(
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
                ))

            # 3. ФОРМИРОВАНИЕ СВОДНЫХ ТАБЛИЦ (SUMMARY)
            sk_summary = TypeSummary(total_g=sk_g, mixed_h=(sk_gh / sk_g) if sk_g > 0 else 0.0)
            rk_summary = TypeSummary(total_g=rk_g, mixed_h=(rk_gh / rk_g) if rk_g > 0 else 0.0)

            return MultiCalculationResult(
                details=details,
                summary=CalculationSummary(sk=sk_summary, rk=rk_summary)
            )

        except (PhysicsEngineError, AdapterError) as e:
            logger.error(f"Calculation Error: {e}")
            raise ValueError(str(e))
        except Exception as e:
            logger.exception("System error")
            raise ValueError(f"Системная ошибка: {e}")
