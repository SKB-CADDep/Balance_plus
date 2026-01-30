import xlrd
import json
import os
import re

# НАСТРОЙКИ
INPUT_FILE = 'geometry.xls'
SHEET_INDEX = 0

# Координаты колонок (0-based: A=0, P=15, Q=16, AA=26, AB=27)
COL_P = 15  # Заголовки (Wo, t1)
COL_Q = 16  # Начало данных пара/давления
COL_AA = 26  # Начало заголовка эжектора (t=)
COL_AB = 27  # Начало данных эжектора (30, 25...)


def clean_text(text):
    """
    Нормализует текст для ПОИСКА ключей (удаляет пробелы, lowercase).
    """
    if not isinstance(text, str): return str(text)
    text = text.lower().replace(' ', '').strip()
    replacements = {
        'а': 'a', 'в': 'b', 'е': 'e', 'к': 'k', 'м': 'm',
        'н': 'h', 'о': 'o', 'р': 'p', 'с': 'c', 'т': 't', 'х': 'x', 'у': 'y'
    }
    for rus, eng in replacements.items():
        text = text.replace(rus, eng)
    return text


def extract_floats(text):
    return [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", str(text))]


def get_cell_val_addr(sheet, cell_str):
    match = re.match(r"([A-Z]+)([0-9]+)", cell_str.upper())
    if not match: return None
    col_letters, row_num = match.groups()
    col_idx = 0
    for char in col_letters:
        col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
    col_idx -= 1
    row_idx = int(row_num) - 1
    try:
        val = sheet.cell_value(row_idx, col_idx)
        return val if val != '' else None
    except IndexError:
        return None


def get_range_values(sheet, row_num_excel, start_col_str, end_col_str):
    row_idx = row_num_excel - 1
    start_col = ord(start_col_str.upper()) - 65
    end_col = ord(end_col_str.upper()) - 65
    values = []
    for col_idx in range(start_col, end_col + 1):
        try:
            val = sheet.cell_value(row_idx, col_idx)
            if val != '' and val is not None:
                values.append(val)
        except IndexError:
            pass
    return values


def parse_results(sheet):
    print("--- НАЧАЛО ОБРАБОТКИ РЕЗУЛЬТАТОВ ---")
    condenser_modes = []
    current_table_obj = None
    current_g_steam_indices = []

    # --- ПАРСИНГ ЛЕВОЙ ЧАСТИ (Конденсатор P-Y) ---
    r = 0
    while r < sheet.nrows:
        try:
            raw_p = sheet.cell_value(r, COL_P)
            val_p = clean_text(raw_p)

            # 1. БЛОК "Wo=..."
            if 'wo=' in val_p and 'b=' in val_p:
                nums = extract_floats(raw_p)
                if len(nums) >= 3:
                    current_table_obj = {
                        "G_steam_axis": [],
                        "t1_main": [],
                        "pressures_axis": []
                    }
                    block = {
                        "W_main": nums[0],
                        "W_builtin": nums[1],
                        "coefficient_b": nums[2],
                        "table_data": [current_table_obj]
                    }
                    condenser_modes.append(block)
                    current_g_steam_indices = []

                    header_row = r + 1
                    if header_row < sheet.nrows:
                        col = COL_Q
                        while col < sheet.ncols:
                            val = sheet.cell_value(header_row, col)
                            if isinstance(val, (int, float)):
                                current_table_obj["G_steam_axis"].append(val)
                                current_g_steam_indices.append(col)
                            elif str(val).strip() == '' and len(current_table_obj["G_steam_axis"]) > 0:
                                break
                            elif str(val).strip() != '' and not isinstance(val, (int, float)):
                                break
                            col += 1
                    r += 2
                    continue

            # 2. СТРОКА ДАННЫХ "t1=..."
            if 't1=' in val_p and current_table_obj is not None:
                parts = str(raw_p).split('=')
                if len(parts) > 1:
                    val_part = parts[1]
                    t_nums = extract_floats(val_part)
                    if t_nums:
                        t1_val = t_nums[0]
                        current_table_obj["t1_main"].append(t1_val)

                        row_pressures = []
                        for col_idx in current_g_steam_indices:
                            try:
                                val = sheet.cell_value(r, col_idx)
                                row_pressures.append(val if val != '' else None)
                            except IndexError:
                                row_pressures.append(None)
                        current_table_obj["pressures_axis"].append(row_pressures)
        except IndexError:
            pass
        r += 1

    # --- ПАРСИНГ ПРАВОЙ ЧАСТИ (Эжектор AA-...) ---
    print("--- ПОИСК ЭЖЕКТОРА ---")
    ejector_data = {}
    ej_start_row = -1

    # 1. Ищем строку с "t=" в колонке AA
    for r_idx in range(10):  # Смотрим первые 10 строк
        try:
            val = sheet.cell_value(r_idx, COL_AA)
            # Используем clean_text для надежности (убираем пробелы, русские буквы)
            if 't=' in clean_text(val):
                ej_start_row = r_idx
                print(f"DEBUG: Эжектор найден в строке {r_idx + 1}")
                break
        except IndexError:
            pass

    if ej_start_row != -1:
        # 2. Читаем ось температур (начиная с колонки AB)
        t_axis = []
        col = COL_AB  # Колонка 27
        while col < sheet.ncols:
            val = sheet.cell_value(ej_start_row, col)
            if isinstance(val, (int, float)):
                t_axis.append(val)
            elif str(val).strip() != '':  # Если встретили текст - стоп
                break
            # Если пусто, тоже можно считать концом, но иногда бывают пропуски?
            # Обычно ось идет подряд. Если пусто - считаем конец.
            elif str(val).strip() == '':
                break
            col += 1

        # 3. Читаем строки данных ниже
        curves = []
        curr = ej_start_row + 1
        while curr < sheet.nrows:
            # Читаем название (Status) из AA
            status_label = sheet.cell_value(curr, COL_AA)

            # Если ячейка статуса пустая - таблица кончилась
            if str(status_label).strip() == '':
                break

            vals = []
            # Читаем ровно столько значений, сколько температур в шапке
            # Начиная с колонки AB
            for k in range(len(t_axis)):
                v = sheet.cell_value(curr, COL_AB + k)
                vals.append(v if v != '' else None)

            # Добавляем строку
            curves.append({
                "status_z": status_label,
                "values": vals
            })
            curr += 1

        ejector_data = {
            "t1_main_axis": t_axis,
            "curves": curves
        }
    else:
        print("DEBUG: Эжектор НЕ найден")

    return {
        "condenser_modes": condenser_modes,
        "ejector_limits": ejector_data
    }


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Ошибка: Файл {INPUT_FILE} не найден.")
        return
    print(f"Чтение файла: {INPUT_FILE}")
    try:
        wb = xlrd.open_workbook(INPUT_FILE)
        sheet = wb.sheet_by_index(SHEET_INDEX)
    except Exception as e:
        print(f"Ошибка: {e}");
        return

    # --- GEOMETRY ---
    val_j6 = get_cell_val_addr(sheet, 'J6')
    val_j7 = get_cell_val_addr(sheet, 'J7')
    main_len = (val_j6 * 1000) if isinstance(val_j6, (int, float)) else None
    builtin_len = (val_j7 * 1000) if isinstance(val_j7, (int, float)) else None
    pass_main = get_cell_val_addr(sheet, 'J8')
    pass_builtin = get_cell_val_addr(sheet, 'J9')

    geometry_data = {
        "condenser_id": None,
        "main_info": {"name_condenser": None, "project_id": None, "doc_num_thermo_calc": None, "doc_num_assembly": None,
                      "doc_num_passport": None},
        "geometry": {
            "diameter_internal": get_cell_val_addr(sheet, 'J16'),
            "wall_thickness": get_cell_val_addr(sheet, 'J17'),
            "material_id": None,
            "main_length": main_len,
            "main_count": get_cell_val_addr(sheet, 'J10'),
            "builtin_length": builtin_len,
            "builtin_count": get_cell_val_addr(sheet, 'J11'),
            "aircooler_count": None,
            "passes_main": pass_main,
            "passes_builtin": pass_builtin,
            "ejectors_count": 1
        },
        "limits": {
            "mass_flow_steam_nom": get_cell_val_addr(sheet, 'J13'),
            "mass_flow_air": get_cell_val_addr(sheet, 'J32')
        }
    }

    # --- MODE ---
    mode_data = {
        "coefficient_b": get_range_values(sheet, 31, 'A', 'J'),
        "Z_main": pass_main,
        "Z_builtin": pass_builtin,
        "Z_ejectors": 1,
        "W_main": get_range_values(sheet, 19, 'A', 'J'),
        "W_builtin": get_range_values(sheet, 21, 'A', 'J'),
        "t1_main": get_range_values(sheet, 23, 'A', 'J'),
        "t1_builtin": get_range_values(sheet, 25, 'A', 'J'),
        "G_steam": get_range_values(sheet, 27, 'A', 'J'),
        "H_steam": get_cell_val_addr(sheet, 'J12')
    }

    # --- RESULTS ---
    results_data = parse_results(sheet)

    # --- SAVE ---
    with open('geometry.json', 'w', encoding='utf-8') as f:
        json.dump(geometry_data, f, ensure_ascii=False, indent=2)
    with open('mode.json', 'w', encoding='utf-8') as f:
        json.dump(mode_data, f, ensure_ascii=False, indent=2)
    with open('results.json', 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)

    print("Все файлы успешно созданы.")


if __name__ == "__main__":
    main()
