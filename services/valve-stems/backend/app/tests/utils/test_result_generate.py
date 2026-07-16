"""Перегенерация эталонных result.json после фикса P_air в адаптере."""

import json
from pathlib import Path

from app.tests.utils.test_valve_stems_calc import calculate_wrapper, get_validation_dir

data_dir = get_validation_dir()
file_prefixes = ["1_st_stock", "2_nd_stock", "3_rd_stock"]

for prefix in file_prefixes:
    data_file = data_dir / f"{prefix}_data.json"
    result_file = data_dir / f"{prefix}_result.json"

    if not data_file.exists():
        print(f"[SKIP] {data_file} не найден")
        continue

    with open(data_file, "r", encoding="utf-8") as f_in:
        payload = json.load(f_in)

    new_result = calculate_wrapper(payload)

    with open(result_file, "w", encoding="utf-8") as f_out:
        json.dump(new_result, f_out, ensure_ascii=False, indent=2)

    print(f"[OK] Обновлён {result_file}")

print("Готово. Не забудь свериться с эталонными PDF перед коммитом!")