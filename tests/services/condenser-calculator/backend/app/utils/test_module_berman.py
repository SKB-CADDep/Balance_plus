import pytest
from app.utils.berman_strategy import BermanStrategy


class TestBermanEjectorPressure:
    """
    Тестирует корректность расчета давления всасывания эжекторов
    в классе BermanStrategy.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Настраивает общие параметры для тестов перед каждым запуском.
        """
        self.strategy = BermanStrategy()
        
        # Словарь с параметрами, необходимыми для расчета эжекторов
        self.simulation_params = {
            # Геометрия и номинальные режимы (нужны для полной инициализации класса)
            'length_cooling_tubes_of_the_main_bundle': 7.080,
            'number_cooling_water_passes_of_the_main_bundle': 2,
            'number_cooling_tubes_of_the_main_bundle': 1754,
            'mass_flow_steam_nom': 16.0,
            'thermal_conductivity_cooling_surface_tube_material': 37.0,
            'diameter_inside_of_pipes': 22.0,
            'thickness_pipe_wall': 1.0,
            'enthalpy_flow_path_1': 520.0, # Энтальпия (влияет на основной расчет, но не на эжектор)
            'BAP': 1,
            
            # Итеративные параметры (значения-заглушки для основного расчета)
            'mass_flow_cooling_water_list': [1200],
            'mass_flow_steam_list': [16],
            'coefficient_R_list': [0.10e-6],
            
            # Ключевые параметры для теста эжекторов
            'temperature_cooling_water_1_list': [4, 5, 10, 15, 20, 25, 30, 35],
            'mass_flow_air': 16.5,
        }

    def test_ejector_pressure_calculation(self):
        """
        Проверяет, что рассчитанные значения давления всасывания эжекторов
        совпадают с эталонными для различных температур на входе.
        """
        # Запускаем полный расчет, чтобы получить результаты по эжекторам
        calculation_results = self.strategy.calculate(self.simulation_params)
        all_ejector_results = calculation_results['ejector_results']

        assert all_ejector_results is not None, "Секция 'ejector_results' отсутствует в результатах."
        
        # Отфильтровываем результаты только для одного работающего эжектора
        results_for_one_ejector = [
            item for item in all_ejector_results if item['number_of_ejectors'] == 1
        ]
        
        # Проверяем, что количество результатов соответствует количеству входных температур
        assert len(results_for_one_ejector) == len(self.simulation_params['temperature_cooling_water_1_list']), \
            "Количество результатов для одного эжектора не совпадает с количеством заданных температур."

        # Преобразуем список результатов в удобный для проверки словарь {температура: давление}
        calculated_pressures_map = {
            item['inlet_water_temperature_C']: item['ejector_pressure_kPa']
            for item in results_for_one_ejector
        }

        # Эталонные значения, с которыми будем сравнивать
        expected_pressures_map = {
            35: 7.341,
            30: 5.889,
            25: 4.755,
            20: 3.879,
            15: 3.209,
            10: 2.703,
            5: 2.325,
            4: 2.263,
        }

        # Сравниваем фактические значения с эталонными для каждой температуры
        for temp, expected_pressure in expected_pressures_map.items():
            assert temp in calculated_pressures_map, f"Результат для температуры {temp}°C не найден."
            actual_pressure = calculated_pressures_map[temp]
            assert actual_pressure == pytest.approx(
                expected_pressure,
                abs=0.01  # Точность до 2-го знака после запятой
            ), f"Давление для t={temp}°C не совпадает с эталоном"

        print("\nТест эжектора: все значения давлений успешно прошли проверку.")
