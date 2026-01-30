from app.utils.metrovickers_strategy import MetroVickersStrategy


def print_beautifully(data_dict, friendly_names, title, keys_to_print):
    """
    Вспомогательная функция для красивой печати данных.
    """
    print(f"\n--- {title} ---")
    max_len = max(
        len(f"{friendly_names[k][0]} [{friendly_names[k][1]}]") for k in keys_to_print if k in friendly_names
    )
    for key in keys_to_print:
        if key in data_dict and key in friendly_names:
            value = data_dict[key]
            desc, unit = friendly_names[key]
            label = f"{desc} [{unit}]".ljust(max_len + 2)
            if isinstance(value, (int, float)):
                print(f"{label}: {value:.4f}")
            else:
                print(f"{label}: {value}")


def generate_and_print_tables(strategy, base_params):
    """
    Генерирует данные и выводит их в виде таблиц, аналогичных скриншоту.
    """
    print("\n" + "#" * 60)
    print("###      Генерация сводных таблиц с результатами      ###")
    print("#" * 60)

    # --- Параметры, которые будут меняться в циклах ---
    beta_values = [1.0, 0.75]  # Коэффициент b
    temp_values = [35, 37, 40]  # Температура t_ср (используется как t_ов1)
    flow_values = [1200, 1250, 1500, 1750, 2000, 2250, 2500]  # Расход воды

    COL_WIDTH = 9  # Ширина колонки для значений

    # --- Основной цикл для генерации таблиц ---
    for beta in beta_values:
        print("\n" + "=" * 60)
        print("4. Результаты для построения графиков")
        print(f"в= {beta}, Z= 2; материал трубок - сплав МНЖ5-1")
        print("=" * 60)

        # Печатаем заголовок таблицы (расходы воды)
        header = "t_ср".ljust(COL_WIDTH) + "".join([str(flow).ljust(COL_WIDTH) for flow in flow_values])
        print(header)

        # Цикл по строкам таблицы (температуры)
        for temp in temp_values:
            result_row = [f"{temp}°C".ljust(COL_WIDTH)]  # Начало строки с температурой

            # Цикл по столбцам таблицы (расходы воды)
            for flow in flow_values:
                current_params = base_params.copy()
                current_params["coefficient_b"] = beta
                current_params["temperature_cooling_water_1"] = float(temp)
                current_params["mass_flow_cooling_water"] = float(flow)

                try:
                    results = strategy.calculate(current_params)
                    pressure = results["pressure_flow_path_1"]
                    # Форматируем результат до 4 знаков после запятой
                    result_row.append(f"{pressure:.4f}".ljust(COL_WIDTH))
                except Exception as e:
                    print(f"Ошибка при расчете для B={beta}, T={temp}, G={flow}: {e}")
                    result_row.append("ERROR".ljust(COL_WIDTH))

            # Печатаем собранную строку результатов
            print("".join(result_row))


