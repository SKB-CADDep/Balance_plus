"""
Автономный консольный валидатор физического движка расчета конденсаторов.
Сверяет расчетные значения давлений с новыми эталонными JSON-сценариями.
"""

import os
import sys
import json
import math
from typing import List

# --- 1. Динамическое определение путей и добавление бэкенда в sys.path ---
def find_backend_root() -> str:
    """Находит корневую папку бэкенда (содержащую папку 'app') вверх по дереву"""
    current_dir = os.path.abspath(os.path.dirname(__file__))
    while True:
        if os.path.exists(os.path.join(current_dir, "app")) and os.path.exists(os.path.join(current_dir, "pyproject.toml")):
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            raise FileNotFoundError("Не удалось найти корневую папку бэкенда с модулем 'app'")
        current_dir = parent_dir

try:
    BACKEND_ROOT = find_backend_root()
    if BACKEND_ROOT not in sys.path:
        sys.path.append(BACKEND_ROOT)
        
    from app.utils.berman_strategy import BermanStrategy
    strategy_available = True
except Exception as e:
    strategy_available = False
    print(f"[WARNING] Не удалось импортировать BermanStrategy: {e}")

# --- 2. Новые верификационные сценарии ---
VALIDATION_SCENARIOS = [
    {
        "id": "К-3100-XIII (Сахалин)",
        "geometry": "geometry_k3100.json",
        "mode": "mode_k3100.json",
        "results": "results_k3100.json",
    },
    {
        "id": "КГ2-6200-III (Т-130/150-12.8)",
        "geometry": "geometry_kg2_6200.json",
        "mode": "mode_kg2_6200.json",
        "results": "results_kg2_6200.json",
    },
    {
        "id": "КГ2-7300-Iм (Владивосток)",
        "geometry": "geometry_kg2_7300.json",
        "mode": "mode_kg2_7300.json",
        "results": "results_kg2_7300.json",
    }
]

# --- 3. Интеллектуальный поиск и загрузка файлов ---
def locate_and_load_json(filename: str) -> dict:
    """Рекурсивно ищет файл по имени вверх и вниз по дереву директорий"""
    current_dir = os.path.abspath(os.path.dirname(__file__))
    search_dir = current_dir
    while True:
        candidate_val_data = os.path.join(search_dir, "validation_data")
        if os.path.exists(candidate_val_data):
            for root, _, files in os.walk(candidate_val_data):
                if filename in files:
                    with open(os.path.join(root, filename), "r", encoding="utf-8") as f:
                        return json.load(f)
        parent_dir = os.path.dirname(search_dir)
        if parent_dir == search_dir:
            break
        search_dir = parent_dir

    raise FileNotFoundError(f"Файл '{filename}' не найден в директориях проекта.")

# --- 4. Адаптивный маппер параметров (Синхронизирован с тест-файлом) ---
def berman_calculate_wrapper(geometry, mode):
    """
    Преобразует входящую JSON-структуру в точные параметры, которые ожидает 
    BermanStrategy, запускает расчет и преобразует результат в формат матрицы давлений.
    """
    strategy = BermanStrategy()
    
    geom_core = geometry.get("geometry", geometry)
    limits_core = geometry.get("limits", {})
    
    # 1. Точный маппинг всех скалярных и списочных параметров для BermanStrategy
    params = {
        "L_main": geom_core["main_length"],
        "L_builtin": geom_core.get("builtin_length", 0.0),
        "Z_main": int(geom_core["passes_main"]),
        "Z_builtin": int(geom_core.get("passes_builtin", 0)),
        "N_main": int(geom_core["main_count"]),
        "N_builtin": int(geom_core.get("builtin_count", 0)),
        
        "H_steam": mode["H_steam"],
        "G_nom": limits_core.get("mass_flow_steam_nom", 330.0),
        
        "d_in": geom_core["diameter_internal"],
        "S_tube": geom_core["wall_thickness"],
        
        "W_main_list": mode["W_main"],
        "W_builtin_list": mode.get("W_builtin", []),
        "t1_main_list": mode["t1_main"],
        "t1_builtin_list": mode.get("t1_builtin", []),
        "G_steam_list": mode["G_steam"],
        "coefficient_b_list": mode["coefficient_b"],
        "G_air": limits_core.get("mass_flow_air", 0.0)
    }
    
    # Расчет наружных диаметров и толщин
    params["delta"] = params["S_tube"]
    params["s"] = params["S_tube"]
    params["d_v"] = params["d_in"]
    params["d_vn"] = params["d_in"]
    params["d_out"] = params["d_in"] + 2.0 * params["delta"]
    params["d_nar"] = params["d_out"]
    
    # Определение теплопроводности lambda
    mat_id = geom_core.get("material_id", "").lower()
    if "lo70" in mat_id or "brass" in mat_id or "латунь" in mat_id:
        params["lambda"] = 90.0
    elif "mnzh5" in mat_id or "мнж5" in mat_id:
        params["lambda"] = 37.0
    elif "mnzhmts" in mat_id or "мнжмц" in mat_id:
        params["lambda"] = 32.0
    else:
        params["lambda"] = 90.0

    # 2. Выполнение расчета физическим движком
    raw_result = strategy.calculate(params)
    main_res = raw_result["main_results"]
    
    # 3. Обратное преобразование плоского массива в структурированные 2D-матрицы
    W_list = mode["W_main"]
    b_list = mode["coefficient_b"]
    t_list = mode["t1_main"]
    G_list = mode["G_steam"]
    
    condenser_modes = []
    flat_idx = 0
    
    for w_idx, w_val in enumerate(W_list):
        w_builtin_val = mode.get("W_builtin", [])[w_idx] if mode.get("W_builtin") else 0.0
        for b_val in b_list:
            pressures_axis = []
            for t_val in t_list:
                row_pressures = []
                for g_val in G_list:
                    if flat_idx < len(main_res):
                        pressure_atm = main_res[flat_idx]["P_steam_formula_atm"]
                        row_pressures.append(pressure_atm)
                        flat_idx += 1
                pressures_axis.append(row_pressures)
            
            condenser_modes.append({
                "W_main": w_val,
                "W_builtin": w_builtin_val,
                "coefficient_b": b_val,
                "table_data": [
                    {
                        "G_steam_axis": G_list,
                        "t1_main": t_list,
                        "pressures_axis": pressures_axis
                    }
                ]
            })
            
    return {"condenser_modes": condenser_modes}

