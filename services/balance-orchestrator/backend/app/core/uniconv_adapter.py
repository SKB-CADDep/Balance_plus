from typing import Any
from uniconv import UnitConverter

uc = UnitConverter()

TARGET_UNITS = {
    "pressure": "кгс/см²",         # P - давление
    "temperature": "°C",           # T - температура (используем латинскую C для стандарта)
    "enthalpy": "ккал/кг",         # H - энтальпия
    "entropy": "ккал/кгК",         # S - энтропия
    "specific_volume": "м³/кг",    # v - удельный объем
    "density": "кг/м³",            # ρ - плотность
    "power": "МВт",                # N - мощность
    "mass_flow": "т/ч",            # G - расход
    "heat_power": "Гкал/ч",        # Q - тепло (в uniconv называется heat_power)
    "quality": "%"                 # X, Y - степень сухости/влажности
}

def convert_input_data_units(data: Any) -> Any:
    """
    Рекурсивно обходит структуру данных и ищет объекты параметров.
    Ожидаемый формат объекта от фронтенда:
    {"value": 10, "unit": "бар", "param_type": "pressure"}
    """
    if isinstance(data, dict):
        if "value" in data and "unit" in data and "param_type" in data:
            p_type = data["param_type"]
            current_unit = data["unit"]
            current_val = data["value"]
            
            if p_type in TARGET_UNITS:
                target = TARGET_UNITS[p_type]
                if current_unit and current_unit != target:
                    new_val = uc.convert(
                        current_val,
                        from_unit=current_unit,
                        to_unit=target,
                        parameter_type=p_type
                    )
                    data["value"] = round(new_val, 6) # округляем для красоты JSON
                    data["unit"] = target
        
        for key, val in data.items():
            data[key] = convert_input_data_units(val)
            
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = convert_input_data_units(data[i])
            
    return data