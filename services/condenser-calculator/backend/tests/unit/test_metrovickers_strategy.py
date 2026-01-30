import pytest
from app.utils.metrovickers_strategy import MetroVickersStrategy


class TestMetroVickersStrategy:
    """
    Набор тестов для проверки корректности расчетов по методике Metro-Vickers.
    """

    def test_calculation_against_known_value(self):
        """
        Проверяет результат расчета по одному набору данных с известным эталонным значением.
        """
        strategy = MetroVickersStrategy()
        input_params = {
            'diameter_inside_of_pipes': 22.4,
            'thickness_pipe_wall': 0.8,
            'length_cooling_tubes_of_the_main_bundle': 13910,
            'number_cooling_tubes_of_the_main_bundle': 20904,
            'number_cooling_tubes_of_the_built_in_bundle': 0,
            'number_cooling_water_passes_of_the_main_bundle': 2,
            'mass_flow_cooling_water': 45000.0,
            'temperature_cooling_water_1': 45.0,
            'thermal_conductivity_cooling_surface_tube_material': 16.2,
            'coefficient_b': 1.0,
            'mass_flow_flow_path_1': 200.0,
            'degree_dryness_flow_path_1': 0.95,
        }
        
        expected_pressure = 0.11498207272441292

        results = strategy.calculate(input_params)
        
        actual_pressure = results['pressure_flow_path_1']

        assert actual_pressure == pytest.approx(
            expected_pressure, 
            abs=1e-5
        ), f"Расчетное давление {actual_pressure} не совпадает с эталонным {expected_pressure}"
