"""Математика: Расчет протечек штоков клапанов (Интеграция с Адаптером)"""

import json
from pathlib import Path

from app.adapters.calculation_adapter import CalculationAdapter
from app.schemas import CalculationParams, ValveInfo

# =====================================================================
# 1. ИМИТАЦИЯ БАЗЫ ДАННЫХ (MOCK DB)
# =====================================================================
MOCK_VALVES_DB = {
    # 1-й шток
    9: ValveInfo(
        id=9,
        name="БТ-252380",
        diameter=50.0,
        clearance=0.15,
        round_radius=2.0,
        section_lengths=[150.0, 120.0, 80.0]  # <--- ПРОВЕРЬ: тут должно быть минимум 2 числа!
    ),
    # 2-й шток
    17: ValveInfo(
        id=17,
        name="Второй клапан",  # Подставь реальное имя
        diameter=60.0,         # Подставь реальные цифры из БД
        clearance=0.2,
        round_radius=2.0,
        section_lengths=[100.0, 100.0] # <--- Минимум 2 числа
    ),
    # 3-й шток
    11: ValveInfo(
        id=11,
        name="Третий клапан",  # Подставь реальное имя
        diameter=40.0,         # Подставь реальные цифры из БД
        clearance=0.1,
        round_radius=2.0,
        section_lengths=[80.0, 90.0, 50.0] # <--- Минимум 2 числа
    )
}


# =====================================================================
# 2. ФУНКЦИЯ-ОБЕРТКА (Эмулирует работу твоего Router'а)
# =====================================================================
def calculate_wrapper(payload: dict):
    details =[]
    summary = {
        "sk": {"total_g": 0.0, "mixed_h": 0.0},
        "rk": {"total_g": 0.0, "mixed_h": 0.0},
        "srk": {"total_g": 0.0, "mixed_h": 0.0}
    }

    globals_data = payload.get("globals", {})
    
    for group in payload.get("groups",[]):
        valve_id = group["valve_id"]
        
        if valve_id not in MOCK_VALVES_DB:
            raise ValueError(f"Добавь геометрию для клапана id={valve_id} в MOCK_VALVES_DB!")
            
        valve_info = MOCK_VALVES_DB[valve_id]
        
        p_ejector =[]
        if "P_lst_leak_off" in globals_data:
            p_ejector.append(globals_data["P_lst_leak_off"])
            
        params = CalculationParams(
            count_valves=group["quantity"],
            p_values=group["p_values"],
            p_values_unit=group.get("p_values_unit", "кгс/см²"),
            p_ejector=p_ejector,
            p_ejector_unit=globals_data.get("P_lst_leak_off_unit", "кгс/см²"),
            t_air=globals_data.get("T_air", 40),
            t_air_unit=globals_data.get("T_air_unit", "°C"),
            temperature_start=globals_data.get("T_fresh"),
            temperature_start_unit=globals_data.get("T_fresh_unit", "°C"),
            enthalpy_start=globals_data.get("H_fresh"),
            enthalpy_start_unit=globals_data.get("H_fresh_unit", "кДж/кг")
        )

        calc_res = CalculationAdapter.run_calculation(params, valve_info)
        
        group_total_g = sum(calc_res.Gi) * group["quantity"]

        detail = {
            "valve_id": valve_id,
            "type": group.get("type", "СК"),
            "valve_names": group.get("valve_names", []),
            "quantity": group["quantity"],
            "Gi": calc_res.Gi,
            "Pi_in": calc_res.Pi_in,
            "Ti": calc_res.Ti,
            "Hi": calc_res.Hi,
            "deaerator_props": calc_res.deaerator_props,
            "ejector_props": calc_res.ejector_props,
            "group_total_g": group_total_g
        }
        details.append(detail)
        
        v_type = detail["type"].lower()
        if v_type in summary:
            summary[v_type]["total_g"] += group_total_g
            if calc_res.Hi:
                summary[v_type]["mixed_h"] = calc_res.Hi[0]

    return {
        "details": details,
        "summary": summary
    }


target_function = calculate_wrapper

# =====================================================================
# 3. ДИНАМИЧЕСКИЙ СБОР ТЕСТОВ ИЗ ПАПКИ VALIDATION_DATA
# =====================================================================
tests =[]

def get_validation_dir():
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "validation_data").exists():
            return parent / "validation_data" / "valve-stems"
    raise FileNotFoundError("Папка validation_data/valve-stems не найдена!")

data_dir = get_validation_dir()

file_prefixes =["1_st_stock", "2_nd_stock", "3_rd_stock", "group_of_stocks"]

for prefix in file_prefixes:
    data_file = data_dir / f"{prefix}_data.json"
    result_file = data_dir / f"{prefix}_result.json"
    
    if data_file.exists() and result_file.exists():
        with open(data_file, "r", encoding="utf-8") as f_in:
            input_payload = json.load(f_in)
            
        with open(result_file, "r", encoding="utf-8") as f_out:
            expected_result = json.load(f_out)
            
        tests.append({
            "id": f"valve_calc_{prefix}",
            "input": {"payload": input_payload},
            "expected": expected_result
        })