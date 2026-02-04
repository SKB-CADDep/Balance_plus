import pytest

from app.utils.VKU_strategy import VKUStrategy


class TestVKUStrategy:
    """
    Набор тестов для класса VKUStrategy.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Настройка тестового окружения."""
        self.mass_flow_nom = 1250.0
        self.dryness_nom = 0.92
        self.strategy = VKUStrategy(
            mass_flow_steam_nom=self.mass_flow_nom,
            degree_dryness_steam_nom=self.dryness_nom
        )
        self.p_at_100_30 = 0.097280927
        self.p_at_100_20 = 0.060673115

    def test_calculation_on_grid_point(self):
        """Тест: Расчет для точки, точно совпадающей с узлом в таблице."""
        params = {
            'mass_flow_flow_path_1': 1250.0,
            'degree_dryness_flow_path_1': 0.92,
            'temperature_air': 30.0
        }

        result = self.strategy.calculate(params)

        assert isinstance(result, dict)
        assert result['mass_flow_reduced_steam_condencer'] == pytest.approx(100.0, abs=1e-5)
        assert result['pressure_flow_path_1'] == pytest.approx(self.p_at_100_30, abs=1e-7)

    def test_default_temperature(self):
        """Тест: Расчет с использованием температуры по умолчанию (20°С)."""
        params = {
            'mass_flow_flow_path_1': 1250.0,
            'degree_dryness_flow_path_1': 0.92
        }

        result = self.strategy.calculate(params)

        assert result['mass_flow_reduced_steam_condencer'] == pytest.approx(100.0, abs=1e-5)
        assert result['pressure_flow_path_1'] == pytest.approx(self.p_at_100_20, abs=1e-7)

    def test_interpolation_between_points(self):
        """Тест: Расчет для точки, требующей интерполяции."""
        params = {
            'mass_flow_flow_path_1': 1187.5,
            'degree_dryness_flow_path_1': 1092.5 / 1187.5,  # ~0.92
            'temperature_air': 27.5
        }

        result = self.strategy.calculate(params)

        expected_pressure_approx = 0.08341
        assert result['mass_flow_reduced_steam_condencer'] == pytest.approx(95.0, abs=1e-5)
        assert result['pressure_flow_path_1'] == pytest.approx(expected_pressure_approx, abs=1e-3)

    def test_missing_required_param(self):
        """Тест: Проверка вызова исключения при отсутствии обязательного параметра."""
        params = {
            'degree_dryness_flow_path_1': 0.92,
            'temperature_air': 20.0
        }

        with pytest.raises(KeyError):
            self.strategy.calculate(params)
