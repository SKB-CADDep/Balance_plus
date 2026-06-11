"""
Адаптер расчетного ядра конденсаторов.

Выступает связующим звеном (мостом) между HTTP-слоем (API, схемы Pydantic, ORM) 
и математическим ядром (стратегии Бермана и Метро-Виккерса). 
Отвечает за подготовку физических данных, диспетчеризацию расчетов, 
итерационное уточнение теплофизических свойств (BR-12) и форматирование 
результатов в стандартизированные матрицы.
"""

import time
import logging
from typing import Callable

import numpy as np

from app.core.converter import converter
from app.core.exceptions import (
    MaterialPropertyError,
    UnitConversionError,
    CalculationEngineError,
)
from app.utils.berman_strategy import BermanStrategy
from app.utils.metrovickers_strategy import MetroVickersStrategy
from app.utils.table_models import Table1D

from app.core.condenser_validators import (
    validate_water_flow_limits,
    validate_temperature_ranges
)

from app.schemas.calculation import (
    CalculationInput,
    CalculationOutput,
    MatrixResult,
    EjectorResult,
)
from app.models.condenser import Condenser
from app.models.material import Material

logger = logging.getLogger(__name__)


class CondenserCalculationAdapter:
    """
    Класс-адаптер для управления процессом расчета конденсатора.
    """

    def calculate(
        self,
        input_data: CalculationInput,
        condenser: Condenser,
        material: Material,
    ) -> CalculationOutput:
        """Основной метод запуска и маршрутизации расчета."""
        start = time.perf_counter()

        logger.info(
            "Starting calculation",
            extra={
                "method": input_data.method,
                "condenser_id": condenser.id,
                "material_id": material.id,
                "num_tables_expected": len(input_data.coefficient_b) * max(len(input_data.W_main), len(input_data.W_builtin or [])),
            }
        )

        try:
            lambda_interp = self._build_lambda_interpolator(material)

            if input_data.method == "berman":
                tables, ejector_results = self._run_berman(input_data, condenser, lambda_interp)
            else:
                tables = self._run_metrovickers(input_data, condenser, lambda_interp)
                ejector_results = []

            elapsed_ms = (time.perf_counter() - start) * 1000

            logger.info(
                "Calculation completed successfully",
                extra={
                    "method": input_data.method,
                    "tables_count": len(tables),
                    "duration_ms": round(elapsed_ms, 2),
                }
            )

            return CalculationOutput(
                condenser_id=condenser.id,
                condenser_name=condenser.name_condenser,
                method=input_data.method,
                tables=tables,
                ejector_results=ejector_results,
                total_tables=len(tables),
                calculation_time_ms=round(elapsed_ms, 2),
            )

        except Exception as e:
            logger.error(
                f"Calculation failed for Method: {input_data.method}, "
                f"Condenser: {condenser.id}, Material: {material.id}. Error: {str(e)}", 
                exc_info=True
            )
            raise CalculationEngineError(
                message="Ошибка при выполнении расчёта конденсатора",
                details=str(e)
            ) from e

    def _build_lambda_interpolator(self, material: Material) -> Table1D:
        points = material.thermal_conductivity_points

        if not points or len(points) < 2:
            raise MaterialPropertyError(
                message=f"Материал '{material.name}' не содержит достаточных данных по теплопроводности",
                details=f"material_id={material.id}"
            )

        x = np.array([p[0] for p in points])
        y = np.array([p[1] for p in points])

        logger.debug("Создан интерполятор теплопроводности (точек: %d)", len(x))
        return Table1D(x_cords=x, y_cords=y)

    def _get_lambda_iterative(
        self,
        lambda_interp: Table1D,
        t_avg_initial: float,
        single_calc_func: Callable[[float], float],
        max_iter: int = 8,
        tol: float = 0.01,
    ) -> float:
        t_avg = float(t_avg_initial)
        for i in range(max_iter):
            lam = float(lambda_interp(t_avg))
            new_t_avg = single_calc_func(lam)

            logger.debug("Итерация %d: t_avg=%.2f, lambda=%.4f, new_t_avg=%.2f", i, t_avg, lam, new_t_avg)

            if abs(new_t_avg - t_avg) < tol:
                return lam
            t_avg = new_t_avg

        return float(lambda_interp(t_avg))

    # ===================================================================
    # BERMAN PATH
    # ===================================================================

    def _run_berman(
        self,
        input_data: CalculationInput,
        condenser: Condenser,
        lambda_interp: Table1D,
    ):
        logger.info("Running Berman strategy")

        # Получаем базовую среднюю температуру через метод, в котором уже вшита проверка if not input_data.t1_main
        t_avg_est = self._estimate_t_avg_berman(input_data, 0.0) + 5.0

        lam = self._get_lambda_iterative(
            lambda_interp,
            t_avg_est,
            lambda lam_val: self._estimate_t_avg_berman(input_data, lam_val)
        )

        params = self._prepare_berman_params(input_data, condenser, lam)

        engine = BermanStrategy()
        raw = engine.calculate(params)

        tables = self._reshape_berman_results(raw["main_results"], input_data, condenser)
        ejectors = [EjectorResult(**e) for e in raw.get("ejector_results", [])]

        return tables, ejectors

    def _prepare_berman_params(self, input_data: CalculationInput, condenser: Condenser, lam: float) -> dict:
        try:
            h_steam = converter.convert(
                input_data.H_steam,
                from_unit=input_data.H_steam_unit,
                to_unit="ккал/кг",
                parameter_type="enthalpy"
            ) if input_data.H_steam is not None else 0.0
        except Exception as e:
            raise UnitConversionError(
                message="Не удалось конвертировать энтальпию пара",
                details=f"H_steam={input_data.H_steam} {input_data.H_steam_unit}"
            ) from e

        return {
            'L_main': condenser.main_length,
            'L_builtin': condenser.builtin_length or 0.0,
            'Z_main': input_data.Z_main,
            'Z_builtin': input_data.Z_builtin or 0,
            'N_main': condenser.main_count,
            'N_builtin': condenser.builtin_count or 0,
            'H_steam': h_steam,
            'G_nom': condenser.mass_flow_steam_nom,
            'lambda': lam,
            'd_in': condenser.diameter_internal,
            'S_tube': condenser.wall_thickness,
            'W_main_list': input_data.W_main,
            'W_builtin_list': input_data.W_builtin or [],
            't1_main_list': input_data.t1_main,
            't1_builtin_list': input_data.t1_builtin or input_data.t1_main,
            'G_steam_list': input_data.G_steam,
            'coefficient_b_list': input_data.coefficient_b,
            'G_air': condenser.mass_flow_air,
        }

    def _estimate_t_avg_berman(self, input_data: CalculationInput, lam: float) -> float:
        if not input_data.t1_main:
            raise ValueError("Массив t1_main не может быть пустым")
        return sum(input_data.t1_main) / len(input_data.t1_main)

    def _reshape_berman_results(self, flat_results: list[dict], input_data: CalculationInput, condenser: Condenser):
        len_W = max(len(input_data.W_main), len(input_data.W_builtin or []))
        len_b = len(input_data.coefficient_b)
        len_t = len(input_data.t1_main)
        len_G = len(input_data.G_steam)

        tables = []
        idx = 0

        for w_i in range(len_W):
            for b_i in range(len_b):
                chunk = flat_results[idx: idx + len_t * len_G]

                matrix = []
                for t_j in range(len_t):
                    row = [chunk[t_j * len_G + g_k].get('P_steam_seuif_atm', 0.0) for g_k in range(len_G)]
                    matrix.append(row)

                w_main = input_data.W_main[w_i] if w_i < len(input_data.W_main) else 0.0
                w_builtin = input_data.W_builtin[w_i] if input_data.W_builtin and w_i < len(input_data.W_builtin) else 0.0

                warnings = validate_water_flow_limits(w_main, w_builtin, condenser.water_flow_limits)
                t1_warnings = validate_temperature_ranges("berman", input_data.t1_main)
                warnings.extend(t1_warnings)

                tables.append(MatrixResult(
                    meta={
                        "coefficient_b": input_data.coefficient_b[b_i],
                        "W_main": w_main,
                        "W_builtin": w_builtin,
                    },
                    columns=input_data.G_steam,
                    rows=input_data.t1_main,
                    values=matrix,
                    warnings=warnings,
                ))
                idx += len_t * len_G

        return tables

    # ===================================================================
    # METROVICKERS PATH
    # ===================================================================

    def _run_metrovickers(
        self,
        input_data: CalculationInput,
        condenser: Condenser,
        lambda_interp: Table1D,
    ):
        logger.info("Running MetroVickers strategy")

        engine = MetroVickersStrategy()
        tables = []

        len_W = max(len(input_data.W_main), len(input_data.W_builtin or []))

        for b in input_data.coefficient_b:
            for w_i in range(len_W):
                # Объявляем переменные расходов ровно один раз! (Избегаем дублирования)
                w_main = input_data.W_main[w_i] if w_i < len(input_data.W_main) else 0.0
                w_builtin = input_data.W_builtin[w_i] if input_data.W_builtin and w_i < len(input_data.W_builtin) else 0.0

                matrix = []
                is_extrapolated_matrix = False
                
                for t1 in input_data.t1_main:
                    t_avg_est = t1 + 3.0
                    lam = self._get_lambda_iterative(
                        lambda_interp, t_avg_est,
                        lambda lam_val: self._estimate_t_avg_metrovickers(t1, w_main, lam_val)
                    )

                    row = []
                    for g in input_data.G_steam:
                        params = self._prepare_metrovickers_params(
                            input_data, condenser, lam, t1, w_main, g, b
                        )
                        result = engine.calculate(params)
                        row.append(result['pressure_flow_path_1'])
                        
                        if result.get('is_extrapolated'):
                            is_extrapolated_matrix = True

                    matrix.append(row)

                warnings = validate_water_flow_limits(w_main, w_builtin, condenser.water_flow_limits)
                t1_warnings = validate_temperature_ranges("metro-vickers", input_data.t1_main)
                warnings.extend(t1_warnings)

                if is_extrapolated_matrix:
                    warnings.append("Данные не подтверждены экспериментально")

                tables.append(MatrixResult(
                    meta={
                        "coefficient_b": b,
                        "W_main": w_main,
                        "W_builtin": w_builtin,
                    },
                    columns=input_data.G_steam,
                    rows=input_data.t1_main,
                    values=matrix,
                    warnings=warnings,
                ))

        return tables

    def _prepare_metrovickers_params(
        self,
        input_data: CalculationInput,
        condenser: Condenser,
        lam: float,
        t1: float,
        w_main: float,
        g: float,
        b: float,
    ):
        return {
            'diameter_inside_of_pipes': condenser.diameter_internal,
            'thickness_pipe_wall': condenser.wall_thickness,
            'length_cooling_tubes_of_the_main_bundle': condenser.main_length,
            'number_cooling_tubes_of_the_main_bundle': condenser.main_count,
            'number_cooling_tubes_of_the_built_in_bundle': condenser.builtin_count or 0,
            'number_cooling_water_passes_of_the_main_bundle': input_data.Z_main,
            'mass_flow_cooling_water': w_main,
            'temperature_cooling_water_1': t1,
            'thermal_conductivity_cooling_surface_tube_material': lam,
            'coefficient_b': b,
            'mass_flow_flow_path_1': g,
            'degree_dryness_flow_path_1': input_data.X_steam,
            'number_air_cooler_total_pipes': condenser.aircooler_count,
        }

    def _estimate_t_avg_metrovickers(self, t1: float, w_main: float, lam: float) -> float:
        return t1 + 3.0
