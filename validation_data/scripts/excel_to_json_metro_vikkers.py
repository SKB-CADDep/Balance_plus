import xlrd
import json
import os
import re

# НАСТРОЙКИ
INPUT_FILE = 'geometry.xls'
SHEET_INDEX = 0

# Координаты колонок (0-based)
# W - это 22-я колонка (A=0 ... W=22)
COL_HEADER = 22  # Столбец W (Заголовки "в=...", "t=...")
COL_DATA_START = 23  # Столбец X (Начало данных)


def clean_text(text):
    """
    Нормализация текста.
    Важно: заменяем русскую 'в' на английскую 'b', чтобы найти 'b=' (coefficient_b).
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
    """Извлекает числа из строки."""
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
    print("--- НАЧАЛО ОБРАБОТКИ РЕЗУЛЬТАТОВ (Колонки W-AF) ---")
    condenser_modes = []

    current_table_obj = None
    current_g_steam_indices = []

    r = 0
    while r < sheet.nrows:
        try:
            # Читаем ячейку в столбце W (22)
            raw_w = sheet.cell_value(r, COL_HEADER)
            val_w = clean_text(raw_w)

            # --- 1. ЗАГОЛОВОК БЛОКА ---
            # Строка вида: "в= 1, Z= 2; материал трубок - титан; W= 15000"
            # После clean_text превратится в "b=1,z=2...w=15000"
            if 'b=' in val_w and 'w=' in val_w:
                nums = extract_floats(raw_w)

                # Обычно nums = [1.0, 2.0, 15000.0] (B, Z, W)
                if len(nums) >= 2:
                    # B - обычно первое число
                    b_val = nums[0]
                    # W - обычно последнее число
                    w_val = nums[-1]

                    print(f"DEBUG: Найдена шапка в строке {r + 1}: W={w_val}, B={b_val}")

                    current_table_obj = {
                        "G_steam_axis": [],
                        "t1_main": [],
                        "pressures_axis": []
                    }

                    block = {
                        "W_main": w_val,
                        "W_builtin": None,
                        "coefficient_b": b_val,
                        "table_data": [current_table_obj]
                    }

                    condenser_modes.append(block)
                    current_g_steam_indices = []

                    # Читаем ось G_steam из следующей строки (r+1), начиная с колонки X (23)
                    header_row = r + 1
                    if header_row < sheet.nrows:
                        col = COL_DATA_START
                        while col < sheet.ncols:
                            val = sheet.cell_value(header_row, col)
                            if isinstance(val, (int, float)):
                                current_table_obj["G_steam_axis"].append(val)
                                current_g_steam_indices.append(col)
                            # Если пусто или текст - останавливаем чтение оси
                            elif str(val).strip() == '' and len(current_table_obj["G_steam_axis"]) > 0:
                                break
                            elif str(val).strip() != '' and not isinstance(val, (int, float)):
                                break
                            col += 1

                    r += 2  # Пропускаем строку заголовка и строку оси
                    continue

            # --- 2. ДАННЫЕ (t=...) ---
            # Строка вида "t= 45"
            if 't=' in val_w and current_table_obj is not None:
                # Разбиваем по '=', чтобы не схватить лишнее
                parts = str(raw_w).split('=')
                if len(parts) > 1:
                    t_nums = extract_floats(parts[1])
                    if t_nums:
                        t1_val = t_nums[0]
                        current_table_obj["t1_main"].append(t1_val)

                        # Читаем давления из тех колонок, где нашли ось
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

    return {
        "condenser_modes": condenser_modes
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
    val_j33 = get_cell_val_addr(sheet, 'J33')  # Dia
    val_j34 = get_cell_val_addr(sheet, 'J34')  # Wall
    val_j35 = get_cell_val_addr(sheet, 'J35')  # Length

    diam_int = (val_j33 * 1000) if isinstance(val_j33, (int, float)) else None
    wall_th = (val_j34 * 1000) if isinstance(val_j34, (int, float)) else None
    main_len = (val_j35 * 1000) if isinstance(val_j35, (int, float)) else None

    val_passes_main = get_cell_val_addr(sheet, 'J30')

    geometry_data = {
        "condenser_id": None,
        "main_info": {
            "name_condenser": None, "project_id": None,
            "doc_num_thermo_calc": None, "doc_num_assembly": None, "doc_num_passport": None
        },
        "geometry": {
            "diameter_internal": diam_int,
            "wall_thickness": wall_th,
            "material_id": None,
            "main_length": main_len,
            "main_count": get_cell_val_addr(sheet, 'J31'),
            "builtin_length": None,
            "builtin_count": None,
            "aircooler_count": get_cell_val_addr(sheet, 'J32'),
            "passes_main": val_passes_main,
            "passes_builtin": None,
            "ejectors_count": 1
        },
        "limits": {
            "mass_flow_steam_nom": None,
            "mass_flow_air": None
        }
    }

    # --- MODE ---
    mode_data = {
        "coefficient_b": get_range_values(sheet, 28, 'A', 'J'),
        "Z_main": val_passes_main,
        "Z_builtin": None,
        "Z_ejectors": 1,
        "W_main": get_range_values(sheet, 22, 'A', 'J'),
        "W_builtin": None,
        "t1_main": get_range_values(sheet, 25, 'A', 'J'),
        "t1_builtin": None,
        "G_steam": get_range_values(sheet, 23, 'A', 'J'),
        "H_steam": None,
        "X_steam": get_cell_val_addr(sheet, 'J39')
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

    print("Все файлы успешно созданы (версия W-AF).")


if __name__ == "__main__":
    main()
