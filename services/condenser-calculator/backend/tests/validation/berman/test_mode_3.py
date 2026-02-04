"""
Валидационные тесты для режима 3: только основной пучок.
Особенность: W_builtin = 0.
"""

import pytest

from .conftest import (
    assert_pressure_approx,
    build_calculation_params,
    find_mode_in_results,
    generate_ejector_test_cases,
    generate_test_cases_from_results,
    get_expected_pressure,
    load_geometry,
    load_mode,
    load_results,
)


_geometry = load_geometry("geometry")
_mode = load_mode(3)
_results = load_results(3)
_test_cases = generate_test_cases_from_results(_results, _mode)
_ejector_cases = generate_ejector_test_cases(_results)


class TestPressureMatrixMode3:
    """Полная проверка матрицы давлений для режима 'только ОП'."""

    @pytest.mark.parametrize("case", _test_cases, ids=[c["id"] for c in _test_cases])
    def test_pressure_calculation(self, strategy, case):
        assert case["W_builtin"] == 0.0, "Mode 3 должен иметь W_builtin = 0"

        params = build_calculation_params(
            geometry=_geometry,
            mode=_mode,
            W_main=case["W_main"],
            W_builtin=0.0,
            t1_main=case["t1_main"],
            t1_builtin=case["t1_main"],
            G_steam=case["G_steam"],
            coefficient_b=case["coefficient_b"],
            G_air=0.0,
        )

        result = strategy.calculate(params)
        assert len(result["main_results"]) > 0

        calculated = result["main_results"][0]["P_steam_formula_atm"]

        assert_pressure_approx(calculated=calculated, expected=case["expected_pressure"], context=f"Тест: {case['id']}")


class TestMainBundleOnlyVsBothBundles:
    """Сравнение режима 'только ОП' с режимом 'ОП+ВП'."""

    @pytest.fixture
    def results_1(self):
        return load_results(1)

    def test_pressure_higher_without_builtin(self, strategy, results_1):
        params_main_only = build_calculation_params(
            geometry=_geometry,
            mode=_mode,
            W_main=12000.0,
            W_builtin=0.0,
            t1_main=20.0,
            t1_builtin=20.0,
            G_steam=200.0,
            coefficient_b=1.0,
        )

        mode_1 = load_mode(1)
        params_both = build_calculation_params(
            geometry=_geometry,
            mode=mode_1,
            W_main=12000.0,
            W_builtin=3500.0,
            t1_main=20.0,
            t1_builtin=20.0,
            G_steam=200.0,
            coefficient_b=1.0,
        )

        result_main_only = strategy.calculate(params_main_only)
        result_both = strategy.calculate(params_both)

        P_main_only = result_main_only["main_results"][0]["P_steam_formula_atm"]
        P_both = result_both["main_results"][0]["P_steam_formula_atm"]

        assert P_main_only > P_both, (
            f"P(только ОП)={P_main_only:.6f} должно быть > P(ОП+ВП)={P_both:.6f}"
        )

        increase = (P_main_only - P_both) / P_both * 100
        print(f"\nУвеличение давления при отключении ВП: {increase:.1f}%")

    @pytest.mark.parametrize("W_main", [8000.0, 12000.0, 15000.0])
    def test_pressure_comparison_multiple_flows(self, strategy, results_1, W_main):
        mode_3_data = find_mode_in_results(_results, W_main=W_main, W_builtin=0.0, coefficient_b=1.0)
        P_mode_3 = get_expected_pressure(mode_3_data, t1_idx=3, G_steam_idx=4)

        W_builtin_map = {8000.0: 1500.0, 12000.0: 3500.0, 15000.0: 5000.0}
        W_builtin = W_builtin_map.get(W_main)

        if W_builtin:
            mode_1_data = find_mode_in_results(results_1, W_main=W_main, W_builtin=W_builtin, coefficient_b=1.0)
            if mode_1_data:
                P_mode_1 = get_expected_pressure(mode_1_data, t1_idx=3, G_steam_idx=4)

                assert P_mode_3 > P_mode_1, (
                    f"W_main={W_main}: P(mode_3)={P_mode_3:.6f} должно быть > P(mode_1)={P_mode_1:.6f}"
                )


class TestVerificationScenario1:
    """Контрольный пример: сценарий 1 (только ОП)."""

    def test_saturation_temperature(self, strategy):
        params = build_calculation_params(
            geometry=_geometry,
            mode=_mode,
            W_main=12000.0,
            W_builtin=0.0,
            t1_main=20.0,
            t1_builtin=20.0,
            G_steam=200.0,
            coefficient_b=1.0,
        )

        result = strategy.calculate(params)
        calculated_t_sat = result["main_results"][0]["t_sat"]

        assert calculated_t_sat == pytest.approx(30.898, abs=0.01), (
            f"Ожидаемое t_sat = 30.898°C, рассчитанное = {calculated_t_sat:.3f}°C"
        )

