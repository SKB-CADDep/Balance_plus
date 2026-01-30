"""
Набор unit-тестов для класса UnitConverter из модуля ``uniconv.py``.

Тесты написаны под `pytest` (pip install pytest).
Запуск:  pytest -q
"""

import pytest

from app.utils.uniconv import (
    UnitConverter,
    UnknownParameterError,
    UnknownUnitError,
)


# ------------------------------------------------------------------
# ФИКСТУРА ― общий экземпляр конвертера для всех тестов
# ------------------------------------------------------------------
@pytest.fixture(scope="module")
def uc() -> UnitConverter:
    """Возвращает единый экземпляр UnitConverter на время модуля."""
    return UnitConverter()


# ------------------------------------------------------------------
# 1. Базовые «счастливые» сценарии
# ------------------------------------------------------------------
def test_pressure_bar_to_kgf(uc: UnitConverter):
    """10 бар ≈ 10.204 кгс/см²"""
    result = uc.convert(
        10, from_unit="бар", to_unit="кгс/см²", parameter_type="pressure"
    )
    assert result == pytest.approx(10 * 100_000 / 98_066.5, rel=1e-6)


def test_temperature_c_to_k_and_back(uc: UnitConverter):
    """Обратимость °C ↔ K"""
    t_c = 25.0
    k = uc.convert(t_c, from_unit="°C", to_unit="K", parameter_type="temperature")
    assert k == pytest.approx(298.15, abs=1e-12)

    # Обратно
    c_back = uc.convert(k, from_unit="K", to_unit="°C", parameter_type="temperature")
    assert c_back == pytest.approx(t_c, abs=1e-12)


def test_density_linear_factor(uc: UnitConverter):
    """Проверяем линейный коэффициент г/см³ ↔ кг/м³"""
    rho_g = 1.2  # г/см³
    rho_kg = uc.convert(rho_g, from_unit="г/см³", to_unit="кг/м³", parameter_type="density")
    assert rho_kg == pytest.approx(1200.0, rel=1e-9)


def test_quality_percent(uc: UnitConverter):
    """85 % → 0.85 и обратно"""
    quality_percent = 85.0
    frac = uc.to_base(quality_percent, from_unit="%", parameter_type="quality")
    assert frac == pytest.approx(0.85)

    perc_back = uc.from_base(frac, to_unit="%", parameter_type="quality")
    assert perc_back == pytest.approx(quality_percent)


def test_identity_conversion(uc: UnitConverter):
    """Конвертация в ту же единицу должна возвращать исходное значение"""
    value = 123.456
    out = uc.convert(value, from_unit="кВт", to_unit="кВт", parameter_type="power")
    assert out == pytest.approx(value)


# ------------------------------------------------------------------
# 2. Метаданные
# ------------------------------------------------------------------
def test_get_base_and_available_units(uc: UnitConverter):
    base = uc.get_base_unit("pressure")
    assert base == "кгс/см²"

    units = uc.get_available_units("pressure")
    # проверяем несколько ключевых единиц
    for u in ("кгс/см²", "Па", "бар"):
        assert u in units


# ------------------------------------------------------------------
# 3. Динамическое расширение API
# ------------------------------------------------------------------
def test_add_new_parameter_and_unit(uc: UnitConverter):
    """Добавляем 'length' c базовой единицей 'м' и проверяем конвертацию."""
    # Добавляем параметр (если он вдруг существует — пропускаем)
    try:
        uc.add_parameter("length", base_unit_symbol="м", base_unit_name="метр")
    except ValueError:
        # уже был добавлен в другом тесте — ничего страшного
        pass

    # Добавляем сантиметры как линейный коэффициент (1 см = 0.01 м)
    uc.add_unit(
        "length",
        unit_symbol="см",
        unit_name="сантиметр",
        to_base=0.01,
        from_base=100,
    )

    fifty_cm = uc.to_base(50, from_unit="см", parameter_type="length")
    assert fifty_cm == pytest.approx(0.5)

    meters_back = uc.from_base(fifty_cm, to_unit="см", parameter_type="length")
    assert meters_back == pytest.approx(50)


def test_add_unit_non_linear(uc: UnitConverter):
    """Пример добавления нелинейной конверсии: °F ↔ °C."""
    # Возможно, unit уже добавлен в ранних запусках — тогда пропустится.
    try:
        uc.add_unit(
            "temperature",
            unit_symbol="°F",
            unit_name="градус Фаренгейта",
            to_base=lambda f: (f - 32) * 5.0 / 9.0,        # °F → °C
            from_base=lambda c: c * 9.0 / 5.0 + 32,        # °C → °F
        )
    except ValueError:
        pass  # Unit уже был

    # Проверка правильности
    temp_f = 212.0  # точка кипения воды
    temp_c = uc.convert(temp_f, from_unit="°F", to_unit="°C", parameter_type="temperature")
    assert temp_c == pytest.approx(100.0, abs=1e-12)


# ------------------------------------------------------------------
# 4. Обработка ошибок
# ------------------------------------------------------------------
def test_unknown_parameter_raises(uc: UnitConverter):
    with pytest.raises(UnknownParameterError):
        uc.convert(1, from_unit="foo", to_unit="bar", parameter_type="nonexistent")


def test_unknown_unit_raises(uc: UnitConverter):
    with pytest.raises(UnknownUnitError):
        uc.convert(1, from_unit="foo", to_unit="bar", parameter_type="pressure")