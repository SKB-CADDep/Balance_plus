"""
Контрольные примеры из документации (раздел 8).
"""

import pytest
from .conftest import build_calculation_params, load_geometry, load_mode


class TestDocumentationVerification:
    """
    Контрольные примеры из раздела 8 документации.

    Общие условия:
    - G_steam = 200 т/ч
    - t1_main = t1_builtin = 20°C
    - coefficient_b = 1.0
    """

    @pytest.fixture(scope="class")
    def verification_geometry(self):
        return load_geometry("geometry")

    @pytest.fixture(scope="class")
    def verification_mode(self):
        return load_mode(1)

    @pytest.mark.parametrize(
        "scenario_name, W_main, W_builtin, expected_t_sat",
        [
            pytest.param("Только ОП", 12000.0, 0.0, 30.898, id="scenario_1_main_only"),
            pytest.param("ОП + ВП", 12000.0, 4000.0, 28.173, id="scenario_2_both"),
            pytest.param("Только ВП", 0.0, 4000.0, 52.694, id="scenario_3_builtin_only"),
        ],
    )
    def test_saturation_temperature(
        self,
        strategy,
        verification_geometry,
        verification_mode,
        scenario_name,
        W_main,
        W_builtin,
        expected_t_sat,
    ):
        params = build_calculation_params(
            geometry=verification_geometry,
            mode=verification_mode,
            W_main=W_main,
            W_builtin=W_builtin,
            t1_main=20.0,
            t1_builtin=20.0,
            G_steam=200.0,
            coefficient_b=1.0,
            G_air=0.0,
        )

        result = strategy.calculate(params)

        assert len(result["main_results"]) > 0, f"Сценарий '{scenario_name}': результаты не получены"

        calculated_t_sat = result["main_results"][0]["t_sat"]

        assert calculated_t_sat == pytest.approx(expected_t_sat, abs=0.01), (
            f"Сценарий '{scenario_name}':\n"
            f"  Ожидаемое t_sat = {expected_t_sat}°C\n"
            f"  Рассчитанное t_sat = {calculated_t_sat:.3f}°C"
        )

    @pytest.mark.parametrize(
        "num_ejectors, expected_pressure_atm",
        [
            pytest.param(1, 0.03955, id="single_ejector"),
            pytest.param(2, 0.03702, id="dual_ejector"),
        ],
    )
    def test_ejector_pressure(
        self,
        strategy,
        verification_geometry,
        verification_mode,
        num_ejectors,
        expected_pressure_atm,
    ):
        params = build_calculation_params(
            geometry=verification_geometry,
            mode=verification_mode,
            W_main=12000.0,
            W_builtin=4000.0,
            t1_main=20.0,
            t1_builtin=20.0,
            G_steam=200.0,
            coefficient_b=1.0,
            G_air=16.5,
        )

        result = strategy.calculate(params)

        ejector_results = [
            ej for ej in result["ejector_results"] if ej["number_of_ejectors"] == num_ejectors
        ]

        assert len(ejector_results) > 0, f"Результат для {num_ejectors} эжектора(ов) не найден"

        calculated = ejector_results[0]["P_ejector_atm"]

        assert calculated == pytest.approx(expected_pressure_atm, rel=0.01), (
            f"Эжектор ({num_ejectors} шт.):\n"
            f"  Ожидаемое P = {expected_pressure_atm} кгс/см²\n"
            f"  Рассчитанное P = {calculated:.5f} кгс/см²"
        )

