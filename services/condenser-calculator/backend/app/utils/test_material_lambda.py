"""
Тестирование бизнес-логики расчета теплопроводности (λ) материалов с мокированием Table1D
"""
import pytest
import numpy as np
from unittest.mock import patch
from app.core.material_lambda import build_lambda_interpolator, get_lambda
from app.core.exceptions import MaterialPropertyError

# --- Вспомогательные классы для тестов ---
class MockPoint:
    def __init__(self, temperature, value):
        self.temperature = temperature
        self.value = value

class MockMaterial:
    def __init__(self, name, points):
        self.name = name
        self.thermal_conductivity_points = points

class FakeTable1D:
    def __init__(self, x, y):
        idx = np.argsort(x)
        self.x = x[idx]
        self.y = y[idx]

    def __call__(self, val):
        return np.interp(val, self.x, self.y)

# --- Фикстуры ---
@pytest.fixture
def valid_material():
    return MockMaterial("МНЖ 5-1", [
        MockPoint(20.0, 15.0),
        MockPoint(100.0, 35.0),
        MockPoint(150.0, 45.0)
    ])

@pytest.fixture
def unordered_material():
    return MockMaterial("Латунь Л68", [
        MockPoint(100.0, 35.0),
        MockPoint(20.0, 15.0),
        MockPoint(150.0, 45.0)
    ])


# --- Тестовые сценарии ---

@patch("app.core.material_lambda.Table1D", side_effect=FakeTable1D)
def test_get_lambda_exact_point(mock_table, valid_material):
    interp = build_lambda_interpolator(valid_material)
    assert get_lambda(interp, 100.0) == 35.0

@patch("app.core.material_lambda.Table1D", side_effect=FakeTable1D)
def test_get_lambda_interpolation(mock_table, valid_material):
    interp = build_lambda_interpolator(valid_material)
    assert get_lambda(interp, 60.0) == 25.0

@patch("app.core.material_lambda.Table1D", side_effect=FakeTable1D)
def test_get_lambda_unordered_points(mock_table, unordered_material):
    interp = build_lambda_interpolator(unordered_material)
    assert get_lambda(interp, 60.0) == 25.0

def test_get_lambda_empty_points():
    material = MockMaterial("Unknown", [])
    with pytest.raises(MaterialPropertyError, match="требуется минимум 2 точки"):
        build_lambda_interpolator(material)

def test_get_lambda_single_point():
    material = MockMaterial("Titanium", [MockPoint(50.0, 20.0)])
    with pytest.raises(MaterialPropertyError, match="требуется минимум 2 точки"):
        build_lambda_interpolator(material)

@patch("app.core.material_lambda.Table1D", side_effect=FakeTable1D)
def test_get_lambda_below_range(mock_table, valid_material):
    interp = build_lambda_interpolator(valid_material)
    with pytest.raises(MaterialPropertyError, match=r"вне диапазона таблицы.*\[20.0; 150.0\]"):
        get_lambda(interp, 10.0)

@patch("app.core.material_lambda.Table1D", side_effect=FakeTable1D)
def test_get_lambda_above_range(mock_table, valid_material):
    interp = build_lambda_interpolator(valid_material)
    with pytest.raises(MaterialPropertyError, match=r"вне диапазона таблицы.*\[20.0; 150.0\]"):
        get_lambda(interp, 200.0)

@patch("app.core.material_lambda.Table1D", side_effect=FakeTable1D)
def test_lambda_list_format(mock_table):
    """Тест обработки формата JSON: списка списков [[t, λ], ...]"""
    material = MockMaterial("TestList", [[20, 10], [100, 30]])
    interp = build_lambda_interpolator(material)
    
    assert interp.min_t == 20.0
    assert interp.max_t == 100.0
    
    result = get_lambda(interp, 60.0)
    assert result == 20.0

@patch("app.core.material_lambda.Table1D", side_effect=FakeTable1D)
def test_lambda_dict_format(mock_table):
    """Тест обработки формата JSON: словари (когда material - тоже словарь)"""
    material_dict = {
        "name": "TestDict",
        "thermal_conductivity_points": [
            {"temperature": 20, "value": 10},
            {"temperature": 100, "value": 30}
        ]
    }
    interp = build_lambda_interpolator(material_dict)
    assert get_lambda(interp, 60.0) == 20.0