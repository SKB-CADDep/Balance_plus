"""
Скрипт профилирования и генерации отчетов по расчету конденсатора (Метод Бермана).

Использует алгоритмическую модель, основанную на трудах Л.Д. Бермана, 
для расчета тепло-гидравлических характеристик. Автоматически перебирает 
различные расходы пара и температуры охлаждающей воды, формируя матрицу 
результатов и сохраняя её в человекочитаемый Markdown-отчет.
"""

from _common import setup_path

setup_path()

# generate_berman_report.py
from app.utils.berman_strategy import BermanStrategy


def create_markdown_table(headers, data_rows):
    """
    Создает строку таблицы в формате Markdown.

    Args:
        headers (list): Список заголовков столбцов.
        data_rows (list): Список списков, где каждый внутренний список - это строка данных.

    Returns:
        str: Строка, представляющая полную таблицу в формате Markdown.
    """
    header_line = "| " + " | ".join(map(str, headers)) + " |"
    # Выравнивание по левому краю для первого столбца, по правому для остальных
    separator_line = "|:---" + "|---:".join([""] * len(headers)) + "|"

    row_lines = []
    for row in data_rows:
        # Форматируем только числовые значения (пропуская первый элемент, если это текст)
        formatted_row = [row[0]] + [f"{val:.3f}" if isinstance(val, (int, float)) else val for val in row[1:]]
        row_lines.append("| " + " | ".join(map(str, formatted_row)) + " |")

    return "\n".join([header_line, separator_line, *row_lines])


def run_berman_simulation(main_water_flow, built_in_water_flow, num_bundles_label, fouling_factor_raw, include_ejector_data):
    """
    Настраивает параметры, запускает симуляцию по методу Бермана и форматирует результаты.

    [ENGINEERING CONTEXT]
    Почему используется деление на 1_000_000 и на 860:
    Исторически термическое сопротивление загрязнений (R_заг) задавалось в (м²·ч·°C)/ккал, 
    причем значения часто умножались на 10^6. Для перевода этого параметра в систему СИ (м²·К/Вт) 
    используется коэффициент 860 (1 кВт = 860 ккал/ч).

    Args:
        main_water_flow (float): Расход воды в основном пучке (в кг/с или т/ч в зависимости от настроек системы).
        built_in_water_flow (float): Расход воды во встроенном пучке.
        num_bundles_label (str): Метка количества активных пучков (например, "1" или "2").
        fouling_factor_raw (float): "Сырое" значение коэффициента загрязнения в исторических единицах.
        include_ejector_data (bool): Флаг, определяющий необходимость включения расчета эжекторов.

    Returns:
        str: Строка с отчетом в формате Markdown (на основе собранных данных).
    """
    # Преобразование коэффициента загрязнения из старых единиц в СИ (м²·К/Вт)
    fouling_factor_old_units = fouling_factor_raw / 1_000_000
    fouling_factor_si = fouling_factor_old_units / 860

    # Сборка словаря с параметрами для передачи в стратегию
    simulation_params = {
        # Геометрия и номинальные параметры
        "length_cooling_tubes_of_the_main_bundle": 7.080,
        "number_cooling_water_passes_of_the_main_bundle": 2,
        "number_cooling_tubes_of_the_main_bundle": 1754,
        "enthalpy_flow_path_1": 2175.68,
        "mass_flow_steam_nom": 16.00,
        "thermal_conductivity_cooling_surface_tube_material": 37.0,
        "diameter_inside_of_pipes": 22.0,  # в мм
        "thickness_pipe_wall": 1.0,  # в мм
        "BAP": float(num_bundles_label),  # Количество активных пучков

        # Списки итеративных параметров
        "coefficient_R_list": [fouling_factor_si],
        "temperature_cooling_water_1_list": [4, 5, 10, 15, 20, 25, 30, 35],
        "mass_flow_steam_list": [16, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        "mass_flow_cooling_water_list": [main_water_flow],

        # Параметры для встроенного пучка (могут быть пустыми)
        "mass_flow_cooling_water_built_in_beam_list": [built_in_water_flow],
        "length_cooling_tubes_of_the_built_in_bundle": 0.0,
        "number_cooling_water_passes_of_the_built_in_bundle": 0,
        "number_cooling_tubes_of_the_built_in_bundle": 0,
        "temperature_cooling_water_built_in_beam_1_list": [0] * 8,  # Заглушка

        # Параметры для расчета эжекторов
        "mass_flow_air": 16.5 if include_ejector_data else 0.0,
    }

    # Создание и запуск стратегии
    strategy = BermanStrategy()
    results = strategy.calculate(simulation_params)

    # Форматирование результатов расчета эжекторов в таблицу MD
    _report_string = ""
    if include_ejector_data and results["ejector_results"]:
        ejector_results = results["ejector_results"]
        # Собираем уникальные температуры и сортируем по убыванию
        _unique_temps = sorted(
            {r["inlet_water_temperature_C"] for r in ejector_results},
            reverse=True
        )


if __name__ == "__main__":
    # Пример вызова с конкретными параметрами
    final_report_content = run_berman_simulation(
        main_water_flow=1200,
        built_in_water_flow=0,
        num_bundles_label="1",
        fouling_factor_raw=0.10,
        include_ejector_data=True,
    )

    # Запись сгенерированного отчета в файл
    report_filename = "berman_report.md"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(final_report_content)

    print(f"Файл '{report_filename}' успешно создан.")

