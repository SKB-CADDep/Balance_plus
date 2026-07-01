import numpy as np
import pytest
from app.utils.TPS_module import TablePressureStrategy
from scipy.interpolate import RectBivariateSpline, interp1d


# =============================================================================
# ТЕСТЫ МЕТОДОВ ВНУТРЕННЕГО ИНТЕРФЕЙСА (_create_namet_interpolator, _create_named_interpolator)
# =============================================================================


def test_create_namet_interpolator_low_temp():
    """Создание NAMET интерполятора (убывающая температура в массиве)"""
    namet_data = [
        [35, 30, 25],
        [20, 50, 100],
        [[6.5, 8.8, 10.9], [5.0, 6.8, 8.5], [3.8, 5.2, 6.7]]
    ]
    s = TablePressureStrategy()
    interp = s._create_namet_interpolator(namet_data)
    assert isinstance(interp, RectBivariateSpline)
    
    # Проверка интерполяции внутри таблицы
    result_30_50 = interp(30, 50)
    assert isinstance(result_30_50, np.ndarray)
    assert result_30_50.shape == (1, 1)
    assert result_30_50[0][0] == pytest.approx(6.8, rel=0.01)
    
    # Экстраполяция: при t=35, G=20 (угол таблицы) значение = 6.5
    result_35_20 = interp(35, 20)
    assert isinstance(result_35_20, np.ndarray)
    assert result_35_20[0][0] == pytest.approx(6.5, rel=0.01)
    
    result_25_100 = interp(25, 100)
    assert isinstance(result_25_100, np.ndarray)
    assert result_25_100[0][0] == pytest.approx(6.7, rel=0.01)


def test_create_namet_interpolator_high_temp():
    """Создание NAMET интерполятора (возрастающая температура в массиве)"""
    namet_data = [
        [20, 25, 30, 35],
        [20, 50, 100, 150],
        [[3.5, 4.0, 4.5, 5.0]] * 4
    ]
    s = TablePressureStrategy()
    interp = s._create_namet_interpolator(namet_data)
    assert isinstance(interp, RectBivariateSpline)
    
    result = interp(25, 50)
    assert isinstance(result, np.ndarray)
    assert result.shape == (1, 1)
    assert result[0][0] == pytest.approx(4.0, rel=0.01)


def test_create_namet_interpolator_extrapolate():
    """Экстраполяция значения за пределами таблицы"""
    namet_data = [
        [35, 30, 25],
        [20, 50, 100],
        [[6.5, 8.8, 10.9], [5.0, 6.8, 8.5], [3.8, 5.2, 6.7]]
    ]
    s = TablePressureStrategy()
    interp = s._create_namet_interpolator(namet_data)
    
    # Экстраполяция за пределами диапазона температур и расходов
    result = interp(40, 200)
    assert isinstance(result, np.ndarray)
    
    result = interp(10, 10)
    assert isinstance(result, np.ndarray)


def test_create_named_interpolator_base():
    """Создание NAMED интерполятора с экстраполяцией"""
    named_data = [
        [15.3, 26.8, 38.4, 49.9],
        [0.157, 0.258, 0.469, 0.607]
    ]
    s = TablePressureStrategy()
    interp = s._create_named_interpolator(named_data)
    assert isinstance(interp, interp1d)
    assert interp.bounds_error is False
    assert interp.fill_value == "extrapolate"


def test_create_named_interpolator():
    """Интерполяция внутри таблицы NAMED"""
    named_data = [
        [15.3, 26.8, 38.4, 49.9],
        [0.157, 0.258, 0.469, 0.607]
    ]
    s = TablePressureStrategy()
    interp = s._create_named_interpolator(named_data)
    result = interp(32.5)
    # interp1d возвращает np.ndarray для скалярного входа
    assert isinstance(result, (np.ndarray, float, np.floating))
    
    # Если result — массив, извлекаем значение
    if isinstance(result, np.ndarray):
        assert result.shape == ()
        value = result.item()
    else:
        value = result
    
    assert 0.258 < value < 0.469


def test_create_named_interpolator_extrap_high():
    """Экстраполяция NAMED выше максимума температуры"""
    named_data = [
        [15.3, 26.8, 38.4, 49.9],
        [0.157, 0.258, 0.469, 0.607]
    ]
    s = TablePressureStrategy()
    interp = s._create_named_interpolator(named_data)
    assert isinstance(interp, interp1d)
    result_high = interp(60.0)
    # interp1d возвращает np.ndarray для скалярного входа
    assert isinstance(result_high, (np.ndarray, float, np.floating))
    
    if isinstance(result_high, np.ndarray):
        value = result_high.item()
    else:
        value = result_high
    
    assert value > 0.607


def test_create_named_interpolator_extrap_low():
    """Экстраполяция NAMED ниже минимума температуры"""
    named_data = [
        [15.3, 26.8, 38.4, 49.9],
        [0.157, 0.258, 0.469, 0.607]
    ]
    s = TablePressureStrategy()
    interp = s._create_named_interpolator(named_data)
    assert isinstance(interp, interp1d)
    result_low = interp(10.0)
    assert isinstance(result_low, (np.ndarray, float, np.floating))
    
    if isinstance(result_low, np.ndarray):
        value = result_low.item()
    else:
        value = result_low
    
    assert value < 0.157


# =============================================================================
# ТЕСТЫ ОСНОВНОЙ ФУНКЦИИ calculate()
# =============================================================================


