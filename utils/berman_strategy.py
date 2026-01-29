import math
from seuif97 import *

class BermanStrategy:
    """
    Методика предназначена для расчета абсолютного давления пара в конденсаторе P_steam (давление за последней ступенью
    турбины, без учета гидравлических потерь в переходном патрубке) на основе геометрических характеристик конденсатора
    и параметров охлаждающей воды. Расчет ведется согласно нормативному методу Л.Д. Бермана для температур охлаждающей
    воды до 45°С.
    Алгоритм учитывает наличие двух пучков трубок: основного (ОП) и встроенного (ВП).
    """

    def calculate(self, params: dict) -> dict:
        """
        Выполняет основной расчет.

        :param params: Словарь с входными параметрами.
        :return: Словарь с результатами расчета для основного контура и эжекторов.
        """
        # --- 1. Извлечение и подготовка входных данных ---

        # Геометрия: длины пучков
        L = [0.0] * 3
        L[1] = params['L_main'] / 1000.0
        L[2] = params.get('L_builtin', 0.0) / 1000.0

        # Геометрия: число ходов
        Z = [0] * 3
        Z[1] = params['Z_main']
        Z[2] = params.get('Z_builtin', 0)

        # Геометрия: количество трубок
        N = [0] * 3
        N[1] = params['N_main']
        N[2] = params.get('N_builtin', 0)

        # Параметры пара и материалов
        H_steam = params['H_steam'] # ккал/кг энтальпия определяется как разность энтальпий перед конденсатором и энтальпии конденсата
        G_nom = params['G_nom']
        lam = params['lambda']  # Используем lam, так как lambda - зарезервированное слово Python

        # Диаметры и толщины в метрах
        d_in = params['d_in'] / 1000.0
        S_tube = params['S_tube'] / 1000.0

        # Списки итеративных параметров
        W = [params['W_main_list'],
             params.get('W_builtin_list', [])]
        t1 = [params['t1_main_list'],
              params.get('t1_builtin_list', [])]
        G = params['G_steam_list']
        coefficient_b_list = params['coefficient_b_list']

        # Расход воздуха для расчета эжекторов
        G_air = params.get('G_air', 0)

        # --- 2. Инициализация рабочих матриц и переменных ---

        # Инициализируем матрицы для хранения итеративных данных
        # Размер определяется количеством заданных значений

        # Для расходов воды берем максимум между основным и встроенным пучком (если он есть)
        len_w_main = len(W[0])
        len_w_builtin = len(W[1]) if len(W) > 1 and W[1] else 0
        size_w = max(len_w_main, len_w_builtin) + 1

        # Для температур
        len_t_main = len(t1[0])
        len_t_builtin = len(t1[1]) if len(t1) > 1 and t1[1] else 0
        size_t = max(len_t_main, len_t_builtin) + 1

        # Для расходов пара и загрязнений
        size_g = len(G) + 1
        size_r = len(coefficient_b_list) + 1

        W_matrix = [[0.0] * 3 for _ in range(size_w)]
        t_matrix = [[0.0] * 3 for _ in range(size_t)]
        steam_flows = [0.0] * size_g
        fouling_resistances = [0.0] * size_r

        # Заполнение матриц из входных списков (с 1-индексацией, как в оригинале)
        for i, val in enumerate(W[0], 1): W_matrix[i][1] = val
        if len(W) > 1 and W[1]:
            for i, val in enumerate(W[1], 1): W_matrix[i][2] = val

        max_temp_idx = 0
        # Заполняем Main
        for i, val in enumerate(t1[0], 1):
            t_matrix[i][1] = val
            # Обновляем макс индекс
            if val != 0 and i > max_temp_idx: max_temp_idx = i

        # Заполняем Built-in и тоже обновляем max_temp_idx
        if len(t1) > 1 and t1[1]:
            for i, val in enumerate(t1[1], 1):
                t_matrix[i][2] = val
                # Обновляем макс индекс, если ВП длиннее или единственный
                if val != 0 and i > max_temp_idx: max_temp_idx = i

        max_steam_flow_idx = 0
        for i, val in enumerate(G, 1):
            steam_flows[i] = val
            if val != 0: max_steam_flow_idx = i

        # Расчет R* по коэффициенту бета: R* = (417.3 - 417.2 * beta) * 10^-6
        for i, beta in enumerate(coefficient_b_list, 1):
            fouling_resistances[i] = (417.3 - 417.2 * beta) * 1e-6

            # --- 3. Основной цикл расчетов ---

        main_results = []
        pi = math.pi

        # Расчетные переменные для каждого пучка
        C = [0.0] * 3
        B = [0.0] * 3
        X = [0.0] * 3
        Phi_c = [0.0] * 3
        Phi_t = [0.0] * 3
        Phi_z = [0.0] * 3
        g_k_priv = [0.0] * 3
        Phi_g = [0.0] * 3
        K_base = [0.0] * 3
        K_load = [0.0] * 3
        K_clean = [0.0] * 3
        K_dirty = [0.0] * 3
        delta_t_heat = [0.0] * 3
        delta_t = [0.0] * 3
        t_sat = [0.0] * 3
        avg_water_temps = [0.0] * 3

        # Расчет площадей поверхности для каждого пучка
        F = [0.0] * 3
        F[1] = pi * L[1] * N[1] * (d_in + 2.0 * S_tube)
        # Проверяем физическое наличие второго пучка
        if L[2] > 0 and N[2] > 0:
            F[2] = pi * L[2] * N[2] * (d_in + 2.0 * S_tube)
        else:
            F[2] = 0.0

        F_total = F[1] + F[2]
        g_k_nom = (G_nom * 1000.0 / F_total) if F_total != 0 else 0.0

        # Внешние циклы по всем вариантам входных данных
        for i in range(1, size_w):
            # Если оба расхода 0, прерываем (но если один есть - работаем)
            if W_matrix[i][1] == 0 and W_matrix[i][2] == 0: break

            # Определяем статус активности каждого пучка отдельно
            is_op_active = (F[1] > 0) and (W_matrix[i][1] > 0)
            is_vp_active = (F[2] > 0) and (W_matrix[i][2] > 0)

            use_two_bundles = is_op_active and is_vp_active

            # Считаем активную площадь
            current_F_total = 0.0
            if is_op_active: current_F_total += F[1]
            if is_vp_active: current_F_total += F[2]

            # Защита от деления на ноль, если все отключено (хотя break сработает раньше)
            if current_F_total == 0: continue

            # Расчет скорости воды в трубках для каждого пучка
            if N[1] > 0 and d_in > 0:
                C[1] = W_matrix[i][1] * Z[1] / (900.0 * pi * N[1] * d_in ** 2)
            else:
                C[1] = 0.0

            if N[2] > 0 and d_in > 0:
                C[2] = W_matrix[i][2] * Z[2] / (900.0 * pi * N[2] * d_in ** 2)
            else:
                C[2] = 0.0

            for m in range(1, len(coefficient_b_list) + 1):
                current_fouling_resistance = fouling_resistances[m]
                if current_fouling_resistance == 0 and m > 1: break

                for j in range(1, max_temp_idx + 1):
                    # Прерываем, только если данных нет ни для ОП, ни для ВП
                    if t_matrix[j][1] == 0 and t_matrix[j][2] == 0: break

                    # Если температура задана только для одного пучка, копируем её во второй
                    if t_matrix[j][1] == 0 and t_matrix[j][2] != 0:
                        t_matrix[j][1] = t_matrix[j][2]
                    elif t_matrix[j][2] == 0 and t_matrix[j][1] != 0:
                        t_matrix[j][2] = t_matrix[j][1]

                    for l in range(1, max_steam_flow_idx + 1):
                        current_steam_flow = steam_flows[l]
                        if current_steam_flow == 0: break

                        delta_t_heat[1], delta_t_heat[2] = 0.0, 0.0

                        # Цикл для расчета коэффициента теплопередачи (без итераций, выполняется один раз для инициализации)
                        for _ in range(1):
                            for bundle_idx in range(1, 3):
                                # Универсальная проверка активности
                                if bundle_idx == 1 and not is_op_active: continue
                                if bundle_idx == 2 and not is_vp_active: continue
                                avg_water_temps[bundle_idx] = t_matrix[j][bundle_idx] + delta_t_heat[bundle_idx]

                                # Коэффициент скорости воды
                                if C[bundle_idx] > 0 and d_in > 0:
                                    B[bundle_idx] = 1.1 * C[bundle_idx] / (params['d_in']) ** 0.25  # Используем диаметр в мм
                                    X[bundle_idx] = 0.12 * (1.0 + 0.15 * avg_water_temps[bundle_idx])
                                    Phi_c[bundle_idx] = B[bundle_idx] ** X[bundle_idx]
                                else:
                                    B[bundle_idx], X[bundle_idx], Phi_c[bundle_idx] = 0, 0, 1.0

                                # Коэффициент температуры воды
                                if avg_water_temps[bundle_idx] < 35.0:
                                    Phi_t[bundle_idx] = 1.0 - 0.00042 * (35.0 - avg_water_temps[bundle_idx]) ** 2
                                else:
                                    Phi_t[bundle_idx] = 1.0 + 0.002 * (avg_water_temps[bundle_idx] - 35.0)

                                # Коэффициент числа ходов
                                if avg_water_temps[bundle_idx] < 35.0:
                                    Phi_z[bundle_idx] = 1.0 + (Z[bundle_idx] - 2.0) / 10.0 * (1.0 - avg_water_temps[bundle_idx] / 35.0)
                                else:
                                    Phi_z[bundle_idx] = 1.0 + (Z[bundle_idx] - 2.0) / 10.0 * (1.0 - avg_water_temps[bundle_idx] / 45.0)

                                # Приведенный расход пара
                                g_k_priv[bundle_idx] = (0.9 - 0.012 * avg_water_temps[bundle_idx]) * g_k_nom

                                # Базовый коэффициент теплопередачи
                                K_base[bundle_idx] = 3500.0 * Phi_c[bundle_idx] * Phi_t[bundle_idx] * Phi_z[bundle_idx]

                            for bundle_idx in range(1, 3):
                                # Универсальная проверка активности
                                if bundle_idx == 1 and not is_op_active: continue
                                if bundle_idx == 2 and not is_vp_active: continue

                                # Считаем удельную нагрузку на основе АКТИВНОЙ площади.
                                g_k = current_steam_flow * 1000.0 / current_F_total if current_F_total != 0 else 0.0

                                load_ratio = g_k / g_k_priv[bundle_idx] if g_k_priv[bundle_idx] != 0 else float('inf')

                                # Коэффициент удельной паровой нагрузки
                                Phi_g[bundle_idx] = load_ratio * (2.0 - load_ratio) if load_ratio < 1.0 else 1.0

                                # Коэффициент теплопередачи с учетом паровой нагрузки
                                K_load[bundle_idx] = K_base[bundle_idx] * Phi_g[bundle_idx]

                                # Учет термического сопротивления стенки
                                k_inv = 1.0 / K_load[bundle_idx] if K_load[bundle_idx] != 0 else float('inf')
                                wall_resistance_term = (S_tube / lam - 0.001 / 90.0) if lam != 0 else float('inf')
                                new_k_inv = k_inv + wall_resistance_term

                                # Коэффициент теплопередачи с учетом материала стенки (чистый)
                                K_clean[bundle_idx] = 1.0 / new_k_inv if not math.isinf(new_k_inv) else 0.0

                                # Расчет нагрева воды
                                D = g_k * F[bundle_idx]

                                delta_t_heat[bundle_idx] = D * H_steam / (W_matrix[i][bundle_idx] * 1000.0) if W_matrix[i][bundle_idx] > 0 else 0.0

                        # Итерационный решатель для двухпучковых конденсаторов
                        if use_two_bundles:
                            temp_diff_check, temp_diff_step = 0.0, 0.1
                            for _ in range(3000):  # Итерационный цикл
                                for bundle_idx in range(1, 3):
                                    k_inv = 1.0 / K_clean[bundle_idx] if K_clean[bundle_idx] != 0 else float('inf')
                                    K_dirty[bundle_idx] = 1.0 / (k_inv + current_fouling_resistance)

                                    exp_arg = (K_dirty[bundle_idx] / W_matrix[i][bundle_idx] * F[bundle_idx] / 1000.0) if \
                                    W_matrix[i][bundle_idx] > 0 else float('inf')
                                    try:
                                        exp_val = math.exp(exp_arg)
                                    except OverflowError:
                                        exp_val = float('inf')

                                    delta_t[bundle_idx] = delta_t_heat[bundle_idx] / (exp_val - 1.0) if (exp_val - 1.0) != 0 else 0.0
                                    t_sat[bundle_idx] = t_matrix[j][bundle_idx] + delta_t_heat[bundle_idx] + delta_t[bundle_idx]

                                temp_diff = t_sat[1] - t_sat[2]
                                if temp_diff_check * temp_diff < 0: temp_diff_step /= 5.0
                                temp_diff_check = temp_diff
                                if abs(temp_diff) <= 0.000001: break

                                step_direction = -temp_diff_step if temp_diff > 0 else temp_diff_step
                                delta_t_heat[1] += step_direction
                                if W_matrix[i][2] > 0:
                                    delta_t_heat[2] = (current_steam_flow * H_steam - delta_t_heat[1] * W_matrix[i][1]) / W_matrix[i][2]
                                else:
                                    break

                            t_sat_final = t_sat[1]

                        else:  # Расчет для однопучкового конденсатора
                            # Определяем индекс активного пучка
                            active_idx = 1 if is_op_active else 2
                            k_inv = 1.0 / K_clean[active_idx] if K_clean[active_idx] != 0 else float('inf')
                            K_dirty[active_idx] = 1.0 / (k_inv + current_fouling_resistance)

                            exp_arg = (K_dirty[active_idx] / W_matrix[i][active_idx] * F[active_idx] / 1000.0)
                            try:
                                exp_val = math.exp(exp_arg)
                            except OverflowError:
                                exp_val = float('inf')

                            if exp_val > 1.00001:
                                delta_t[active_idx] = delta_t_heat[active_idx] / (exp_val - 1.0)
                            else:
                                delta_t[active_idx] = 0.0
                            t_sat_final = t_matrix[j][active_idx] + delta_t_heat[active_idx] + delta_t[active_idx]

                        # Расчет давления насыщения по финальной температуре
                        saturation_temp_K = t_sat_final + 273.15
                        try:
                            pressure_exponent = 82.86568 + 1.028003 / 100.0 * saturation_temp_K - 7821.541 / saturation_temp_K - 11.48776 * math.log(saturation_temp_K)
                            P_steam_formula_atm = math.exp(pressure_exponent) / 0.0980665
                            P_steam_formula_Pa = P_steam_formula_atm * 98.0665

                            P_steam_seuif_Pa = tx(t_sat_final,1.0,0) * 1000
                            P_steam_seuif_atm = P_steam_seuif_Pa / 98.0665
                        except (ValueError, ZeroDivisionError):
                            condenser_pressure_Pa = 0.0

                        # Температура на выходе
                        t2_main = t_matrix[j][1] + delta_t_heat[1]

                        # Для встроенного пучка считаем, только если он используется
                        t2_builtin = 0.0
                        if is_vp_active:
                            t2_builtin = t_matrix[j][2] + delta_t_heat[2]

                        main_results.append({
                            "F_main": F[1],
                            "F_builtin": F[2],
                            "g_k_nom": g_k_nom,
                            "C_main": C[1],
                            "C_builtin": C[2],
                            "B_main": B[1],
                            "B_builtin": B[2],
                            "X_main": X[1],
                            "X_builtin": X[2],
                            "Phi_c_main": Phi_c[1],
                            "Phi_c_builtin": Phi_c[2],
                            "Phi_z_main": Phi_z[1],
                            "Phi_z_builtin": Phi_z[2],
                            "Phi_t_main": Phi_t[1],
                            "Phi_t_builtin": Phi_t[2],
                            "g_k_priv_main": g_k_priv[1],
                            "g_k_priv_builtin": g_k_priv[2],
                            "g_k": g_k,
                            "Phi_g_main": Phi_g[1],
                            "Phi_g_builtin": Phi_g[2],
                            "K_base_main": K_base[1],
                            "K_base_builtin": K_base[2],
                            "K_load_main": K_load[1],
                            "K_load_builtin": K_load[2],
                            "K_clean_main": K_clean[1],
                            "K_clean_builtin": K_clean[2],
                            "K_dirty_main": K_dirty[1],
                            "K_dirty_builtin": K_dirty[2],
                            "D": D,
                            "delta_t_heat_main": delta_t_heat[1],
                            "delta_t_heat_builtin": delta_t_heat[2],
                            "delta_t_main": delta_t[1],
                            "delta_t_builtin": delta_t[2],
                            "t_sat": t_sat_final,
                            "t2_main": t2_main,
                            "t2_builtin": t2_builtin,
                            "P_steam_seuif_Pa": P_steam_seuif_Pa,
                            "P_steam_seuif_atm": P_steam_seuif_atm,
                            "P_steam_formula_Pa": P_steam_formula_Pa,
                            "P_steam_formula_atm": P_steam_formula_atm
                        })

        # --- 4. Расчет эжекторов ---
        ejector_results = []
        if G_air > 0:
            for num_ejectors in range(1, 3):
                for temp_idx in range(1, max_temp_idx + 1):
                    list_idx = max_temp_idx - temp_idx + 1
                    inlet_temp_C = t_matrix[list_idx][1]
                    if inlet_temp_C == 0:
                        inlet_temp_C = t_matrix[list_idx][2]
                    if inlet_temp_C == 0:
                        continue
                    water_temp_K = inlet_temp_C + 273.15 + 1.0
                    scaled_temp = water_temp_K / 1000.0
                    try:
                        ejector_pressure_exponent = -7.821541 / scaled_temp + 82.86586 + 10.28 * scaled_temp - 11.48776 * math.log(
                            water_temp_K)
                        ejector_pressure_Pa = math.exp(ejector_pressure_exponent)
                        P_ejector_kPa = (0.009 + 0.0003 * G_air / num_ejectors + ejector_pressure_Pa * 10) * 100
                        P_ejector_atm = P_ejector_kPa / 98.0665

                        ejector_results.append({
                            "number_of_ejectors": num_ejectors,
                            "P_ejector_kPa": P_ejector_kPa,
                            "P_ejector_atm": P_ejector_atm
                        })
                    except (ValueError, ZeroDivisionError):
                        pass

        return {'main_results': main_results, 'ejector_results': ejector_results}
