import logging

from seuif97 import ph2t, pt2h

from app.core.converter import converter

# Импортируем наше чистое Ядро
from app.domain.models import ThermoConditions, ValveGeometry
from app.domain.valve_physics_engine import PhysicsEngineError, ValvePhysicsEngine
from app.schemas import CalculationParams, CalculationResult, ValveInfo


logger = logging.getLogger(__name__)


class AdapterError(Exception):
    """Ошибка валидации данных перед передачей в ядро"""
    pass


class CalculationAdapter:
    """
    Адаптер-Оркестратор. 
    Переводит данные с языка Web (Pydantic + юзерские единицы) 
    на язык Domain (Dataclass + СИ/МПа) и обратно.
    """

    @staticmethod
    def run_calculation(params: CalculationParams, valve_info: ValveInfo) -> CalculationResult:
        try:
            # ==========================================
            # 1. ПОДГОТОВКА ГЕОМЕТРИИ (перевод мм -> м)
            # ==========================================
            raw_lengths = getattr(valve_info, "section_lengths", []) or []
            len_parts_m = [float(L) / 1000.0 for L in raw_lengths if L is not None]

            count_parts = len(len_parts_m)
            if count_parts < 2:
                raise AdapterError("Клапан должен иметь как минимум два участка.")

            geo = ValveGeometry(
                count_parts=count_parts,
                diameter_m=float(valve_info.diameter) / 1000.0,
                clearance_m=float(valve_info.clearance) / 1000.0,
                radius_rounding_m=float(valve_info.round_radius or 2.0) / 1000.0,
                len_parts_m=len_parts_m
            )

            # ==========================================
            # 2. ПОДГОТОВКА ТЕРМОДИНАМИКИ (UnitConverter)
            # ==========================================

            # Давления: юзерские единицы -> МПа
            p_values_in = list(params.p_values[:count_parts])
            p_in_mpa = [
                converter.convert(p, from_unit=params.p_values_unit, to_unit="МПа", parameter_type="pressure")
                for p in p_values_in
            ]

            p_suctions_raw = list(params.p_ejector or [])
            p_suctions_mpa = [
                converter.convert(p, from_unit=params.p_ejector_unit, to_unit="МПа", parameter_type="pressure")
                for p in p_suctions_raw
            ]

            # Температура воздуха: юзерские единицы -> °C
            t_air_c = converter.convert(
                params.t_air, from_unit=params.t_air_unit, to_unit="°C", parameter_type="temperature"
            )

            # Логика взаимоисключения Температура / Энтальпия
            if params.temperature_start is not None:
                t_start_c = converter.convert(
                    params.temperature_start, from_unit=params.temperature_start_unit, to_unit="°C", parameter_type="temperature"
                )
                h_start_kj = pt2h(p_in_mpa[0], t_start_c)
            elif params.enthalpy_start is not None:
                h_start_kj = converter.convert(
                    params.enthalpy_start, from_unit=params.enthalpy_start_unit, to_unit="кДж/кг", parameter_type="enthalpy"
                )
                t_start_c = ph2t(p_in_mpa[0], h_start_kj)
            else:
                raise AdapterError("Не задана ни температура, ни энтальпия свежего пара.")

            thermo = ThermoConditions(
                count_valves=int(params.count_valves),
                p_in_mpa=p_in_mpa,
                t_start_c=t_start_c,
                h_start_kj_kg=h_start_kj,
                t_air_c=t_air_c,
                p_suctions_mpa=p_suctions_mpa
            )

            # ==========================================
            # 3. ВЫЗОВ ФИЗИЧЕСКОГО ДВИЖКА (ЯДРА)
            # ==========================================
            engine = ValvePhysicsEngine(geo=geo, thermo=thermo)
            raw_result = engine.execute()

            # ==========================================
            # 4. ФОРМИРОВАНИЕ ОТВЕТА (Перевод МПа -> База)
            # ==========================================
            # Возвращаем давления обратно в те единицы, которые мы считаем
            # "дефолтными" для отдачи на фронтенд (раньше было кгс/см2).
            # Если фронтенд захочет получать ответ в тех же единицах, что и вводил,
            # мы можем использовать `to_unit=params.p_values_unit`. Пока оставляем кгс/см2.

            pi_out = [
                converter.convert(p, from_unit="МПа", to_unit="кгс/см²", parameter_type="pressure")
                for p in raw_result.pi_in_mpa
            ]

            dea_p_out = converter.convert(
                raw_result.dea_p_mpa, from_unit="МПа", to_unit="кгс/см²", parameter_type="pressure"
            ) if raw_result.dea_p_mpa else 0.0

            ej_props_out = []
            for ej in raw_result.ej_results:
                ej_p_out = converter.convert(
                    ej["p_mpa"], from_unit="МПа", to_unit="кгс/см²", parameter_type="pressure"
                ) if ej["p_mpa"] else 0.0

                ej_props_out.append({
                    "g": ej["g"], "t": ej["t"], "h": ej["h"], "p": ej_p_out
                })

            # Собираем итоговую Pydantic-схему
            return CalculationResult(
                Gi=raw_result.gi_t_h,
                Pi_in=pi_out,
                Ti=raw_result.ti_c,
                Hi=raw_result.hi_kj_kg,
                deaerator_props=[raw_result.dea_g, raw_result.dea_t, raw_result.dea_h, dea_p_out],
                ejector_props=ej_props_out
            )

        except (PhysicsEngineError, AdapterError) as e:
            # Эти ошибки мы сами вызвали, они понятные
            logger.error(f"Calculation Error: {e}")
            raise ValueError(str(e))
        except Exception as e:
            # Непредвиденные падения
            logger.exception("Unexpected error in CalculationAdapter")
            raise ValueError(f"Системная ошибка при расчете: {e}")
