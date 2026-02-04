"""
Валидационные тесты для режима 4: расширенный диапазон, сокращённая матрица.
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


_geometry = load_geometry("geometry_4")  # Специальная геометрия для mode_4
_mode = load_mode(4)
_results = load_results(4)
_test_cases = generate_test_cases_from_results(_results, _mode)
_ejector_cases = generate_ejector_test_cases(_results)


class TestPressureMatrixMode4:
    """Полная проверка матрицы давлений из results_4.json."""

    @pytest.mark.parametrize("case", _test_cases, ids=[c["id"] for c in _test_cases])
    def test_pressure_calculation(self, strategy, case):
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


class TestEjectorsMode4:
    """Тесты эжекторов с увеличенным расходом воздуха."""

    @pytest.mark.parametrize("case", _ejector_cases, ids=[c["id"] for c in _ejector_cases])
    def test_ejector_pressure(self, strategy, case):
        params = build_calculation_params(
            geometry=_geometry,
            mode=_mode,
            W_main=12000.0,
            W_builtin=0.0,
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
            f"Эжектор {case['num_ejectors']} шт., t1={case['t1']}°C, G_air=20:\n"
            f"  Ожидаемое = {case['expected_pressure']:.6f}\n"
            f"  Рассчитанное = {calculated:.6f}"
        )

    def test_higher_air_flow_increases_ejector_pressure(self, strategy):
        base_params = {
            "W_main": 12000.0,
            "W_builtin": 0.0,
            "t1_main": 20.0,
            "t1_builtin": 20.0,
            "G_steam": 200.0,
            "coefficient_b": 1.0,
        }

        geometry_std = load_geometry("geometry")
        params_low = build_calculation_params(geometry=geometry_std, mode=_mode, **base_params, G_air=16.5)
        params_high = build_calculation_params(geometry=_geometry, mode=_mode, **base_params, G_air=20.0)

        result_low = strategy.calculate(params_low)
        result_high = strategy.calculate(params_high)

        P_low = next(ej["P_ejector_atm"] for ej in result_low["ejector_results"] if ej["number_of_ejectors"] == 1)
        P_high = next(ej["P_ejector_atm"] for ej in result_high["ejector_results"] if ej["number_of_ejectors"] == 1)

        assert P_high > P_low, f"P(G_air=20)={P_high:.6f} должно быть > P(G_air=16.5)={P_low:.6f}"


class TestExtendedWaterFlowRange:
    """Проверка расширенного диапазона расхода воды (8000-16000 м³/ч)."""

    def test_w16000_lower_pressure_than_w8000(self):
        mode_8000 = find_mode_in_results(_results, W_main=8000.0, W_builtin=0.0, coefficient_b=1.0)
        mode_16000 = find_mode_in_results(_results, W_main=16000.0, W_builtin=0.0, coefficient_b=1.0)

        for t_idx in range(6):
            for g_idx in range(2):
                P_8000 = get_expected_pressure(mode_8000, t_idx, g_idx)
                P_16000 = get_expected_pressure(mode_16000, t_idx, g_idx)

                assert P_16000 < P_8000, (
                    f"t_idx={t_idx}, g_idx={g_idx}: P(16000)={P_16000:.6f} должно быть < P(8000)={P_8000:.6f}"
                )

    def test_pressure_reduction_quantification(self):
        mode_8000 = find_mode_in_results(_results, W_main=8000.0, W_builtin=0.0, coefficient_b=1.0)
        mode_16000 = find_mode_in_results(_results, W_main=16000.0, W_builtin=0.0, coefficient_b=1.0)

        P_8000 = get_expected_pressure(mode_8000, t1_idx=3, G_steam_idx=0)
        P_16000 = get_expected_pressure(mode_16000, t1_idx=3, G_steam_idx=0)

        reduction = (P_8000 - P_16000) / P_8000 * 100

        print("\nСнижение давления при увеличении W с 8000 до 16000 м³/ч:")
        print(f"  P(8000) = {P_8000:.6f} кгс/см²")
        print(f"  P(16000) = {P_16000:.6f} кгс/см²")
        print(f"  Снижение: {reduction:.1f}%")

        assert 15 < reduction < 30


class TestMode4VsMode3:
    """Сравнение mode_4 с mode_3 для общих режимов."""

    @pytest.fixture
    def results_3(self):
        return load_results(3)

    def test_w8000_matches_mode3(self, results_3):
        mode_3 = find_mode_in_results(results_3, W_main=8000.0, W_builtin=0.0, coefficient_b=1.0)
        mode_4 = find_mode_in_results(_results, W_main=8000.0, W_builtin=0.0, coefficient_b=1.0)

        for t_idx in range(6):
            P_mode3_100 = mode_3["table_data"][0]["pressures_axis"][t_idx][2]
            P_mode4_100 = mode_4["table_data"][0]["pressures_axis"][t_idx][0]

            assert P_mode3_100 == pytest.approx(P_mode4_100, rel=0.0001), (
                f"t_idx={t_idx}, G=100: mode_3={P_mode3_100:.6f}, mode_4={P_mode4_100:.6f}"
            )

            P_mode3_300 = mode_3["table_data"][0]["pressures_axis"][t_idx][6]
            P_mode4_300 = mode_4["table_data"][0]["pressures_axis"][t_idx][1]

            assert P_mode3_300 == pytest.approx(P_mode4_300, rel=0.0001), (
                f"t_idx={t_idx}, G=300: mode_3={P_mode3_300:.6f}, mode_4={P_mode4_300:.6f}"
            )

