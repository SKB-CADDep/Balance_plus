import pytest
from unittest.mock import MagicMock, patch
import time

import numpy as np

from app.adapters.calculation_adapter import CondenserCalculationAdapter
from app.core.exceptions import (
    MaterialPropertyError,
    UnitConversionError,
    CalculationEngineError,
)
from app.schemas.calculation import CalculationInput, MatrixResult, EjectorResult


# ===================================================================
# FIXTURES
# ===================================================================

@pytest.fixture
def adapter():
    return CondenserCalculationAdapter()


@pytest.fixture
def mock_condenser():
    c = MagicMock()
    c.id = 42
    c.name_condenser = "80-КЦС-3"
    c.main_length = 8950.0
    c.main_count = 8400
    c.builtin_length = 8950.0
    c.builtin_count = 1200
    c.aircooler_count = 450
    c.diameter_internal = 24.0
    c.wall_thickness = 1.0
    c.mass_flow_steam_nom = 155000.0
    c.mass_flow_air = 40.0
    return c


@pytest.fixture
def mock_material():
    m = MagicMock()
    m.id = 7
    m.name = "12МХЛ"
    m.thermal_conductivity_points = [
        [20.0, 110.0],
        [100.0, 105.0],
        [300.0, 98.0]
    ]
    return m


@pytest.fixture
def input_berman():
    return CalculationInput(
        condenser_id=42,
        material_id=7,
        method="berman",
        coefficient_b=[1.0, 0.75],
        G_steam=[10.0, 20.0, 30.0],
        W_main=[4000.0, 8000.0],
        W_builtin=[2000.0, 4000.0],
        t1_main=[10.0, 20.0],
        H_steam=560.5,
        H_steam_unit="ккал/кг",
    )


@pytest.fixture
def input_metrovickers(input_berman):
    data = input_berman.model_copy()
    data.method = "metro-vickers"
    data.H_steam = None
    data.X_steam = 0.95
    return data


# ===================================================================
# ПАРАМЕТРИЗОВАННЫЕ ТЕСТЫ
# ===================================================================

@pytest.mark.parametrize("method, h_steam, x_steam", [
    ("berman", 560.5, 0.95),
    ("metro-vickers", None, 0.95),
])
def test_calculate_different_methods(
    adapter, mock_condenser, mock_material, method, h_steam, x_steam
):
    """Параметризованный тест для обеих методик"""
    input_data = CalculationInput(
        condenser_id=42,
        material_id=7,
        method=method,
        coefficient_b=[1.0],
        G_steam=[20.0],
        W_main=[5000.0],
        t1_main=[20.0],
        H_steam=h_steam,
        X_steam=x_steam,
    )

    with patch.object(adapter, f'_run_{method.replace("-", "_")}') as mock_run:
        mock_run.return_value = (
            [MagicMock(spec=MatrixResult)],
            [MagicMock(spec=EjectorResult)] if method == "berman" else []
        )

        result = adapter.calculate(input_data, mock_condenser, mock_material)

        assert result.method == method
        assert result.total_tables == 1
        assert result.calculation_time_ms > 0


# ===================================================================
# ТЕСТЫ НА WARNINGS (BR-06, BR-10, BR-11)
# ===================================================================

def test_berman_warning_water_flow_limits(adapter, mock_condenser, mock_material, input_berman):
    """BR-06: Расход воды вне лимитов → warning"""
    input_berman.W_main = [30000.0]  # сильно выше номинала

    with patch.object(adapter, '_run_berman') as mock_run:
        mock_table = MagicMock(spec=MatrixResult)
        mock_table.warnings = ["Расход охлаждающей воды превышает максимальный паспортный"]
        mock_run.return_value = ([mock_table], [])

        result = adapter.calculate(input_berman, mock_condenser, mock_material)

        assert len(result.tables[0].warnings) > 0
        assert any("расход" in w.lower() for w in result.tables[0].warnings)


