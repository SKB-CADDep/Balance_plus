"""
Валидация математики: Расчет конденсатора по Берману по эталонным сценариям
"""

import os
import json
from app.utils.berman_strategy import BermanStrategy

def berman_calculate_wrapper(geometry, mode):
    """
    Преобразует входящую JSON-структуру в точные параметры, которые ожидает 
    BermanStrategy, запускает расчет и преобразует результат в формат матрицы давлений.
    """
    strategy = BermanStrategy()
    
    geom_core = geometry.get("geometry", geometry)
    limits_core = geometry.get("limits", {})
    
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
    
    mat_id = geom_core.get("material_id", "").lower()
    if "lo70" in mat_id or "brass" in mat_id or "латунь" in mat_id:
        params["lambda"] = 90.0
    elif "mnzh5" in mat_id or "мнж5" in mat_id:
        params["lambda"] = 37.0
    elif "mnzhmts" in mat_id or "мнжмц" in mat_id:
        params["lambda"] = 32.0
    else:
        params["lambda"] = 90.0

    raw_result = strategy.calculate(params)
    main_res = raw_result["main_results"]
    
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

target_function = berman_calculate_wrapper


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

    raise FileNotFoundError(
        f"Критическая ошибка: Файл '{filename}' не найден в директориях проекта."
    )


geom_k3100 = locate_and_load_json("geometry_k3100.json")
mode_k3100 = locate_and_load_json("mode_k3100.json")
res_k3100 = locate_and_load_json("results_k3100.json")

geom_kg2_6200 = locate_and_load_json("geometry_kg2_6200.json")
mode_kg2_6200 = locate_and_load_json("mode_kg2_6200.json")
res_kg2_6200 = locate_and_load_json("results_kg2_6200.json")

geom_kg2_7300 = locate_and_load_json("geometry_kg2_7300.json")
mode_kg2_7300 = locate_and_load_json("mode_kg2_7300.json")
res_kg2_7300 = locate_and_load_json("results_kg2_7300.json")


tests = [
    {
        "id": "berman_k3100",
        "input": {"geometry": geom_k3100, "mode": mode_k3100},
        "expected": res_k3100
    },
    {
        "id": "berman_kg2_6200",
        "input": {"geometry": geom_kg2_6200, "mode": mode_kg2_6200},
        "expected": res_kg2_6200
    },
    {
        "id": "berman_kg2_7300",
        "input": {"geometry": geom_kg2_7300, "mode": mode_kg2_7300},
        "expected": res_kg2_7300
    }
]