# --- 5. Логика поузлового сравнения матриц ---
def compare_matrices(computed, expected, rel_tol=1e-5, abs_tol=1e-6) -> List[str]:
    errors = []
    for i in range(len(expected)):
        for j in range(len(expected[i])):
            comp_val = computed[i][j]
            exp_val = expected[i][j]
            if not math.isclose(comp_val, exp_val, rel_tol=rel_tol, abs_tol=abs_tol):
                errors.append(
                    f"Индекс [{i}][{j}]: расчёт={comp_val:.5f}, эталон={exp_val:.5f} (Δ={abs(comp_val - exp_val):.5f})"
                )
    return errors

# --- 6. Запуск процесса валидации ---
def run_validation():
    print("=" * 75)
    print("ЗАПУСК КОНСОЛЬНОЙ ВАЛИДАЦИИ ФИЗИЧЕСКОГО ДВИЖКА (НОВЫЙ БАЗИС)")
    print("=" * 75)
    
    if not strategy_available:
        print("[СБОЙ] Скрипт должен запускаться в виртуальном окружении Poetry.")
        return

    for scenario in VALIDATION_SCENARIOS:
        print(f"\n Scenarios {scenario['id']}:")
        try:
            geom = locate_and_load_json(scenario["geometry"])
            mode = locate_and_load_json(scenario["mode"])
            expected = locate_and_load_json(scenario["results"])
            
            print(f"  - Файлы верификации успешно загружены.")
            computed = berman_calculate_wrapper(geom, mode)
            
            failures = 0
            for exp_mode in expected["condenser_modes"]:
                w_main = exp_mode["W_main"]
                b_val = exp_mode["coefficient_b"]
                
                comp_mode = next(
                    (m for m in computed["condenser_modes"] 
                     if m["W_main"] == w_main and m["coefficient_b"] == b_val), None
                )
                
                if not comp_mode:
                    print(f"  - [ОШИБКА] Режим W={w_main} b={b_val} отсутствует в расчетах.")
                    failures += 1
                    continue
                
                comp_matrix = comp_mode["table_data"][0]["pressures_axis"]
                exp_matrix = exp_mode["table_data"][0]["pressures_axis"]
                
                errors = compare_matrices(comp_matrix, exp_matrix)
                if errors:
                    print(f"  - [РАСХОЖДЕНИЕ] Режим W={w_main} b={b_val}: обнаружено {len(errors)} расхождений:")
                    for err in errors[:3]:
                        print(f"    * {err}")
                    if len(errors) > 3:
                        print(f"    * ... и еще {len(errors)-3} расхождений.")
                    failures += len(errors)
                else:
                    print(f"  - [ОК] Режим W={w_main} b={b_val} совпадает с эталоном.")
            
            if failures == 0:
                print(f"  - [УСПЕХ] Конденсатор {scenario['id']} полностью верифицирован!")
            else:
                print(f"  - [FAIL] Найдено {failures} несовпадений с эталоном.")
                
        except Exception as ex:
            print(f"  - [СБОЙ] Ошибка выполнения сценария: {ex}")

if __name__ == "__main__":
    run_validation()