def test_berman_warning_temperature_range(adapter, mock_condenser, mock_material, input_berman):
    """BR-10: t1 > 45°C для Бермана → warning"""
    input_berman.t1_main = [50.0]

    with patch.object(adapter, '_run_berman') as mock_run:
        mock_table = MagicMock(spec=MatrixResult)
        mock_table.warnings = ["Температура 50.0°C выходит за оптимальный диапазон Бермана (0-45°C)"]
        mock_run.return_value = ([mock_table], [])

        result = adapter.calculate(input_berman, mock_condenser, mock_material)

        assert any("45" in w for w in result.tables[0].warnings)


def test_metrovickers_warning_extrapolation(adapter, mock_condenser, mock_material, input_metrovickers):
    """BR-11: Экстраполяция в MetroVickers → warning"""
    input_metrovickers.t1_main = [160.0]

    with patch.object(adapter, '_run_metrovickers') as mock_run:
        mock_table = MagicMock(spec=MatrixResult)
        mock_table.warnings = ["Данные находятся в области экстраполяции кривой K (Метро-Виккерс)"]
        mock_run.return_value = [mock_table]

        result = adapter.calculate(input_metrovickers, mock_condenser, mock_material)

        assert any("экстраполяц" in w.lower() for w in result.tables[0].warnings)


# ===================================================================
# ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ
# ===================================================================

def test_performance_under_500ms(adapter, mock_condenser, mock_material, input_berman):
    """Расчёт должен укладываться в 500 мс даже в худшем случае"""
    MAX_ALLOWED_MS = 500

    with patch.object(adapter, '_run_berman') as mock_run:
        mock_run.return_value = ([MagicMock()], [])

        start = time.perf_counter()
        adapter.calculate(input_berman, mock_condenser, mock_material)
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < MAX_ALLOWED_MS, f"Расчёт занял {duration_ms:.1f} мс (лимит {MAX_ALLOWED_MS} мс)"


# ===================================================================
# EDGE CASES
# ===================================================================

def test_w_builtin_none(adapter, mock_condenser, mock_material):
    """W_builtin = None должно работать корректно"""
    input_data = CalculationInput(
        condenser_id=42,
        material_id=7,
        method="berman",
        coefficient_b=[1.0],
        G_steam=[20.0],
        W_main=[5000.0],
        W_builtin=None,
        t1_main=[20.0],
        H_steam=560.5,
    )

    with patch.object(adapter, '_run_berman') as mock_run:
        mock_run.return_value = ([MagicMock()], [])
        result = adapter.calculate(input_data, mock_condenser, mock_material)

        assert result.total_tables == 1


def test_empty_coefficient_b_uses_default(adapter, mock_condenser, mock_material):
    """Пустой coefficient_b → используем default [1.0]"""
    input_data = CalculationInput(
        condenser_id=42,
        material_id=7,
        method="berman",
        coefficient_b=[],
        G_steam=[20.0],
        W_main=[5000.0],
        t1_main=[20.0],
        H_steam=560.5,
    )

    with patch.object(adapter, '_run_berman') as mock_run:
        mock_run.return_value = ([MagicMock()], [])
        result = adapter.calculate(input_data, mock_condenser, mock_material)

        assert result.tables[0].meta["coefficient_b"] == 1.0


# ===================================================================
# ТЕСТЫ КОНВЕРТЕРА
# ===================================================================

def test_converter_enthalpy_conversion():
    """Проверка корректности конвертера энтальпии"""
    from app.core.converter import converter

    result = converter.convert(560.5, "ккал/кг", "кДж/кг", "enthalpy")
    assert abs(result - 2348.0) < 5.0  # 560.5 * 4.1868 ≈ 2348


def test_converter_unknown_unit_raises():
    """Неизвестная единица → UnitConversionError"""
    from app.core.converter import converter
    from app.core.exceptions import UnitConversionError

    with pytest.raises(UnitConversionError):
        converter.convert(100.0, "попугаев/час", "кг/с", "mass_flow")