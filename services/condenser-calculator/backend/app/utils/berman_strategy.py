import math

class BermanStrategy:
    """
    Рассчитывает теплогидравлические характеристики конденсатора по методике С.С. Бермана.
    """
    def calculate(self, params: dict) -> dict:
        """
        Выполняет основной расчет.

        :param params: Словарь с входными параметрами.
        :return: Словарь с результатами расчета для основного контура и эжекторов.
        """
        # --- 1. Извлечение и подготовка входных данных ---

        # Геометрия: длины пучков
        bundle_lengths = [0.0] * 3
        bundle_lengths[1] = params['length_cooling_tubes_of_the_main_bundle']
        bundle_lengths[2] = params.get('length_cooling_tubes_of_the_built_in_bundle', 0.0)

        # Геометрия: число ходов
        num_passes = [0] * 3
        num_passes[1] = params['number_cooling_water_passes_of_the_main_bundle']
        num_passes[2] = params.get('number_cooling_water_passes_of_the_built_in_bundle', 0)

        # Геометрия: количество трубок
        num_tubes = [0] * 3
        num_tubes[1] = params['number_cooling_tubes_of_the_main_bundle']
        num_tubes[2] = params.get('number_cooling_tubes_of_the_built_in_bundle', 0)

        # Параметры пара и материалов
        enthalpy = params['enthalpy_flow_path_1']
        nominal_steam_flow = params['mass_flow_steam_nom']
        thermal_conductivity = params['thermal_conductivity_cooling_surface_tube_material']
        bap_coefficient = params.get('BAP', 1)  # Количество пучков (1 или 2)
        
        # Диаметры и толщины в метрах
        diameter_inside_m = params['diameter_inside_of_pipes'] / 1000.0
        wall_thickness_m = params['thickness_pipe_wall'] / 1000.0
        
        # Списки итеративных параметров
        water_flow_lists = [params['mass_flow_cooling_water_list'], 
                            params.get('mass_flow_cooling_water_built_in_beam_list', [])]
        inlet_temp_lists = [params['temperature_cooling_water_1_list'], 
                            params.get('temperature_cooling_water_built_in_beam_1_list', [])]
        steam_flow_list = params['mass_flow_steam_list']
        fouling_resistance_list = params['coefficient_R_list'] # Аналог β, но в других ед.

        # Расход воздуха для расчета эжекторов
        mass_flow_air = params.get('mass_flow_air', 0)

        # --- 2. Инициализация рабочих матриц и переменных ---
        
        # Инициализируем матрицы для хранения итеративных данных
        # Размер 11 - условный максимум из оригинального кода
        water_flows_matrix = [[0.0] * 3 for _ in range(11)]
        inlet_temps_matrix = [[0.0] * 3 for _ in range(11)]
        steam_flows = [0.0] * 11
        fouling_resistances = [0.0] * 11

        # Заполнение матриц из входных списков (с 1-индексацией, как в оригинале)
        for i, val in enumerate(water_flow_lists[0], 1): water_flows_matrix[i][1] = val
        if len(water_flow_lists) > 1 and water_flow_lists[1]:
            for i, val in enumerate(water_flow_lists[1], 1): water_flows_matrix[i][2] = val

        max_temp_idx = 0
        for i, val in enumerate(inlet_temp_lists[0], 1):
            inlet_temps_matrix[i][1] = val
            if val != 0: max_temp_idx = i
        if len(inlet_temp_lists) > 1 and inlet_temp_lists[1]:
            for i, val in enumerate(inlet_temp_lists[1], 1): inlet_temps_matrix[i][2] = val

        max_steam_flow_idx = 0
        for i, val in enumerate(steam_flow_list, 1):
            steam_flows[i] = val
            if val != 0: max_steam_flow_idx = i

        for i, val in enumerate(fouling_resistance_list, 1):
            fouling_resistances[i] = val 

        # --- 3. Основной цикл расчетов ---

        main_results = []
        pi = math.pi
        
        # Расчетные переменные для каждого пучка
        water_speeds = [0.0] * 3
        ref_heat_transfer_coeffs = [0.0] * 3
        heat_transfer_coeffs = [0.0] * 3
        water_heating_values = [0.0] * 3
        heat_transfer_coeffs_with_fouling = [0.0] * 3
        undercooling_values = [0.0] * 3
        saturation_temps = [0.0] * 3
        avg_water_temps = [0.0] * 3

        # Расчет площадей поверхности для каждого пучка
        surface_areas = [0.0] * 3
        surface_areas[1] = pi * bundle_lengths[1] * num_tubes[1] * (diameter_inside_m + 2.0 * wall_thickness_m)
        surface_areas[2] = pi * bundle_lengths[2] * num_tubes[2] * (diameter_inside_m + 2.0 * wall_thickness_m) if bap_coefficient > 2 else 0.0

        total_surface_area = surface_areas[1] + surface_areas[2]
        nominal_steam_load_per_area = (nominal_steam_flow * 1000.0 / total_surface_area) if total_surface_area != 0 else 0.0

        # Внешние циклы по всем вариантам входных данных
        for i in range(1, len(water_flow_lists[0]) + 1):
            if water_flows_matrix[i][1] == 0: break

            # Расчет скорости воды в трубках для каждого пучка
            if num_tubes[1] > 0 and diameter_inside_m > 0:
                water_speeds[1] = water_flows_matrix[i][1] * num_passes[1] / (900.0 * pi * num_tubes[1] * diameter_inside_m**2)
            else:
                water_speeds[1] = 0.0

            if bap_coefficient > 2 and num_tubes[2] > 0 and diameter_inside_m > 0:
                water_speeds[2] = water_flows_matrix[i][2] * num_passes[2] / (900.0 * pi * num_tubes[2] * diameter_inside_m**2)
            else:
                water_speeds[2] = 0.0

            for m in range(1, len(fouling_resistance_list) + 1):
                current_fouling_resistance = fouling_resistances[m]
                if current_fouling_resistance == 0 and m > 1: break

                for j in range(1, max_temp_idx + 1):
                    if inlet_temps_matrix[j][1] == 0: break

                    for l in range(1, max_steam_flow_idx + 1):
                        current_steam_flow = steam_flows[l]
                        if current_steam_flow == 0: break

                        water_heating_values[1], water_heating_values[2] = 0.0, 0.0

                        # Цикл для расчета K (без итераций, выполняется один раз для инициализации)
                        for _ in range(1):
                            for bundle_idx in range(1, 3):
                                avg_water_temps[bundle_idx] = inlet_temps_matrix[j][bundle_idx] + water_heating_values[bundle_idx]
                                
                                # Поправка на скорость воды
                                if water_speeds[bundle_idx] > 0 and diameter_inside_m > 0:
                                    B_factor = 1.1 * water_speeds[bundle_idx] / (params['diameter_inside_of_pipes'])**0.25 # Используем диаметр в мм
                                    X_exponent = 0.12 * (1.0 + 0.15 * avg_water_temps[bundle_idx])
                                    speed_correction_factor = B_factor**X_exponent
                                else:
                                    speed_correction_factor = 1.0

                                # Поправки на температуру и число ходов
                                temp_correction_factor = 1.0 - 0.42 * (35.0 - avg_water_temps[bundle_idx])**2 * 0.001
                                passes_correction_factor = 1.0 + 0.1 * (num_passes[bundle_idx] - 2.0) * (1.0 - avg_water_temps[bundle_idx] / 35.0)
                                
                                ref_heat_transfer_coeffs[bundle_idx] = (0.9 - 0.012 * avg_water_temps[bundle_idx]) * nominal_steam_load_per_area
                                heat_transfer_coeffs[bundle_idx] = 3500.0 * speed_correction_factor * temp_correction_factor * passes_correction_factor
                                
                                if bap_coefficient <= 2: break

                            for bundle_idx in range(1, 3):
                                # Поправка на паровую нагрузку
                                current_steam_load_per_area = current_steam_flow * 1000.0 / total_surface_area if total_surface_area != 0 else 0.0
                                load_ratio = current_steam_load_per_area / ref_heat_transfer_coeffs[bundle_idx] if ref_heat_transfer_coeffs[bundle_idx] != 0 else float('inf')
                                load_correction_factor = load_ratio * (2.0 - load_ratio) if load_ratio < 1.0 else 1.0
                                heat_transfer_coeffs[bundle_idx] *= load_correction_factor

                                # Учет термического сопротивления стенки
                                k_inv = 1.0 / heat_transfer_coeffs[bundle_idx] if heat_transfer_coeffs[bundle_idx] != 0 else float('inf')
                                wall_resistance_term = (wall_thickness_m / thermal_conductivity - 0.001 / 90.0) if thermal_conductivity != 0 else float('inf')
                                new_k_inv = k_inv + wall_resistance_term
                                heat_transfer_coeffs[bundle_idx] = 1.0 / new_k_inv if not math.isinf(new_k_inv) else 0.0

                                # Расчет нагрева воды
                                heat_transfer_per_bundle = current_steam_load_per_area * surface_areas[bundle_idx]
                                water_heating_values[bundle_idx] = heat_transfer_per_bundle * enthalpy / (water_flows_matrix[i][bundle_idx] * 1000.0) if water_flows_matrix[i][bundle_idx] > 0 else 0.0
                                
                                if bap_coefficient <= 2: break

                        # Итерационный решатель для двухпучковых конденсаторов
                        if bap_coefficient > 2:
                            temp_diff_check, temp_diff_step = 0.0, 0.1
                            for _ in range(100): # Итерационный цикл
                                for bundle_idx in range(1, 3):
                                    k_inv = 1.0 / heat_transfer_coeffs[bundle_idx] if heat_transfer_coeffs[bundle_idx] != 0 else float('inf')
                                    heat_transfer_coeffs_with_fouling[bundle_idx] = 1.0 / (k_inv + current_fouling_resistance)

                                    exp_arg = (heat_transfer_coeffs_with_fouling[bundle_idx] / water_flows_matrix[i][bundle_idx] * surface_areas[bundle_idx] / 1000.0) if water_flows_matrix[i][bundle_idx] > 0 else float('inf')
                                    try: exp_val = math.exp(exp_arg)
                                    except OverflowError: exp_val = float('inf')

                                    undercooling_values[bundle_idx] = water_heating_values[bundle_idx] / (exp_val - 1.0) if (exp_val - 1.0) != 0 else 0.0
                                    saturation_temps[bundle_idx] = inlet_temps_matrix[j][bundle_idx] + water_heating_values[bundle_idx] + undercooling_values[bundle_idx]

                                temp_diff = saturation_temps[1] - saturation_temps[2]
                                if temp_diff_check * temp_diff < 0: temp_diff_step /= 5.0
                                temp_diff_check = temp_diff
                                if abs(temp_diff) <= 0.01: break

                                step_direction = -temp_diff_step if temp_diff > 0 else temp_diff_step
                                water_heating_values[1] += step_direction
                                if water_flows_matrix[i][2] > 0:
                                    water_heating_values[2] = (current_steam_flow * enthalpy - water_heating_values[1] * water_flows_matrix[i][1]) / water_flows_matrix[i][2]
                                else:
                                    break
                            
                            final_saturation_temp = saturation_temps[1]

                        else: # Расчет для однопучкового конденсатора
                            bundle_idx = 1
                            k_inv = 1.0 / heat_transfer_coeffs[bundle_idx] if heat_transfer_coeffs[bundle_idx] != 0 else float('inf')
                            heat_transfer_coeffs_with_fouling[bundle_idx] = 1.0 / (k_inv + current_fouling_resistance)

                            exp_arg = (heat_transfer_coeffs_with_fouling[bundle_idx] / water_flows_matrix[i][bundle_idx] * surface_areas[bundle_idx] / 1000.0) if water_flows_matrix[i][bundle_idx] > 0 else float('inf')
                            try: exp_val = math.exp(exp_arg)
                            except OverflowError: exp_val = float('inf')

                            undercooling_values[bundle_idx] = water_heating_values[bundle_idx] / (exp_val - 1.0) if (exp_val - 1.0) != 0 else 0.0
                            final_saturation_temp = inlet_temps_matrix[j][bundle_idx] + water_heating_values[bundle_idx] + undercooling_values[bundle_idx]

                        # Расчет давления насыщения по финальной температуре
                        saturation_temp_K = final_saturation_temp + 273.15
                        try:
                            pressure_exponent = 82.86568 + 1.028003 / 100.0 * saturation_temp_K - 7821.541 / saturation_temp_K - 11.48776 * math.log(saturation_temp_K)
                            condenser_pressure_Pa = math.exp(pressure_exponent)
                        except (ValueError, ZeroDivisionError):
                            condenser_pressure_Pa = 0.0

                        main_results.append({
                            "condenser_pressure_Pa": condenser_pressure_Pa,
                            "saturation_temperature_C": final_saturation_temp,
                            "undercooling_main_bundle_C": undercooling_values[1],
                            "undercooling_built_in_bundle_C": undercooling_values[2],
                        })
        
        # --- 4. Расчет эжекторов ---
        ejector_results = []
        if mass_flow_air > 0:
            for num_ejectors in range(1, 3):
                for temp_idx in range(1, max_temp_idx + 1):
                    list_idx = max_temp_idx - temp_idx + 1
                    inlet_temp_C = inlet_temps_matrix[list_idx][1]
                    water_temp_K = inlet_temp_C + 273.15 + 1.0
                    scaled_temp = water_temp_K / 1000.0
                    try:
                        ejector_pressure_exponent = -7.821541 / scaled_temp + 82.86586 + 10.28 * scaled_temp - 11.48776 * math.log(water_temp_K)
                        ejector_pressure_Pa = math.exp(ejector_pressure_exponent)
                        ejector_pressure_kPa = (0.009 + 0.0003 * mass_flow_air / num_ejectors + ejector_pressure_Pa * 10) * 100

                        ejector_results.append({
                            "number_of_ejectors": num_ejectors,
                            "inlet_water_temperature_C": inlet_temp_C,
                            "ejector_pressure_kPa": ejector_pressure_kPa
                        })
                    except (ValueError, ZeroDivisionError):
                        pass

        return {'main_results': main_results, 'ejector_results': ejector_results}