"""Математика: Расчет протечек"""

import json
import os
from pathlib import Path


# настройки подключения специально для тестов из Windows
os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["POSTGRES_PORT"] = "5254"

from sqlalchemy import text

from app.adapters.calculation_adapter import CalculationAdapter
from app.schemas import CalculationGlobals, MultiCalculationParams, ValveGroupInput


class DummyValveInfo:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def calculate_wrapper(payload: dict):
    details = []
    summary = {
        "sk": {"total_g": 0.0, "mixed_h": 0.0},
        "rk": {"total_g": 0.0, "mixed_h": 0.0},
        "srk": {"total_g": 0.0, "mixed_h": 0.0},
    }
    globals_data = payload.get("globals", {})

    db = SessionLocal()
    try:
        for group in payload.get("groups", []):
            valve_id = group["valve_id"]

            query = text("SELECT * FROM autocalc.stocks WHERE id = :vid")
            result = db.execute(query, {"vid": valve_id}).mappings().first()

            if not result:
                raise ValueError(f"Клапан с id={valve_id} не найден в таблице autocalc.stocks!")

            raw_lengths = [
                result.get("len_part1"),
                result.get("len_part2"),
                result.get("len_part3"),
                result.get("len_part4"),
                result.get("len_part5"),
            ]
            valid_lengths = [float(L) for L in raw_lengths if L is not None and float(L) > 0]

            if len(valid_lengths) < 2:
                raise ValueError(
                    f"В БД у клапана id={valve_id} не заполнены длины участков! Значения: {raw_lengths}"
                )

            valve_info = DummyValveInfo(
                id=result["id"],
                name=result.get("name", "Unknown"),
                diameter=result.get("diameter", 0.0),
                clearance=result.get("clearance", 0.0),
                round_radius=result.get("round_radius", 2.0),
                section_lengths=valid_lengths,
            )

            p_ejector = group.get("p_leak_offs", [])
            if not p_ejector and "P_lst_leak_off" in globals_data:
                p_ejector.append(globals_data["P_lst_leak_off"])

            multi_params = MultiCalculationParams(
                turbine_id=1,
                globals=CalculationGlobals(
                    P_fresh=globals_data.get("P_fresh"),
                    P_fresh_unit=globals_data.get("P_fresh_unit", "кгс/см²"),
                    T_fresh=globals_data.get("T_fresh"),
                    T_fresh_unit=globals_data.get("T_fresh_unit", "°C"),
                    T_air=globals_data.get("T_air", 40),
                    T_air_unit=globals_data.get("T_air_unit", "°C"),
                    P_lst_leak_off=globals_data.get("P_lst_leak_off", 0.97),
                    P_lst_leak_off_unit=globals_data.get("P_lst_leak_off_unit", "кгс/см²"),
                ),
                groups=[
                    ValveGroupInput(
                        valve_id=valve_id,
                        type=group.get("type", "СК"),
                        valve_names=group.get("valve_names", []),
                        quantity=group["quantity"],
                        p_values=group["p_values"],
                        p_values_unit=group.get("p_values_unit", "кгс/см²"),
                        p_leak_offs=group.get("p_leak_offs", []),
                        p_leak_offs_unit=group.get("p_leak_offs_unit", "кгс/см²"),
                    )
                ],
            )
            calc_res = CalculationAdapter.run_multi_calculation(multi_params, valve_info)
            
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
                "group_total_g": group_total_g,
            }
            details.append(detail)

            v_type = detail["type"].lower()
            if v_type in summary:
                summary[v_type]["total_g"] += group_total_g
                if calc_res.Hi:
                    summary[v_type]["mixed_h"] = calc_res.Hi[0]

    finally:
        db.close()

    return {"details": details, "summary": summary}


target_function = calculate_wrapper

tests = []


def get_validation_dir():
    current = Path(__file__).resolve().parent
    for parent in [current, *list(current.parents)]:
        if (parent / "validation_data").exists():
            return parent / "validation_data" / "valve-stems"
    raise FileNotFoundError("Папка validation_data/valve-stems не найдена!")


data_dir = get_validation_dir()
file_prefixes = ["1_st_stock", "2_nd_stock", "3_rd_stock"]

for prefix in file_prefixes:
    data_file = data_dir / f"{prefix}_data.json"
    result_file = data_dir / f"{prefix}_result.json"

    if data_file.exists() and result_file.exists():
        with open(data_file, encoding="utf-8") as f_in:
            input_payload = json.load(f_in)
        with open(result_file, encoding="utf-8") as f_out:
            expected_result = json.load(f_out)

        tests.append(
            {
                "id": f"valve_calc_{prefix}",
                "input": {"payload": input_payload},
                "expected": expected_result,
            }
        )