def main():
    strategy = MetroVickersStrategy()

    # --- Входные параметры для единичного расчета ---
    input_params = {
        "diameter_inside_of_pipes": 22.4,
        "thickness_pipe_wall": 0.8,
        "length_cooling_tubes_of_the_main_bundle": 13910,
        "number_cooling_tubes_of_the_main_bundle": 20904,
        "number_cooling_tubes_of_the_built_in_bundle": 0,
        "number_cooling_water_passes_of_the_main_bundle": 2,
        "mass_flow_cooling_water": 45000.0,
        "temperature_cooling_water_1": 45.0,
        "thermal_conductivity_cooling_surface_tube_material": 16.2,
        "coefficient_b": 1.0,
        "mass_flow_flow_path_1": 200.0,
        "degree_dryness_flow_path_1": 0.95,
    }

    # --- Словарь для перевода имен ---
    friendly_names = {
        "diameter_inside_of_pipes": ("Внутренний диаметр трубок", "мм"),
        "thickness_pipe_wall": ("Толщина стенки трубок", "мм"),
        "length_cooling_tubes_of_the_main_bundle": ("Активная длина труб", "м"),
        "number_cooling_tubes_of_the_main_bundle": ("Кол-во трубок осн. пучка", "шт"),
        "number_cooling_tubes_of_the_built_in_bundle": ("Кол-во трубок встр. пучка", "шт"),
        "number_cooling_water_passes_of_the_main_bundle": ("Число ходов воды (Z)", "шт"),
        "mass_flow_cooling_water": ("Расход охлаждающей воды", "т/ч"),
        "temperature_cooling_water_1": ("Температура воды на входе", "°C"),
        "thermal_conductivity_cooling_surface_tube_material": ("Теплопроводность материала", "Вт/(м·К)"),
        "coefficient_b": ("Коэффициент чистоты (β)", "-"),
        "mass_flow_flow_path_1": ("Расход пара", "т/ч"),
        "degree_dryness_flow_path_1": ("Степень сухости пара", "-"),
        "diameter_outside_of_pipes": ("Наружный диаметр трубок", "мм"),
        "area_tube_bundle_surface_total": ("Площадь поверхности осн. пучка", "м²"),
        "area_surface_of_the_air_cooler_tube_bundle": ("Площадь поверхности возд-ля", "м²"),
        "coefficient_Kf": ("Коэффициент отношения площадей", "-"),
        "coefficient_R1": ("Терм. сопротивление стенки", "м²·К/Вт"),
        "speed_cooling_water": ("Скорость охлаждающей воды", "м/с"),
        "heat_of_vaporization": ("Теплота парообразования", "ккал/кг"),
        "temperature_cooling_water_2": ("Температура воды на выходе", "°C"),
        "temperature_cooling_water_average_heating": ("Средняя температура воды", "°C"),
        "coefficient_K_temp": ("К-т теплопередачи (подобранный)", "Вт/(м²·К)"),
        "coefficient_K": ("К-т теплопередачи (чистый)", "Вт/(м²·К)"),
        "coefficient_R": ("Терм. сопротивление загрязнений", "м²·К/Вт"),
        "coefficient_Kzag": ("К-т теплопередачи (с загрязнением)", "Вт/(м²·К)"),
        "temperature_relative_underheating": ("Относительный недогрев", "°C"),
        "temperature_saturation_steam": ("Температура насыщения", "°C"),
        "pressure_flow_path_1": ("Давление пара в конденсаторе", "кгс/см²"),
    }

    # === ЧАСТЬ 1: Расчет и вывод для одного набора параметров ===
    print_beautifully(input_params, friendly_names, "Входные параметры для единичного расчета", input_params.keys())
    try:
        results = strategy.calculate(input_params)
        intermediate_keys = [
            "speed_cooling_water",
            "temperature_cooling_water_2",
            "temperature_cooling_water_average_heating",
            "coefficient_K_temp",
            "temperature_saturation_steam",
        ]
        print_beautifully(results, friendly_names, "Ключевые промежуточные результаты", intermediate_keys)
        print("\n" + "=" * 50)
        final_key = "pressure_flow_path_1"
        desc, unit = friendly_names[final_key]
        value = results[final_key]
        print(f"  Главный результат:\n  {desc}: {value:.4f} [{unit}]")
        print("=" * 50)
    except Exception as e:
        print(f"\n--- ОШИБКА ПРИ РАСЧЕТЕ --- \n{e}")

    # === ЧАСТЬ 2: Генерация и печать таблиц ===
    # base_params_for_tables = input_params.copy()
    # del base_params_for_tables['mass_flow_cooling_water']
    # del base_params_for_tables['temperature_cooling_water_1']
    # del base_params_for_tables['coefficient_b']
    #
    # generate_and_print_tables(strategy, base_params_for_tables)


if __name__ == "__main__":
    main()

