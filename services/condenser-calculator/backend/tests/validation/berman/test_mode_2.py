"""
Валидационные тесты для режима 2: ОП + ВП с разными температурами.
Особенность: t1_builtin = t1_main + 3°C.
"""

import pytest

from .conftest import (
    assert_pressure_approx,
    build_calculation_params,
    find_mode_in_results,
    generate_test_cases_from_results,
    get_expected_pressure,
    load_geometry,
    load_mode,
    load_results,
)


_geometry = load_geometry("geometry")
_mode = load_mode(2)
_results = load_results(2)
_test_cases = generate_test_cases_from_results(_results, _mode)


class TestPressureMatrixMode2:
    """Полная проверка матрицы давлений из results_2.json."""

    @pytest.mark.parametrize("case", _test_cases, ids=[c["id"] for c in _test_cases])
    def test_pressure_calculation(self, strategy, case):
        params = build_calculation_params(
            geometry=_geometry,
            mode=_mode,
            W_main=case["W_main"],
            W_builtin=case["W_builtin"],
            t1_main=case["t1_main"],
            t1_builtin=case["t1_builtin"],  # Отличается от t1_main!
            G_steam=case["G_steam"],
            coefficient_b=case["coefficient_b"],
            G_air=0.0,
        )

        result = strategy.calculate(params)

        assert len(result["main_results"]) > 0

        calculated = result["main_results"][0]["P_steam_formula_atm"]

        assert_pressure_approx(calculated=calculated, expected=case["expected_pressure"], context=f"Тест: {case['id']}")


class TestDifferentTemperaturesEffect:
    """Проверка влияния разных температур на ОП и ВП."""

    @pytest.fixture
    def results_1_for_comparison(self):
        return load_results(1)

    def test_higher_builtin_temp_increases_pressure(self, strategy, results_1_for_comparison):
        params_diff = build_calculation_params(
            geometry=_geometry,
            mode=_mode,
            W_main=12000.0,
            W_builtin=3500.0,
            t1_main=20.0,
            t1_builtin=23.0,  # +3°C
            G_steam=200.0,
            coefficient_b=1.0,
        )

        mode_1 = load_mode(1)
        params_same = build_calculation_params(
            geometry=_geometry,
            mode=mode_1,
            W_main=12000.0,
            W_builtin=3500.0,
            t1_main=20.0,
            t1_builtin=20.0,
            G_steam=200.0,
            coefficient_b=1.0,
        )

        result_diff = strategy.calculate(params_diff)
        result_same = strategy.calculate(params_same)

        P_diff = result_diff["main_results"][0]["P_steam_formula_atm"]
        P_same = result_same["main_results"][0]["P_steam_formula_atm"]

        assert P_diff > P_same, (
            f"P(t1_builtin=23°C)={P_diff:.6f} должно быть > "
            f"P(t1_builtin=20°C)={P_same:.6f}"
        )

    @pytest.mark.parametrize(
        "t1_main, t1_builtin",
        [(5.0, 8.0), (10.0, 13.0), (15.0, 18.0), (20.0, 23.0), (25.0, 28.0), (30.0, 33.0)],
        ids=["5/8", "10/13", "15/18", "20/23", "25/28", "30/33"],
    )
    def test_all_temperature_pairs(self, strategy, t1_main, t1_builtin):
        mode_data = find_mode_in_results(_results, W_main=12000.0, W_builtin=3500.0, coefficient_b=1.0)

        t1_list = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
        t_idx = t1_list.index(t1_main)

        expected = get_expected_pressure(mode_data, t1_idx=t_idx, G_steam_idx=4)

        params = build_calculation_params(
            geometry=_geometry,
            mode=_mode,
            W_main=12000.0,
            W_builtin=3500.0,
            t1_main=t1_main,
            t1_builtin=t1_builtin,
            G_steam=200.0,
            coefficient_b=1.0,
        )

        result = strategy.calculate(params)
        calculated = result["main_results"][0]["P_steam_formula_atm"]

        assert_pressure_approx(calculated, expected, context=f"t1_main={t1_main}°C, t1_builtin={t1_builtin}°C")

