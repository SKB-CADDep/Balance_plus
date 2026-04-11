"""
Тестирование бизнес-логики расчета теплопроводности (λ) материалов с мокированием Table1D
"""
import pytest
import numpy as np
from unittest.mock import patch
from app.core.material_lambda import build_lambda_interpolator, get_lambda

# --- Вспомогательные классы для тестов ---
class MockPoint:
    def __init__(self, temperature, value):
        self.temperature = temperature
        self.value = value

class MockMaterial:
    def __init__(self, name, points):
        self.name = name
        self.thermal_conductivity_points = points

# Фейковый Table1D для имитации корректной интерполяции без вызова реального движка
class FakeTable1D:
    def __init__(self, x, y):
        # Table1D умеет сортировать точки
        idx = np.argsort(x)
        self.x = x[idx]
        self.y = y[idx]

    def __call__(self, val):
        return np.interp(val, self.x, self.y)


# --- Фикстуры (тестовые данные) ---
@pytest.fixture
def valid_material():
    points = [
        MockPoint(20.0, 15.0),
        MockPoint(100.0, 35.0),
        MockPoint(150.0, 45.0)
    ]
    return MockMaterial("МНЖ 5-1", points)

@pytest.fixture
def unordered_material():
    points = [
        MockPoint(100.0, 35.0),
        MockPoint(20.0, 15.0),
        MockPoint(150.0, 45.0)
    ]
    return MockMaterial("Латунь Л68", points)

@pytest.fixture
def empty_material():
    return MockMaterial("Unknown", [])

@pytest.fixture
def single_point_material():
    return MockMaterial("Titanium", [MockPoint(50.0, 20.0)])


# --- Тестовые сценарии (Test cases) ---

@patch("app.core.material_lambda.Table1D", side_effect=FakeTable1D)
def test_get_lambda_exact_point(mock_table, valid_material):
    """Проверка возврата точного значения, если температура совпадает с узловой точкой"""
    result = get_lambda(valid_material, 100.0)
    assert result == 35.0

@patch("app.core.material_lambda.Table1D", side_effect=FakeTable1D)
def test_get_lambda_interpolation(mock_table, valid_material):
    """Проверка корректной интерполяции между двумя известными точками"""
    result = get_lambda(valid_material, 60.0)
    assert result == 25.0

@patch("app.core.material_lambda.Table1D", side_effect=FakeTable1D)
def test_get_lambda_unordered_points(mock_table, unordered_material):
    """Проверка, что функция корректно справляется с неотсортированными точками"""
    result = get_lambda(unordered_material, 60.0)
    assert result == 25.0

def test_get_lambda_empty_points(empty_material):
    """Проверка генерации ошибки при пустом массиве точек теплопроводности"""
    with pytest.raises(ValueError, match="Недостаточно данных теплопроводности"):
        get_lambda(empty_material, 50.0)

def test_get_lambda_single_point(single_point_material):
    """Проверка генерации ошибки, если у материала всего 1 точка теплопроводности"""
    with pytest.raises(ValueError, match="Недостаточно данных теплопроводности"):
        get_lambda(single_point_material, 50.0)

def test_get_lambda_below_range(valid_material):
    """Запрет экстраполяции: температура ниже доступного диапазона"""
    with pytest.raises(ValueError, match=r"вне диапазона таблицы.*\[20.0; 150.0\]"):
        get_lambda(valid_material, 10.0)

def test_get_lambda_above_range(valid_material):
    """Запрет экстраполяции: температура выше доступного диапазона"""
    with pytest.raises(ValueError, match=r"вне диапазона таблицы.*\[20.0; 150.0\]"):
        get_lambda(valid_material, 200.0)

@patch("app.core.material_lambda.Table1D", side_effect=FakeTable1D)
def test_build_lambda_interpolator_returns_table1d(mock_table, valid_material):
    """Проверка, что в конструктор Table1D передаются правильные массивы numpy.ndarray"""
    build_lambda_interpolator(valid_material)
    
    assert mock_table.called
    args, _ = mock_table.call_args
    x_arr, y_arr = args
    
    assert isinstance(x_arr, np.ndarray)
    assert isinstance(y_arr, np.ndarray)
    assert list(x_arr) == [20.0, 100.0, 150.0]
    assert list(y_arr) == [15.0, 35.0, 45.0]