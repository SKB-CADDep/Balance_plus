from dbfread import DBF
import os
import json
import datetime
import decimal
from collections import defaultdict


def default_serializer(obj):
    """Кастомный сериализатор для JSON (даты + Decimal)."""
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def load_dbf_data():
    """Загружает связанные DBF-файлы и сохраняет результат в JSON."""
    dbf_folder = r"C:/Data_BALANCE"

    # --- НАСТРОЙКИ ТИПОВ КРИВЫХ ---

    # Тип 1: Явные 3D кривые (по NAMU)
    # C, P, K (лат) и С, К, Р (кир)
    CURVE_3D_TYPES = ['C', 'P', 'K', 'С', 'К', 'Р']

    # Тип 2: Общая ось X (Shared X)
    # U (лат)
    CURVE_SHARED_X_TYPES = ['U']

    # --- Проверяем папку и наличие нужных файлов ----------------------------
    if not os.path.exists(dbf_folder):
        raise FileNotFoundError(f"Папка {dbf_folder} не найдена")

    required_files = ['TEPO.DBF', 'TEPP.DBF', 'TEPR.DBF',
                      'TEPS.DBF', 'TEPT.DBF', 'TEPW.DBF']
    for file in required_files:
        if not os.path.exists(os.path.join(dbf_folder, file)):
            raise FileNotFoundError(f"Не найден файл {file}")

    # --- Загружаем TEPO (список объектов) -----------------------------------
    try:
        tepo_table = DBF(os.path.join(dbf_folder, 'TEPO.DBF'), encoding='cp866')
    except UnicodeDecodeError:
        tepo_table = DBF(os.path.join(dbf_folder, 'TEPO.DBF'), encoding='cp1251')

    object_names = [rec['NAME'] for rec in tepo_table if 'NAME' in rec]
    if not object_names:
        raise ValueError("В таблице TEPO не найдены объекты")

    print("Доступные объекты:")
    for i, n in enumerate(object_names, 1):
        print(f"{i}. {n}")

    while True:
        try:
            idx = int(input("Выберите номер объекта: ")) - 1
            if 0 <= idx < len(object_names):
                selected_object = object_names[idx]
                break
            print("Некорректный номер")
        except ValueError:
            print("Введите число")

    # --- Ищем запись в TEPO и связанные имена ------------------------------
    selected_record = None
    related_names = {}
    for rec in tepo_table:
        if rec.get('NAME') == selected_object:
            selected_record = dict(rec)
            related_names = {'TEPP': rec.get('NAMEP', ''),
                             'TEPR': rec.get('NAMER', ''),
                             'TEPW': rec.get('NAMEW', ''),
                             'TEPS': rec.get('NAMES', '')}
            break

    if not selected_record:
        raise ValueError(f"Объект '{selected_object}' не найден")

    # --- Результирующий словарь --------------------------------------------
    result = {
        selected_object: {
            "TEPO": selected_record,
            "TEPP": [], "TEPR": [], "TEPS": [], "TEPW": [], "TEPT": []
        }
    }

    # --- Загружаем остальные таблицы ---------------------------------------
    tables, tpt_field_names = {}, []
    for tbl in ['TEPP', 'TEPR', 'TEPS', 'TEPT', 'TEPW']:
        path = os.path.join(dbf_folder, f"{tbl}.DBF")
        try:
            try:
                dbf = DBF(path, encoding='cp866')
            except UnicodeDecodeError:
                dbf = DBF(path, encoding='cp1251')
            tables[tbl] = list(dbf)

            if tbl == 'TEPT':
                # Все поля, кроме NAME и NAMU
                tpt_field_names = [f.name for f in dbf.fields
                                   if f.name not in ('NAME', 'NAMU')]

        except Exception as e:
            print(f"Ошибка загрузки {tbl}: {e}")
            tables[tbl] = []

    # --- Заполняем связанные списки (TEPP, TEPR, …) -------------------------
    for tbl in ['TEPP', 'TEPR', 'TEPS', 'TEPW']:
        key = related_names.get(tbl)
        if key:
            result[selected_object][tbl] = [dict(r) for r in tables[tbl]
                                            if r.get('NAME') == key]

    # --- Собираем имена для поиска в TEPT, разделяя источники --------------
    tepp_target_names = set()
    tepw_target_names = set()

    # 1. Из TEPP
    if related_names['TEPP']:
        tepp_records = [r for r in tables['TEPP']
                        if r.get('NAME') == related_names['TEPP']]
        for r in tepp_records:
            nt = r.get('NAMET')
            nd = r.get('NAMED')
            if nt and str(nt).strip(): tepp_target_names.add(nt)
            if nd and str(nd).strip(): tepp_target_names.add(nd)

    # 2. Из TEPW (Эти всегда считаем 3D)
    if related_names['TEPW']:
        tepw_records = [r for r in tables['TEPW']
                        if r.get('NAME') == related_names['TEPW']]
        for r in tepw_records:
            nm = r.get('NAME')
            nt = r.get('NAMET')  # На всякий случай
            if nm and str(nm).strip(): tepw_target_names.add(nm)
            if nt and str(nt).strip(): tepw_target_names.add(nt)

    # Объединяем для общей фильтрации при загрузке
    all_target_names = tepp_target_names | tepw_target_names

    # --- Формируем TEPT -----------------------------------------------------
    if all_target_names:
        # 1. Группируем записи TEPT по NAME
        grouped_tept = defaultdict(list)
        for rec in tables['TEPT']:
            rec_name = rec.get('NAME')
            # Фильтруем пустые и ненужные
            if rec_name and str(rec_name).strip() and rec_name in all_target_names:
                grouped_tept[rec_name].append(rec)

        tpt_out = []

        # 2. Обрабатываем группы
        for name, records in grouped_tept.items():
            if not records:
                continue

            # Определяем тип.
            # ПРИОРИТЕТ 1: Если имя из TEPW - это 3D кривая (X, Y, Z), даже если NAMU пустое
            is_from_tepw = name in tepw_target_names

            first_namu = records[0].get('NAMU', '').strip()

            if is_from_tepw or first_namu in CURVE_3D_TYPES:
                # === 3D КРИВЫЕ (Из TEPW или по NAMU C, P, K) ===
                # Структура: строка 1=X, строка 2=Y, остальные=Z

                matrix_values = []
                for r in records:
                    raw_vals = [r.get(f) for f in tpt_field_names]
                    clean_vals = [v for v in raw_vals if v is not None and v != 0]
                    matrix_values.append(clean_vals)

                x_vals = matrix_values[0] if len(matrix_values) > 0 else []
                y_vals = matrix_values[1] if len(matrix_values) > 1 else []
                z_vals = matrix_values[2:] if len(matrix_values) > 2 else []

                tpt_out.append({
                    "NAME": name,
                    "X": x_vals,
                    "Y": y_vals,
                    "Z": z_vals
                })

            elif first_namu in CURVE_SHARED_X_TYPES:
                # === Shared X (U) ===
                raw_x = [records[0].get(f) for f in tpt_field_names]
                x_vals = [v for v in raw_x if v is not None and v != 0]

                for y_row in records[1:]:
                    raw_y = [y_row.get(f) for f in tpt_field_names]
                    y_vals = [v for v in raw_y if v is not None and v != 0]

                    y_namu = y_row.get('NAMU', '').strip()
                    if y_namu:
                        tpt_out.append({
                            "NAME": y_namu,
                            "X": x_vals,
                            "Y": y_vals
                        })

            else:
                # === 2D КРИВЫЕ (Все остальные из TEPP) ===
                # Универсальная обработка 2 или 4 строки

                matrix_values = []
                for r in records:
                    raw_vals = [r.get(f) for f in tpt_field_names]
                    clean_vals = [v for v in raw_vals if v is not None and v != 0]
                    matrix_values.append(clean_vals)

                rows_count = len(matrix_values)

                if rows_count == 2:
                    tpt_out.append({
                        "NAME": name,
                        "X": matrix_values[0],
                        "Y": matrix_values[1]
                    })

                elif rows_count == 4:
                    x_part1 = matrix_values[0]
                    y_part1 = matrix_values[1]
                    x_part2 = matrix_values[2]
                    y_part2 = matrix_values[3]

                    full_x = x_part1 + x_part2[1:]
                    full_y = y_part1 + y_part2[1:]

                    tpt_out.append({
                        "NAME": name,
                        "X": full_x,
                        "Y": full_y
                    })

                else:
                    # Fallback для странных случаев (не 2 и не 4 строки, и не 3D)
                    for r in records:
                        current_name = r.get('NAME', '').strip()
                        if current_name:
                            raw_vals = [r.get(f) for f in tpt_field_names]
                            tab_vals = [v for v in raw_vals if v is not None and v != 0]
                            tpt_out.append({
                                "NAME": current_name,
                                "NAMU": r.get('NAMU', ''),
                                "tab": tab_vals
                            })

        result[selected_object]['TEPT'] = tpt_out

    # --- Сохраняем JSON -----------------------------------------------------
    json_path = os.path.join(dbf_folder, f"{selected_object}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=default_serializer)

    print(f"\nРезультат сохранён в: {json_path}")
    return result


if __name__ == "__main__":
    try:
        load_dbf_data()
    except Exception as err:
        import traceback

        traceback.print_exc()
        print(f"Ошибка: {err}")
