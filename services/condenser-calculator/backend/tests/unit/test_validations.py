import pytest
from app.core.condenser_validators import validate_condenser_for_method, validate_water_flow_limits
from app.models import Condenser
from app.core.exceptions import ValidationError


def test_validate_condenser_br02_berman_missing_aircooler():
    condenser = Condenser(aircooler_count=None)
    with pytest.raises(ValidationError, match=r"Ошибка валидации БД \(BR-02\)"):
        validate_condenser_for_method(condenser, "berman")


def test_validate_condenser_br02_metrovickers_missing_aircooler():
    condenser = Condenser(aircooler_count=None)
    with pytest.raises(ValidationError, match=r"Ошибка валидации БД \(BR-02\)"):
        validate_condenser_for_method(condenser, "metro-vickers")


def test_validate_condenser_br02_valid():
    condenser = Condenser(aircooler_count=100)
    # Should not raise
    validate_condenser_for_method(condenser, "berman")
    validate_condenser_for_method(condenser, "metro-vickers")


def test_water_flow_limits_br06():
    limits = {
        "main_bundle": {"min": 6000.0, "max": 12000.0},
        "builtin_bundle": {"min": 500.0, "max": 1500.0},
    }

    # Normal operation within limits
    warnings = validate_water_flow_limits(8000.0, 1000.0, limits)
    assert len(warnings) == 0

    # Main below min
    warnings = validate_water_flow_limits(5000.0, 1000.0, limits)
    assert len(warnings) == 1
    assert "ниже минимума" in warnings[0]
    assert "BR-06" in warnings[0]

    # Builtin above max
    warnings = validate_water_flow_limits(8000.0, 2000.0, limits)
    assert len(warnings) == 1
    assert "выше максимума" in warnings[0]

    # Both violating
    warnings = validate_water_flow_limits(15000.0, 400.0, limits)
    assert len(warnings) == 2


def test_water_flow_limits_br07():
    limits = {
        "main_bundle": {"min": 6000.0, "max": 12000.0},
        "builtin_bundle": {"min": 500.0, "max": 1500.0},
    }

    # Single bundle running
    warnings = validate_water_flow_limits(15000.0, 0.0, limits)
    assert len(warnings) == 1
    assert "BR-07" in warnings[0]
    assert "ОП" in warnings[0]

    warnings = validate_water_flow_limits(0.0, 400.0, limits)
    assert len(warnings) == 1
    assert "BR-07" in warnings[0]
    assert "ВП" in warnings[0]


def test_water_flow_limits_empty():
    warnings = validate_water_flow_limits(8000.0, 1000.0, None)
    assert len(warnings) == 0
    warnings = validate_water_flow_limits(8000.0, 1000.0, {})
    assert len(warnings) == 0


def test_temperature_ranges_br10_berman():
    from app.core.condenser_validators import validate_temperature_ranges
    # Normal
    warnings = validate_temperature_ranges("berman", [10.0, 20.0, 30.0])
    assert len(warnings) == 0

    # Outside bounds
    warnings = validate_temperature_ranges("berman", [-5.0, 20.0])
    assert len(warnings) == 1
    assert "Берман" in warnings[0]

    warnings = validate_temperature_ranges("berman", [20.0, 50.0])
    assert len(warnings) == 1


def test_temperature_ranges_br10_metrovickers():
    from app.core.condenser_validators import validate_temperature_ranges
    # Normal
    warnings = validate_temperature_ranges("metro-vickers", [50.0, 100.0])
    assert len(warnings) == 0

    # Outside bounds
    warnings = validate_temperature_ranges("metro-vickers", [30.0, 60.0])
    assert len(warnings) == 1
    assert "Метро-Виккерс" in warnings[0]

    warnings = validate_temperature_ranges("metro-vickers", [100.0, 160.0])
    assert len(warnings) == 1
