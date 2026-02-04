# tests/unit/test_module_berman.py
"""
Юнит-тесты для BermanStrategy.
"""

import pytest

from app.utils.berman_strategy import BermanStrategy


class TestBermanStrategy:
    """Базовые тесты BermanStrategy."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Инициализация стратегии и базовых параметров."""
        self.strategy = BermanStrategy()

        # Базовые параметры для тестов
        self.base_params = {
            # Геометрия
            'L_main': 7500.0,           # мм - длина основного пучка
            'L_builtin': 7500.0,        # мм - длина встроенного пучка
            'N_main': 12000,            # шт - количество трубок ОП
            'N_builtin': 4000,          # шт - количество трубок ВП
            'd_in': 20.0,               # мм - внутренний диаметр
            'S_tube': 1.0,              # мм - толщина стенки
            'Z_main': 2,                # число ходов ОП
            'Z_builtin': 2,             # число ходов ВП

            # Параметры
            'G_nom': 350.0,             # т/ч - номинальный расход пара
            'H_steam': 515.0,           # ккал/кг - энтальпия
            'lambda': 90.0,             # Вт/(м·К) - теплопроводность

            # Рабочие параметры (списки)
            'W_main_list': [12000.0],
            'W_builtin_list': [4000.0],
            't1_main_list': [20.0],
            't1_builtin_list': [20.0],
            'G_steam_list': [200.0],
            'coefficient_b_list': [1.0],
            'G_air': 0.0,
        }

    def test_strategy_instantiation(self):
        """Проверка создания экземпляра."""
        assert self.strategy is not None
        assert hasattr(self.strategy, 'calculate')

    def test_calculate_returns_dict(self):
        """Проверка что calculate возвращает словарь."""
        result = self.strategy.calculate(self.base_params)

        assert isinstance(result, dict)
        assert 'main_results' in result
        assert 'ejector_results' in result

    def test_calculate_returns_results(self):
        """Проверка что результаты не пустые."""
        result = self.strategy.calculate(self.base_params)

        assert len(result['main_results']) > 0

    def test_result_contains_required_fields(self):
        """Проверка наличия обязательных полей в результате."""
        result = self.strategy.calculate(self.base_params)

        main_result = result['main_results'][0]

        required_fields = [
            't_sat',
            'P_steam_formula_atm',
            'P_steam_formula_Pa',
            'K_dirty_main',
            'delta_t_heat_main',
        ]

        for field in required_fields:
            assert field in main_result, f"Поле '{field}' отсутствует в результате"

    def test_saturation_temperature_positive(self):
        """Проверка что температура насыщения положительная."""
        result = self.strategy.calculate(self.base_params)

        t_sat = result['main_results'][0]['t_sat']

        assert t_sat > 0, f"t_sat должна быть > 0, получено {t_sat}"

    def test_pressure_positive(self):
        """Проверка что давление положительное."""
        result = self.strategy.calculate(self.base_params)

        pressure = result['main_results'][0]['P_steam_formula_atm']

        assert pressure > 0, f"Давление должно быть > 0, получено {pressure}"


class TestBermanEjectorPressure:
    """Тесты расчёта эжекторов."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Инициализация."""
        self.strategy = BermanStrategy()

        self.params_with_ejector = {
            'L_main': 7500.0,
            'L_builtin': 7500.0,
            'N_main': 12000,
            'N_builtin': 4000,
            'd_in': 20.0,
            'S_tube': 1.0,
            'Z_main': 2,
            'Z_builtin': 2,
            'G_nom': 350.0,
            'H_steam': 515.0,
            'lambda': 90.0,
            'W_main_list': [12000.0],
            'W_builtin_list': [4000.0],
            't1_main_list': [20.0],
            't1_builtin_list': [20.0],
            'G_steam_list': [200.0],
            'coefficient_b_list': [1.0],
            'G_air': 16.5,  # Включаем расчёт эжекторов
        }

    def test_ejector_pressure_calculation(self):
        """Проверка расчёта давления эжекторов."""
        result = self.strategy.calculate(self.params_with_ejector)

        assert 'ejector_results' in result
        assert len(result['ejector_results']) > 0

    def test_ejector_results_structure(self):
        """Проверка структуры результатов эжекторов."""
        result = self.strategy.calculate(self.params_with_ejector)

        ejector_result = result['ejector_results'][0]

        assert 'number_of_ejectors' in ejector_result
        assert 'P_ejector_kPa' in ejector_result
        assert 'P_ejector_atm' in ejector_result

    def test_ejector_pressure_positive(self):
        """Проверка что давление эжектора положительное."""
        result = self.strategy.calculate(self.params_with_ejector)

        for ejector_result in result['ejector_results']:
            assert ejector_result['P_ejector_atm'] > 0

    def test_no_ejector_when_g_air_zero(self):
        """Проверка что эжекторы не рассчитываются при G_air=0."""
        params = self.params_with_ejector.copy()
        params['G_air'] = 0

        result = self.strategy.calculate(params)

        assert len(result['ejector_results']) == 0


class TestBermanEdgeCases:
    """Тесты граничных условий."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Инициализация."""
        self.strategy = BermanStrategy()

        self.base_params = {
            'L_main': 7500.0,
            'L_builtin': 7500.0,
            'N_main': 12000,
            'N_builtin': 4000,
            'd_in': 20.0,
            'S_tube': 1.0,
            'Z_main': 2,
            'Z_builtin': 2,
            'G_nom': 350.0,
            'H_steam': 515.0,
            'lambda': 90.0,
            'W_main_list': [12000.0],
            'W_builtin_list': [4000.0],
            't1_main_list': [20.0],
            't1_builtin_list': [20.0],
            'G_steam_list': [200.0],
            'coefficient_b_list': [1.0],
            'G_air': 0.0,
        }

    def test_main_bundle_only(self):
        """Тест режима только ОП (W_builtin=0)."""
        params = self.base_params.copy()
        params['W_builtin_list'] = [0.0]

        result = self.strategy.calculate(params)

        assert len(result['main_results']) > 0
        assert result['main_results'][0]['t_sat'] > 0

    def test_low_steam_flow(self):
        """Тест при низком расходе пара."""
        params = self.base_params.copy()
        params['G_steam_list'] = [5.0]

        result = self.strategy.calculate(params)

        assert len(result['main_results']) > 0

    def test_high_steam_flow(self):
        """Тест при высоком расходе пара."""
        params = self.base_params.copy()
        params['G_steam_list'] = [400.0]

        result = self.strategy.calculate(params)

        assert len(result['main_results']) > 0

    def test_dirty_tubes(self):
        """Тест при загрязнённых трубках."""
        params = self.base_params.copy()
        params['coefficient_b_list'] = [0.75]

        result = self.strategy.calculate(params)

        assert len(result['main_results']) > 0

    def test_multiple_temperatures(self):
        """Тест с несколькими температурами."""
        params = self.base_params.copy()
        params['t1_main_list'] = [10.0, 20.0, 30.0]
        params['t1_builtin_list'] = [10.0, 20.0, 30.0]

        result = self.strategy.calculate(params)

        # Должно быть 3 результата (по одному на каждую температуру)
        # Или больше, если есть комбинации с G_steam
        assert len(result['main_results']) >= 3
