"""
Тестирование бизнес-логики исключений в конденсаторе (CondenserExceptions)

Покрытие:
- calculate_pressure() — 3 условия перехода
- Обработка None значений
- Проверка PIF > 0
"""

from app.utils.exceptions_method import CondenserExceptions


def test_calculate_pressure_condenser_positive():
    """
    Условие 1: pressure_condenser > 0
    
    При положительном давлении конденсатора возвращается его значение,
    остальные параметры игнорируются.
    """
    params = CondenserExceptions(
        pressure_condenser=7.280,
        temperature_cooling_water_1=30.0,
        pif=0.316,
    )
    result = params.calculate_pressure()
    assert result == 7.280


def test_calculate_pressure_condenser_zero():
    """
    Условие 1: pressure_condenser = 0 (не проходит)
    
    При нулевом давлении конденсатора первое условие не выполняется,
    проверяется второе условие.
    """
    params = CondenserExceptions(
        pressure_condenser=0,
        temperature_cooling_water_1=30.0,
        pif=0.316,
    )
    result = params.calculate_pressure()
    assert result is None


def test_calculate_pressure_condenser_negative():
    """
    Условие 1: pressure_condenser < 0 (не проходит)
    
    При отрицательном давлении конденсатора первое условие не выполняется,
    проверяется второе условие.
    """
    params = CondenserExceptions(
        pressure_condenser=-1.0,
        temperature_cooling_water_1=30.0,
        pif=0.316,
    )
    result = params.calculate_pressure()
    assert result is None


def test_calculate_pressure_condition2_all_none_pif_positive():
    """
    Условие 2: pressure_condenser = None, temperature_cooling_water_1 = None, PIF > 0
    
    При отсутствии давления конденсатора и температуры, но наличии положительного PIF,
    возвращается значение PIF.
    """
    params = CondenserExceptions(
        pressure_condenser=None,
        temperature_cooling_water_1=None,
        pif=0.316,
    )
    result = params.calculate_pressure()
    assert result == 0.316


def test_calculate_pressure_condition2_pif_zero():
    """
    Условие 2: PIF = 0 (не проходит)
    
    При отсутствии давления конденсатора и температуры, но нулевом PIF,
    возвращается None.
    """
    params = CondenserExceptions(
        pressure_condenser=None,
        temperature_cooling_water_1=None,
        pif=0,
    )
    result = params.calculate_pressure()
    assert result is None


def test_calculate_pressure_condition2_pif_negative():
    """
    Условие 2: PIF < 0 (не проходит)
    
    При отсутствии давления конденсатора и температуры, но отрицательном PIF,
    возвращается None.
    """
    params = CondenserExceptions(
        pressure_condenser=None,
        temperature_cooling_water_1=None,
        pif=-0.5,
    )
    result = params.calculate_pressure()
    assert result is None


def test_calculate_pressure_condition2_temperature_not_none():
    """
    Условие 2: temperature_cooling_water_1 != None (не проходит)
    
    При отсутствии давления конденсатора, но наличии температуры,
    возвращается None (не выполняется условие temperature_cooling_water_1 = None).
    """
    params = CondenserExceptions(
        pressure_condenser=None,
        temperature_cooling_water_1=30.0,
        pif=0.316,
    )
    result = params.calculate_pressure()
    assert result is None


def test_calculate_pressure_all_parameters_none():
    """
    Все параметры = None.
    
    При отсутствии всех параметров возвращается None.
    """
    params = CondenserExceptions(
        pressure_condenser=None,
        temperature_cooling_water_1=None,
        pif=None,
    )
    result = params.calculate_pressure()
    assert result is None


def test_calculate_pressure_only_pressure_condenser_set():
    """
    Только pressure_condenser != None, остальные None.
    
    При наличии только давления конденсатора (положительного) возвращается его значение.
    """
    params = CondenserExceptions(
        pressure_condenser=7.280,
        temperature_cooling_water_1=None,
        pif=None,
    )
    result = params.calculate_pressure()
    assert result == 7.280


def test_calculate_pressure_only_pif_set():
    """
    Только pif != None, остальные None.
    
    При наличии только PIF (положительного) и отсутствии других параметров
    возвращается значение PIF.
    """
    params = CondenserExceptions(
        pressure_condenser=None,
        temperature_cooling_water_1=None,
        pif=0.316,
    )
    result = params.calculate_pressure()
    assert result == 0.316


def test_calculate_pressure_pif_very_small_positive():
    """
    PIF очень маленькое положительное число (0.001).
    
    При минимальном положительном значении PIF возвращается его значение.
    """
    params = CondenserExceptions(
        pressure_condenser=None,
        temperature_cooling_water_1=None,
        pif=0.001,
    )
    result = params.calculate_pressure()
    assert result == 0.001


def test_calculate_pressure_condenser_exactly_one():
    """
    pressure_condenser = 1 (минимальное положительное значение).
    
    При минимальном положительном значении давления конденсатора
    возвращается его значение.
    """
    params = CondenserExceptions(
        pressure_condenser=1,
        temperature_cooling_water_1=None,
        pif=0.316,
    )
    result = params.calculate_pressure()
    assert result == 1


def test_calculate_pressure_priority_pressure_condenser_over_pif():
    """
    Приоритет: pressure_condenser > 0 имеет приоритет над pif.
    
    Если и давление конденсатора, и PIF положительны, возвращается давление конденсатора.
    """
    params = CondenserExceptions(
        pressure_condenser=7.280,
        temperature_cooling_water_1=30.0,
        pif=0.316,
    )
    result = params.calculate_pressure()
    assert result == 7.280


def test_calculate_pressure_multiple_calls_return_same_result():
    """
    Множественные вызовы возвращают одинаковый результат.
    
    Метод должен быть детерминированным — при одинаковых входных данных
    возвращать одинаковый результат.
    """
    params = CondenserExceptions(
        pressure_condenser=7.280,
        temperature_cooling_water_1=30.0,
        pif=0.316,
    )
    result1 = params.calculate_pressure()
    result2 = params.calculate_pressure()
    result3 = params.calculate_pressure()
    assert result1 == result2 == result3 == 7.280


def test_calculate_pressure_object_state_after_successful_calculation():
    """
    После успешного расчета pressure_flow_path_1 должен быть установлен.
    
    Проверка изменения состояния объекта после успешного расчета.
    """
    params = CondenserExceptions(
        pressure_condenser=7.280,
        temperature_cooling_water_1=30.0,
        pif=0.316,
    )
    result = params.calculate_pressure()
    assert params.pressure_flow_path_1 == 7.280
    assert result == 7.280


def test_calculate_pressure_object_state_after_failed_calculation():
    """
    После неуспешного расчета pressure_flow_path_1 должен остаться None.
    
    Проверка, что состояние объекта не изменяется при неуспешном расчете.
    """
    params = CondenserExceptions(
        pressure_condenser=-1.0,
        temperature_cooling_water_1=30.0,
        pif=-0.5,
    )
    result = params.calculate_pressure()
    assert params.pressure_flow_path_1 is None
    assert result is None
