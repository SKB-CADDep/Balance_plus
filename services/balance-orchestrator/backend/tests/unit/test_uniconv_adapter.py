import pytest
from uniconv import UnknownUnitError
from app.core.uniconv_adapter import convert_input_data_units, TARGET_UNITS

def test_convert_simple_dict():
    """Проверка конвертации в плоском словаре"""
    data = {
        "p1": {"value": 10, "unit": "бар", "param_type": "pressure"}
    }
    result = convert_input_data_units(data)
    
    # 10 бар ≈ 10.197... кгс/см²
    assert result["p1"]["unit"] == TARGET_UNITS["pressure"]
    assert result["p1"]["value"] > 10.19
    assert result["p1"]["value"] < 10.20

def test_convert_nested_structure():
    """Проверка глубокой вложенности (списки внутри словарей)"""
    data = {
        "section_1": [
            {"temp": {"value": 300, "unit": "K", "param_type": "temperature"}},
            # Параметр без типа не должен ломать логику
            {"meta": "some info"} 
        ]
    }
    result = convert_input_data_units(data)
    
    converted_temp = result["section_1"][0]["temp"]
    assert converted_temp["unit"] == "°C"
    # 300K = 26.85°C
    assert round(converted_temp["value"], 2) == 26.85

def test_convert_unknown_unit_raises_error():
    """Проверка, что адаптер пробрасывает исключение UnknownUnitError"""
    data = {
        "bad_param": {"value": 5, "unit": "попугаи", "param_type": "pressure"}
    }
    
    with pytest.raises(UnknownUnitError):
        convert_input_data_units(data)

def test_ignore_unknown_param_types():
    """Если param_type не в списке TARGET_UNITS, данные не меняются"""
    data = {
        "other": {"value": 100, "unit": "мм", "param_type": "length"} # length нет в нашем target-списке
    }
    result = convert_input_data_units(data)
    # Данные должны остаться как есть
    assert result["other"]["unit"] == "мм"
    assert result["other"]["value"] == 100