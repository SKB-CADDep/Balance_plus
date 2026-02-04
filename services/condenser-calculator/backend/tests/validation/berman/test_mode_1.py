"""
Валидационные тесты для режима 1: ОП + ВП с одинаковыми температурами.
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
_mode = load_mode(1)
_results = load_results(1)
_test_cases = generate_test_cases_from_results(_results, _mode)
_ejector_cases = generate_ejector_test_cases(_results)


class TestPressureMatrixMode1:
    """Полная проверка матрицы давлений из results_1.json."""

    @pytest.mark.parametrize("case", _test_cases, ids=[c["id"] for c in _test_cases])
    def test_pressure_calculation(self, strategy, case):
        params = build_calculation_params(
            geometry=_geometry,
            mode=_mode,
            W_main=case["W_main"],
            W_builtin=case["W_builtin"],
            t1_main=case["t1_main"],
            t1_builtin=case["t1_builtin"],
            G_steam=case["G_steam"],
            coefficient_b=case["coefficient_b"],
            G_air=0.0,
        )

        result = strategy.calculate(params)

        assert len(result["main_results"]) > 0, f"Результаты не получены для {case['id']}"

        calculated = result["main_results"][0]["P_steam_formula_atm"]

        assert_pressure_approx(
            calculated=calculated, expected=case["expected_pressure"], context=f"Тест: {case['id']}"
        )


class TestEjectorsMode1:
    """Проверка расчёта эжекторов для режима 1."""

    @pytest.mark.parametrize("case", _ejector_cases, ids=[c["id"] for c in _ejector_cases])
    def test_ejector_pressure(self, strategy, case):
        params = build_calculation_params(
            geometry=_geometry,
            mode=_mode,
            W_main=12000.0,
            W_builtin=4000.0,
            t1_main=case["t1"],
            t1_builtin=case["t1"],
            G_steam=200.0,
            coefficient_b=1.0,
            G_air=_geometry["limits"]["mass_flow_air"],
        )

        result = strategy.calculate(params)

        ejector_results = [
            ej for ej in result["ejector_results"] if ej["number_of_ejectors"] == case["num_ejectors"]
        ]

        assert len(ejector_results) > 0

        calculated = ejector_results[0]["P_ejector_atm"]

        assert calculated == pytest.approx(case["expected_pressure"], rel=0.01), (
            f"Эжектор {case['num_ejectors']} шт., t1={case['t1']}°C:\n"
            f"  Ожидаемое = {case['expected_pressure']:.6f}\n"
            f"  Рассчитанное = {calculated:.6f}"
        )


class TestSpotCheckMode1:
    """Выборочные проверки для ключевых режимов."""

    def test_reference_mode(self, strategy, geometry_standard, mode_1, results_1):
        mode_data = find_mode_in_results(results_1, W_main=12000.0, W_builtin=3500.0, coefficient_b=1.0)
        assert mode_data is not None

        expected = get_expected_pressure(mode_data, t1_idx=3, G_steam_idx=4)

        params = build_calculation_params(
            geometry=geometry_standard,
            mode=mode_1,
            W_main=12000.0,
            W_builtin=3500.0,
            t1_main=20.0,
            t1_builtin=20.0,
            G_steam=200.0,
            coefficient_b=1.0,
        )

        result = strategy.calculate(params)
        calculated = result["main_results"][0]["P_steam_formula_atm"]

        assert_pressure_approx(calculated, expected, context="Опорный режим mode_1")

    def test_dirty_tubes_increase_pressure(self, strategy, geometry_standard, mode_1, results_1):
        mode_clean = find_mode_in_results(results_1, W_main=12000.0, W_builtin=3500.0, coefficient_b=1.0)
        mode_dirty = find_mode_in_results(results_1, W_main=12000.0, W_builtin=3500.0, coefficient_b=0.75)

        P_clean = get_expected_pressure(mode_clean, t1_idx=3, G_steam_idx=4)
        P_dirty = get_expected_pressure(mode_dirty, t1_idx=3, G_steam_idx=4)

        assert P_dirty > P_clean, f"P(dirty)={P_dirty:.6f} должно быть > P(clean)={P_clean:.6f}"


class TestPhysicalConsistencyMode1:
    """Проверка физической корректности результатов."""

    def test_pressure_monotonicity_by_temperature(self, results_1):
        mode_data = find_mode_in_results(results_1, W_main=12000.0, W_builtin=3500.0, coefficient_b=1.0)
        pressures = mode_data["table_data"][0]["pressures_axis"]

        for t_idx in range(5):
            P_curr = pressures[t_idx][4]
            P_next = pressures[t_idx + 1][4]
            assert P_next > P_curr, (
                f"Давление должно расти с температурой: "
                f"P[t{t_idx}]={P_curr:.6f}, P[t{t_idx+1}]={P_next:.6f}"
            )

    def test_pressure_monotonicity_by_steam_flow(self, results_1):
        mode_data = find_mode_in_results(results_1, W_main=12000.0, W_builtin=3500.0, coefficient_b=1.0)
        pressures = mode_data["table_data"][0]["pressures_axis"]

        for g_idx in range(8):
            P_curr = pressures[3][g_idx]
            P_next = pressures[3][g_idx + 1]
            assert P_next > P_curr, "Давление должно расти с расходом пара"

