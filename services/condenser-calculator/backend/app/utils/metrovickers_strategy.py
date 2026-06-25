"""
Стратегия расчета конденсаторов по методике Метро-Виккерса.

Модуль реализует тепловой и гидравлический расчет конденсатора с использованием 
эмпирических матриц (интерполяции коэффициента теплопередачи). Метод учитывает 
геометрию трубных пучков, свойства материалов стенки, чистоту труб и влияние 
воздухоохладителя на общую эффективность.
"""

import math
from typing import Any

import numpy as np
import seuif97
from scipy.interpolate import RegularGridInterpolator

from .Constants import (
    coefficient_B_const,
    k_interpolation_data,
    speed_cooling_water_const,
    temperature_cooling_water_average_heating_const,
)
from .uniconv import UnitConverter


class MetroVickersStrategy:
    """
    Класс-стратегия для выполнения расчетов по методу Метро-Виккерса.
    
    Инкапсулирует логику подготовки интерполяторов и пошагового 
    итерационного алгоритма вычисления конечного давления насыщения пара.
    """
    
    def __init__(self):
        """
        Инициализирует базовые вычислительные инструменты стратегии.
        
        Создает объект двумерной интерполяции теплопередачи (k) на основе 
        глобальных констант (матрицы Метро-Виккерса). Если расчетная точка 
        выходит за пределы таблицы, метод 'nearest' использует ближайшее граничное значение.
        """
        self._get_k_from_table_temp = RegularGridInterpolator(
            (k_interpolation_data["speed_points"],
             k_interpolation_data["temperature_points"]),
            np.array(k_interpolation_data["k_values_matrix"]),
            bounds_error=False,
            method="nearest"
        )
        # Эмпирическая формула для скрытой теплоты парообразования
        self._get_heat_of_vaporization = lambda temp: (
            30 - temp) * 0.582 + 580.4
        self.uc = UnitConverter()

    def calculate(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Выполняет полный цикл теплового расчета для заданного набора параметров.

        Алгоритм включает:
        1. Расчет геометрических площадей (с учетом пучка воздухоохладителя).
        2. Вычисление термических сопротивлений (стенки и загрязнений).
        3. Итерационный подбор коэффициента теплопередачи K_temp.
        4. Расчет нагрева воды и итогового давления насыщения.

        Args:
            params (dict[str, Any]): Словарь исходных параметров (геометрия, режимы, материалы).

        Returns:
            dict[str, Any]: Подробный словарь результатов, включающий:
                - Промежуточные коэффициенты (K, Kf, R, R1)
                - Расчетные температуры и площади
                - Итоговое давление пара ('pressure_flow_path_1' в кгс/см²)
                - Флаг 'is_extrapolated' (True, если данные вышли за пределы достоверной таблицы).
        """
        diameter_inside_of_pipes = params['diameter_inside_of_pipes']
        thickness_pipe_wall = params['thickness_pipe_wall']
        length_cooling_tubes_of_the_main_bundle = params['length_cooling_tubes_of_the_main_bundle']
        number_cooling_tubes_of_the_main_bundle = params['number_cooling_tubes_of_the_main_bundle']
        number_cooling_tubes_of_the_built_in_bundle = params[
            'number_cooling_tubes_of_the_built_in_bundle']
        number_cooling_water_passes_of_the_main_bundle = params[
            'number_cooling_water_passes_of_the_main_bundle']
        mass_flow_cooling_water = params['mass_flow_cooling_water']
        temperature_cooling_water_1 = params['temperature_cooling_water_1']
        thermal_conductivity_cooling_surface_tube_material = params[
            'thermal_conductivity_cooling_surface_tube_material']
        coefficient_b = params.get('coefficient_b', 1.0)
        mass_flow_flow_path_1 = params['mass_flow_flow_path_1']
        degree_dryness_flow_path_1 = params['degree_dryness_flow_path_1']

        number_air_cooler_total_pipes = params.get(
            'number_air_cooler_total_pipes')
        if number_air_cooler_total_pipes is None:
            total_tubes = number_cooling_tubes_of_the_main_bundle + \
                number_cooling_tubes_of_the_built_in_bundle
            number_air_cooler_total_pipes = total_tubes * 0.15

        results = {}

        diameter_outside_of_pipes = diameter_inside_of_pipes + 2 * thickness_pipe_wall  # p.1
        area_tube_bundle_surface_total = (math.pi * length_cooling_tubes_of_the_main_bundle *
                                          (number_cooling_tubes_of_the_main_bundle + number_cooling_tubes_of_the_built_in_bundle) *
                                          diameter_outside_of_pipes * 1e-6)  # p.2.1

        # ==================== ДИАГНОСТИЧЕСКИЙ БЛОК ====================
        # print(math.pi, length_cooling_tubes_of_the_main_bundle, number_cooling_tubes_of_the_main_bundle, diameter_outside_of_pipes)
        # ==============================================================

        area_surface_of_the_air_cooler_tube_bundle = (math.pi * length_cooling_tubes_of_the_main_bundle *
                                                      number_air_cooler_total_pipes *
                                                      diameter_outside_of_pipes * 1e-6)  # p.2.2
        if area_tube_bundle_surface_total == 0:  # Избегаем деления на ноль
            coefficient_Kf = 1.0
        else:
            coefficient_Kf = 1 - 0.225 * \
                (area_surface_of_the_air_cooler_tube_bundle /
                 area_tube_bundle_surface_total)  # p.3

        coefficient_R1 = ((2 * thickness_pipe_wall / 1000 * diameter_outside_of_pipes / 1000) /
                          ((diameter_outside_of_pipes / 1000 + diameter_inside_of_pipes / 1000)
                           * thermal_conductivity_cooling_surface_tube_material))  # p.4

        max_iterations = 20
        tolerance = 0.001

        coefficient_K_temp = self._get_k_from_table_temp(
            # p.5
            (speed_cooling_water_const, temperature_cooling_water_average_heating_const)).item()

        speed_cooling_water = ((mass_flow_cooling_water * number_cooling_water_passes_of_the_main_bundle) /
                               (900 * math.pi * (number_cooling_tubes_of_the_main_bundle +
                                                 # p.8
                                                 number_cooling_tubes_of_the_built_in_bundle) * (diameter_inside_of_pipes / 1000)**2))

        heat_of_vaporization = self._get_heat_of_vaporization(
            temperature_cooling_water_1)  # p.9

        delta_t_water = (mass_flow_flow_path_1 * heat_of_vaporization *
                         degree_dryness_flow_path_1) / mass_flow_cooling_water
        temperature_cooling_water_2 = temperature_cooling_water_1 + delta_t_water  # p.10
        temperature_cooling_water_average_heating = (
            temperature_cooling_water_1 + temperature_cooling_water_2) / 2  # p.11

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
                (k_interpolation_data["speed_points"],
                 k_interpolation_data["temperature_points"]),
                np.array(k_interpolation_data["k_values_matrix"]),
                bounds_error=False,
                method="nearest"
            )

            query_point = np.array(
                [[speed_cooling_water, temperature_cooling_water_average_heating]])
            k_temp_new = _get_k_from_table(query_point).item()

            '''
                Сравниваем K_new и K_old. Если разница велика,
                то K_old становится равным K_new, повторяем,
                пока abs(K_new - K_old) не станет меньше tolerance
            '''
            if abs(k_temp_new - coefficient_K_temp) < tolerance:
                coefficient_K_temp = k_temp_new  # Сохраняем последнее значение
                break

            coefficient_K_temp = k_temp_new

            if i == max_iterations - 1:
                print("Warning: Iteration limit reached without convergence.")

        k_clean_denominator = (1 / (coefficient_K_temp * 0.85 * coefficient_B_const *
                               coefficient_Kf)) - 0.087 / 10000 + coefficient_R1  # p.12
        coefficient_K = 1 / k_clean_denominator

        coefficient_R = (1 / coefficient_K) * ((1 / coefficient_b) - 1)  # p.7

        k_zag_denominator = k_clean_denominator + coefficient_R  # p.13
        coefficient_Kzag = 1 / k_zag_denominator

        temperature_relative_underheating = 1 / \
            (math.e ** ((coefficient_Kzag * area_tube_bundle_surface_total) /
             (mass_flow_cooling_water * 1000)) - 1)  # p.14

        temperature_saturation_steam = temperature_cooling_water_2 + temperature_relative_underheating * \
            (temperature_cooling_water_2 - temperature_cooling_water_1)  # p.15

        pressure_flow_path_1_mpa = seuif97.tx(
            temperature_saturation_steam, 1.0, 1)

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
            'pressure_flow_path_1': pressure_flow_path_1_kgf_cm2,
            'is_extrapolated': temperature_cooling_water_average_heating > 100.0 or
            speed_cooling_water > max(k_interpolation_data['speed_points']) or
            temperature_cooling_water_average_heating > max(
                k_interpolation_data['temperature_points'])
        })

        return results