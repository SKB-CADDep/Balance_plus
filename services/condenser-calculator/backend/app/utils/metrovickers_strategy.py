import math
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from typing import Dict, Any
import seuif97
from uniconv import UnitConverter

from utils.Constants import coefficient_B_const, k_interpolation_data, \
    temperature_cooling_water_average_heating_const, speed_cooling_water_const

class MetroVickersStrategy:
    def __init__(self):
        self._get_k_from_table_temp = RegularGridInterpolator(
            (k_interpolation_data["speed_points"], k_interpolation_data["temperature_points"]),
            np.array(k_interpolation_data["k_values_matrix"]),
            bounds_error=False, 
            method="nearest"
        )
        self._get_heat_of_vaporization = lambda temp: (30 - temp) * 0.582 + 580.4
        self.uc = UnitConverter()

    def calculate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        diameter_inside_of_pipes = params['diameter_inside_of_pipes']
        thickness_pipe_wall = params['thickness_pipe_wall']
        length_cooling_tubes_of_the_main_bundle = params['length_cooling_tubes_of_the_main_bundle']
        number_cooling_tubes_of_the_main_bundle = params['number_cooling_tubes_of_the_main_bundle']
        number_cooling_tubes_of_the_built_in_bundle = params['number_cooling_tubes_of_the_built_in_bundle']
        number_cooling_water_passes_of_the_main_bundle = params['number_cooling_water_passes_of_the_main_bundle']
        mass_flow_cooling_water = params['mass_flow_cooling_water']
        temperature_cooling_water_1 = params['temperature_cooling_water_1']
        thermal_conductivity_cooling_surface_tube_material = params['thermal_conductivity_cooling_surface_tube_material']
        coefficient_b = params.get('coefficient_b', 1.0)
        mass_flow_flow_path_1 = params['mass_flow_flow_path_1']
        degree_dryness_flow_path_1 = params['degree_dryness_flow_path_1']
        
        number_air_cooler_total_pipes = params.get('number_air_cooler_total_pipes')
        if number_air_cooler_total_pipes is None:
            total_tubes = number_cooling_tubes_of_the_main_bundle + number_cooling_tubes_of_the_built_in_bundle
            number_air_cooler_total_pipes = total_tubes * 0.15

        results = {}

        diameter_outside_of_pipes = diameter_inside_of_pipes + 2 * thickness_pipe_wall # p.1
        area_tube_bundle_surface_total = (math.pi * length_cooling_tubes_of_the_main_bundle *
                                          (number_cooling_tubes_of_the_main_bundle + number_cooling_tubes_of_the_built_in_bundle) *
                                          diameter_outside_of_pipes * 1e-6) # p.2.1
        
        # ==================== ДИАГНОСТИЧЕСКИЙ БЛОК ====================
        #print(math.pi, length_cooling_tubes_of_the_main_bundle, number_cooling_tubes_of_the_main_bundle, diameter_outside_of_pipes)
        # ==============================================================

        area_surface_of_the_air_cooler_tube_bundle = (math.pi * length_cooling_tubes_of_the_main_bundle *
                                                      number_air_cooler_total_pipes *
                                                      diameter_outside_of_pipes * 1e-6) # p.2.2
        if area_tube_bundle_surface_total == 0: # Избегаем деления на ноль
            coefficient_Kf = 1.0
        else:
            coefficient_Kf = 1 - 0.225 * (area_surface_of_the_air_cooler_tube_bundle / area_tube_bundle_surface_total) # p.3
        
        coefficient_R1 = ((2 * thickness_pipe_wall / 1000 * diameter_outside_of_pipes / 1000) / 
                          ((diameter_outside_of_pipes / 1000 + diameter_inside_of_pipes / 1000) 
                           * thermal_conductivity_cooling_surface_tube_material)) # p.4

        max_iterations = 20
        tolerance = 0.001
        
        coefficient_K_temp = self._get_k_from_table_temp((speed_cooling_water_const, temperature_cooling_water_average_heating_const)).item() # p.5

        speed_cooling_water = ((mass_flow_cooling_water * number_cooling_water_passes_of_the_main_bundle) / 
                                   (900 * math.pi * (number_cooling_tubes_of_the_main_bundle + 
                                                     number_cooling_tubes_of_the_built_in_bundle) * (diameter_inside_of_pipes / 1000)**2)) # p.8
            
        heat_of_vaporization = self._get_heat_of_vaporization(temperature_cooling_water_1) # p.9

        delta_t_water = (mass_flow_flow_path_1 * heat_of_vaporization * degree_dryness_flow_path_1) / mass_flow_cooling_water 
        temperature_cooling_water_2 = temperature_cooling_water_1 + delta_t_water # p.10
        temperature_cooling_water_average_heating = (temperature_cooling_water_1 + temperature_cooling_water_2) / 2 # p.11

         # ==================== ДИАГНОСТИЧЕСКИЙ БЛОК ====================
        # print("\n--- ДИАГНОСТИКА ПЕРЕД ЦИКЛОМ ---")
        # print(f"Расчетная скорость: {speed_cooling_water:.4f} м/с")
        # print(f"Расчетная сред. температура: {temperature_cooling_water_average_heating:.4f} °C")
        # print("---")
        # print(f"Границы таблицы по скорости: от {k_interpolation_data['speed_points'][0]} до {k_interpolation_data['speed_points'][-1]}")
        # print(f"Границы таблицы по температуре: от {k_interpolation_data['temperature_points'][0]} до {k_interpolation_data['temperature_points'][-1]}")
        # print("-------------------------------------\n")
        # ===============================================================
        
        for i in range(max_iterations):   

            # ==================== ДИАГНОСТИЧЕСКИЙ БЛОК ====================
            # print(f"\n--- Итерация #{i} ---")
            # print(f"speed_cooling_water: значение = {speed_cooling_water}, тип = {type(speed_cooling_water)}")
            # print(f"temperature_cooling_water_average_heating: значение = {temperature_cooling_water_average_heating}, тип = {type(temperature_cooling_water_average_heating)}")
            # ==============================================================

            _get_k_from_table = RegularGridInterpolator(
                (k_interpolation_data["speed_points"], k_interpolation_data["temperature_points"]),
                np.array(k_interpolation_data["k_values_matrix"]),
                bounds_error=False,
                method="nearest"
            )

            try:
                query_point = np.array([[speed_cooling_water, temperature_cooling_water_average_heating]])
                k_temp_new = _get_k_from_table(query_point).item()
            except ValueError as e:
                error_message = (
                    f"Ошибка интерполяции: расчетные параметры вышли за пределы таблицы.\n"
                    f"  - Расчетная скорость воды: {speed_cooling_water:.2f} м/с (допустимый диапазон: {k_interpolation_data['speed_points'][0]} - {k_interpolation_data['speed_points'][-1]})\n"
                    f"  - Расчетная средняя температура: {temperature_cooling_water_average_heating:.2f} °C (допустимый диапазон: {k_interpolation_data['temperature_points'][0]} - {k_interpolation_data['temperature_points'][-1]})\n"
                    f"Проверьте входные данные, особенно `diameter_inside_of_pipes` (должен быть в мм)."
                )
                raise ValueError(error_message) from e
            
            '''
                Сравниваем K_new и K_old. Если разница велика, 
                то K_old становится равным K_new, повторяем, 
                пока abs(K_new - K_old) не станет меньше tolerance
            '''
            if abs(k_temp_new - coefficient_K_temp) < tolerance:
                coefficient_K_temp = k_temp_new # Сохраняем последнее значение
                break
            
            coefficient_K_temp = k_temp_new
            
            if i == max_iterations - 1:
                print("Warning: Iteration limit reached without convergence.")
                
        k_clean_denominator = (1 / (coefficient_K_temp * 0.85 * coefficient_B_const * coefficient_Kf)) - 0.087 / 10000 + coefficient_R1 # p.12
        coefficient_K = 1 / k_clean_denominator 

        coefficient_R = (1 / coefficient_K) * ((1 / coefficient_b) - 1) # p.7
        
        k_zag_denominator = k_clean_denominator + coefficient_R # p.13
        coefficient_Kzag = 1 / k_zag_denominator
        
        temperature_relative_underheating = 1 / (math.e ** ((coefficient_Kzag * area_tube_bundle_surface_total) / (mass_flow_cooling_water * 1000)) - 1) # p.14
    
        temperature_saturation_steam = temperature_cooling_water_2 + temperature_relative_underheating * (temperature_cooling_water_2 - temperature_cooling_water_1) # p.15

        pressure_flow_path_1_mpa = seuif97.tx(temperature_saturation_steam, 1.0, 0)

        pressure_flow_path_1_kgf_cm2 = self.uc.convert(
            pressure_flow_path_1_mpa,
            from_unit="МПа",
            to_unit="кгс/см²",
            parameter_type="pressure"
        )

        results.update({
            'diameter_outside_of_pipes': diameter_outside_of_pipes,
            'area_tube_bundle_surface_total': area_tube_bundle_surface_total,
            'area_surface_of_the_air_cooler_tube_bundle': area_surface_of_the_air_cooler_tube_bundle,
            'coefficient_Kf': coefficient_Kf,
            'coefficient_R1': coefficient_R1,
            'speed_cooling_water': speed_cooling_water,
            'heat_of_vaporization': heat_of_vaporization,
            'temperature_cooling_water_2': temperature_cooling_water_2,
            'temperature_cooling_water_average_heating': temperature_cooling_water_average_heating,
            'coefficient_K_temp': coefficient_K_temp,
            'coefficient_K': coefficient_K,
            'coefficient_R': coefficient_R,
            'coefficient_Kzag': coefficient_Kzag,
            'temperature_relative_underheating': temperature_relative_underheating,
            'temperature_saturation_steam': temperature_saturation_steam,
            'pressure_flow_path_1': pressure_flow_path_1_kgf_cm2
        })
        return results