def test_calculate_base():
    """Базовый расчет давления по таблицам NAMET и NAMED"""
    params = {
        "NAMET": {
            "data": [
                [35, 30, 25],
                [20, 50, 100],
                [[6.5, 8.8, 10.9], [5.0, 6.8, 8.5], [3.8, 5.2, 6.7]]
            ],
        },
        "NAMED": {
            "data": [[15.3, 26.8, 38.4], [0.157, 0.258, 0.469]]
        },
        "inputs": {
            "temperature_cooling_water_1": 27.5,
            "mass_flow_flow_path_1": 75.0
        }
    }
    result = TablePressureStrategy().calculate(params)
    
    assert isinstance(result, dict)
    assert "pressure_flow_path_1_NAMET" in result
    assert "pressure_flow_path_1_NAMED" in result
    assert "pressure_flow_path_1" in result


def test_calculate_NAMET_greater():
    """Когда NAMET > NAMED, итоговое давление = NAMET"""
    params = {
        "NAMET": {
            "data": [[30, 25], [100, 200], [[5.0, 6.0], [4.0, 5.0]]],
        },
        "NAMED": {"data": [[20, 30], [0.1, 0.2]]},
        "inputs": {
            "temperature_cooling_water_1": 25.0,
            "mass_flow_flow_path_1": 150.0
        }
    }
    result = TablePressureStrategy().calculate(params)
    
    assert isinstance(result, dict)
    assert result["pressure_flow_path_1"] == result["pressure_flow_path_1_NAMET"]


def test_calculate_NAMED_greater():
    """Когда NAMED > NAMET, итоговое давление = NAMED"""
    params = {
        "NAMET": {
            "data": [[30, 25], [100, 200], [[0.1, 0.2], [0.08, 0.15]]],
        },
        "NAMED": {"data": [[20, 30], [0.5, 0.6]]},
        "inputs": {
            "temperature_cooling_water_1": 25.0,
            "mass_flow_flow_path_1": 150.0
        }
    }
    result = TablePressureStrategy().calculate(params)
    
    assert isinstance(result, dict)
    assert result["pressure_flow_path_1"] == result["pressure_flow_path_1_NAMED"]


def test_calculate_validation():
    """Валидация расчета по эталонным данным (t=30°C, G=112)"""
    params = {
        "NAMET": {
            "data": [
                [35, 33, 30, 25],
                [20, 50, 100, 150, 200],
                [
                    [6.549, 7.211, 8.88, 10.945, 13.409],
                    [5.9, 6.499, 8.018, 9.927, 12.214],
                    [5.036, 5.552, 6.872, 8.572, 10.622],
                    [3.851, 4.257, 5.299, 6.712, 8.438],
                ],
            ],
        },
        "NAMED": {
            "data": [
                [15.3, 26.8, 38.4, 49.9, 61.5, 73],
                [0.157, 0.258, 0.469, 0.607, 0.763, 0.919],
            ],
        },
        "inputs": {
            "temperature_cooling_water_1": 30.0,
            "mass_flow_flow_path_1": 112.0
        }
    }
    result = TablePressureStrategy().calculate(params)
    
    # Сравнение с погрешностью 1%
    assert result["pressure_flow_path_1_NAMET"] == pytest.approx(7.280, rel=0.01)
    assert result["pressure_flow_path_1_NAMED"] == pytest.approx(0.316, rel=0.01)
    assert result["pressure_flow_path_1"] == pytest.approx(7.280, rel=0.01)


def test_calculate_extrapolation():
    """Экстраполяция температуры за пределами таблицы (t=36°C, при max t=35°C)"""
    params = {
        "NAMET": {
            "data": [
                [35, 33, 30, 25],
                [20, 50, 100, 150, 200],
                [
                    [6.549, 7.211, 8.88, 10.945, 13.409],
                    [5.9, 6.499, 8.018, 9.927, 12.214],
                    [5.036, 5.552, 6.872, 8.572, 10.622],
                    [3.851, 4.257, 5.299, 6.712, 8.438],
                ],
            ],
        },
        "NAMED": {
            "data": [
                [15.3, 26.8, 38.4, 49.9, 61.5, 73],
                [0.157, 0.258, 0.469, 0.607, 0.763, 0.919],
            ],
        },
        "inputs": {
            "temperature_cooling_water_1": 36.0,  # Выход за пределы: 36 > 35
            "mass_flow_flow_path_1": 112.0
        }
    }
    result = TablePressureStrategy().calculate(params)
    
    # Проверка, что результат существует и положителен
    assert result["pressure_flow_path_1_NAMET"] is not None
    assert result["pressure_flow_path_1_NAMED"] is not None
    assert not np.isnan(result["pressure_flow_path_1_NAMET"])
    assert not np.isnan(result["pressure_flow_path_1_NAMED"])
    assert result["pressure_flow_path_1"] > 0


def test_calculate_boundary():
    """Граничные значения (углы таблицы): t=35°C, G=20"""
    params = {
        "NAMET": {
            "data": [
                [35, 33, 30, 25],
                [20, 50, 100, 150, 200],
                [
                    [6.549, 7.211, 8.88, 10.945, 13.409],
                    [5.9, 6.499, 8.018, 9.927, 12.214],
                    [5.036, 5.552, 6.872, 8.572, 10.622],
                    [3.851, 4.257, 5.299, 6.712, 8.438],
                ],
            ],
        },
        "NAMED": {
            "data": [
                [15.3, 26.8, 38.4, 49.9, 61.5, 73],
                [0.157, 0.258, 0.469, 0.607, 0.763, 0.919],
            ],
        },
        "inputs": {
            "temperature_cooling_water_1": 35.0,
            "mass_flow_flow_path_1": 20.0
        }
    }
    result = TablePressureStrategy().calculate(params)
    
    # При t=35, G=20: NAMET = 6.549 (угол таблицы)
    assert result["pressure_flow_path_1_NAMET"] == pytest.approx(6.549, rel=0.01)
    assert result["pressure_flow_path_1"] == pytest.approx(6.549, rel=0.01)
