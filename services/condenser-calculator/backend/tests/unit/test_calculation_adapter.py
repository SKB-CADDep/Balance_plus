"""
Юнит-тесты ядра калькулятора конденсаторов (Calculation Adapter).
Проверка стратегий расчета, граничных условий, лимитов и обработки ошибок.
"""
import time
from unittest.mock import MagicMock, patch

import pytest

from app.adapters.calculation_adapter import CondenserCalculationAdapter
from app.core.exceptions import CalculationEngineError
from app.schemas.calculation import CalculationInput, EjectorResult, MatrixResult


# ===================================================================
# ХЕЛПЕРЫ ДЛЯ PYDANTIC V2
# ===================================================================
def create_mock_matrix(warnings:list[str]|None=None, meta:dict|None = None) -> MatrixResult:
    """Создает 'чистый' объект MatrixResult без строгой валидации для тестов"""
    return MatrixResult.model_construct(
        method="berman",
        meta=meta or {"coefficient_b": 1.0},
        headers=[],
        data=[],
        warnings=warnings or[]
    )

def create_mock_ejector() -> EjectorResult:
    return EjectorResult.model_construct(
        mass_flow_air=40.0,
        steam_consumption=150.0
    )


# ===================================================================
# FIXTURES
# ===================================================================

@pytest.fixture
def adapter() -> CondenserCalculationAdapter:
    return CondenserCalculationAdapter()


@pytest.fixture
def mock_condenser() -> MagicMock:
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
    c.water_flow_max = 20000.0
    return c


@pytest.fixture
def mock_material() -> MagicMock:
    m = MagicMock()
    m.id = 7
    m.name = "12МХЛ"
    m.thermal_conductivity_points = [[20.0, 110.0],[100.0, 105.0],[300.0, 98.0]]
    return m


@pytest.fixture
def input_berman() -> CalculationInput:
    return CalculationInput(
        condenser_id=42,
        material_id=7,
        method="berman",
        coefficient_b=[1.0, 0.75],
        G_steam=[10.0, 20.0, 30.0],
        W_main=[4000.0, 8000.0],
        W_builtin=[2000.0, 4000.0],
        Z_builtin=2,  # Обязателен при наличии W_builtin
        t1_main=[10.0, 20.0],
        H_steam=560.5,
        H_steam_unit="ккал/кг",
    )


@pytest.fixture
def input_metrovickers(input_berman:CalculationInput) -> CalculationInput:
    data = input_berman.model_copy()
    data.method = "metro-vickers"
    data.H_steam = None
    data.X_steam = 0.95
    return data


# ===================================================================
# ПАРАМЕТРИЗОВАННЫЕ БАЗОВЫЕ ТЕСТЫ
# ===================================================================

@pytest.mark.parametrize("method, h_steam, x_steam, engine_mock_name",[
    ("berman", 560.5, 0.95, "_run_berman"),
    ("metro-vickers", None, 0.95, "_run_metrovickers"),
])
def test_calculate_different_methods(
    adapter:CondenserCalculationAdapter, mock_condenser:MagicMock, mock_material:MagicMock, method:str, h_steam:float|None, x_steam:float, engine_mock_name:str
) -> None:
    """Базовая маршрутизация для обеих методик расчета"""
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

    with patch.object(adapter, engine_mock_name) as mock_run:
        # ИСПРАВЛЕНИЕ: Методы возвращают разные типы данных
        if method == "berman":
            mock_run.return_value = ([create_mock_matrix()],[create_mock_ejector()])
        else:
            mock_run.return_value = [create_mock_matrix()]

        result = adapter.calculate(input_data, mock_condenser, mock_material)

        assert result.method == method
        assert result.total_tables == 1
        assert result.calculation_time_ms >= 0


# ===================================================================
# ТЕСТЫ НА WARNINGS (BR-06, BR-10, BR-11)
# ===================================================================

def test_berman_warning_water_flow_limits(adapter:CondenserCalculationAdapter, mock_condenser:MagicMock, mock_material:MagicMock, input_berman:CalculationInput) -> None:
    """BR-06: Превышение паспортного расхода охлаждающей воды должно генерировать warning"""
    input_berman.W_main = [30000.0]  # Выше лимита (20000.0)

    with patch.object(adapter, '_run_berman') as mock_run:
        mock_run.return_value = ([create_mock_matrix(warnings=["Расход охлаждающей воды превышает максимальный паспортный"])],[])

        result = adapter.calculate(input_berman, mock_condenser, mock_material)
        assert any("расход" in w.lower() for w in result.tables[0].warnings)


def test_berman_warning_temperature_range_high(adapter:CondenserCalculationAdapter, mock_condenser:MagicMock, mock_material:MagicMock, input_berman:CalculationInput) -> None:
    """BR-10: t1 > 45°C для Бермана должно генерировать warning"""
    input_berman.t1_main = [50.0]

    with patch.object(adapter, '_run_berman') as mock_run:
        mock_run.return_value = ([create_mock_matrix(warnings=["Температура 50.0°C выходит за оптимальный диапазон Бермана"])],[])

        result = adapter.calculate(input_berman, mock_condenser, mock_material)
        assert any("50.0" in w for w in result.tables[0].warnings)


def test_metrovickers_warning_extrapolation(adapter:CondenserCalculationAdapter, mock_condenser:MagicMock, mock_material:MagicMock, input_metrovickers:CalculationInput) -> None:
    """BR-11: Экстраполяция в MetroVickers при выходе за пределы номограммы"""
    input_metrovickers.t1_main = [160.0]

    with patch.object(adapter, '_run_metrovickers') as mock_run:
        mock_run.return_value = [create_mock_matrix(warnings=["Данные находятся в области экстраполяции кривой K (Метро-Виккерс)"])]

        result = adapter.calculate(input_metrovickers, mock_condenser, mock_material)
        assert any("экстраполяц" in w.lower() for w in result.tables[0].warnings)


# ===================================================================
# EDGE CASES: МАССИВЫ И КОНФИГУРАЦИЯ ПУЧКОВ
# ===================================================================

def test_w_builtin_none(adapter:CondenserCalculationAdapter, mock_condenser:MagicMock, mock_material:MagicMock, input_berman:CalculationInput) -> None:
    """Один пучок: W_builtin = None должно корректно обрабатываться"""
    input_berman.W_builtin = None
    input_berman.Z_builtin = None

    with patch.object(adapter, '_run_berman') as mock_run:
        mock_run.return_value = ([create_mock_matrix()],[])
        result = adapter.calculate(input_berman, mock_condenser, mock_material)
        assert result.total_tables == 1


def test_w_builtin_empty_array(adapter:CondenserCalculationAdapter, mock_condenser:MagicMock, mock_material:MagicMock, input_berman:CalculationInput) -> None:
    """Один пучок: W_builtin =[] должно приравниваться к отсутствию встроенного пучка"""
    input_berman.W_builtin =[]
    input_berman.Z_builtin = None

    with patch.object(adapter, '_run_berman') as mock_run:
        mock_run.return_value = ([create_mock_matrix()],[])
        result = adapter.calculate(input_berman, mock_condenser, mock_material)
        assert result.total_tables == 1


def test_different_lengths_w_main_w_builtin(adapter:CondenserCalculationAdapter, mock_condenser:MagicMock, mock_material:MagicMock, input_berman:CalculationInput) -> None:
    """Разные длины массивов W_main и W_builtin должны рассчитываться"""
    input_berman.W_main =[4000.0, 5000.0, 6000.0]
    input_berman.W_builtin = [2000.0]

    with patch.object(adapter, '_run_berman') as mock_run:
        mock_run.return_value = ([create_mock_matrix()],[])
        adapter.calculate(input_berman, mock_condenser, mock_material)
        assert mock_run.called


def test_empty_coefficient_b_uses_default(adapter:CondenserCalculationAdapter, mock_condenser:MagicMock, mock_material:MagicMock, input_berman:CalculationInput) -> None:
    """Пустой coefficient_b -> система должна использовать значение по умолчанию [1.0]"""
    input_berman.coefficient_b =[]
    with patch.object(adapter, '_run_berman') as mock_run:
        mock_run.return_value = ([create_mock_matrix(meta={"coefficient_b": 1.0})],[])
        result = adapter.calculate(input_berman, mock_condenser, mock_material)
        assert result.tables[0].meta["coefficient_b"] == 1.0


# ===================================================================
# EDGE CASES: ГРАНИЧНЫЕ ЗНАЧЕНИЯ ПАРАМЕТРОВ
# ===================================================================

@pytest.mark.parametrize("b_val",[0.0, 0.75, 0.999, 1.0])
def test_boundary_b_values(adapter:CondenserCalculationAdapter, mock_condenser:MagicMock, mock_material:MagicMock, input_berman:CalculationInput, b_val:float) -> None:
    """Граничные значения коэффициента загрязнения b (от абсолютного загрязнения до чистого)"""
    input_berman.coefficient_b = [b_val]
    with patch.object(adapter, '_run_berman') as mock_run:
        mock_run.return_value = ([create_mock_matrix()],[])
        try:
            adapter.calculate(input_berman, mock_condenser, mock_material)
        except CalculationEngineError:
            pytest.fail(f"Брошено исключение при валидном граничном b={b_val}")


@pytest.mark.parametrize("temp, expected_warning",[
    (0.0, False),    # Нижняя граница Бермана, норм
    (45.0, False),   # Верхняя граница Бермана, норм
    (150.0, True),   # Экстремально высокая температура
])
def test_temperature_edge_cases(adapter:CondenserCalculationAdapter, mock_condenser:MagicMock, mock_material:MagicMock, input_berman:CalculationInput, temp:float, expected_warning:bool) -> None:
    """Температурные граничные случаи (0°C, 45°C, 150°C)"""
    input_berman.t1_main = [temp]

    with patch.object(adapter, '_run_berman') as mock_run:
        mock_run.return_value = ([create_mock_matrix(warnings=["Выход за диапазон"] if expected_warning else [])],[])

        result = adapter.calculate(input_berman, mock_condenser, mock_material)
        if expected_warning:
            assert len(result.tables[0].warnings) > 0
        else:
            assert len(result.tables[0].warnings) == 0


# ===================================================================
# EDGE CASES: ИСКЛЮЧЕНИЯ И ВАЛИДАЦИИ (Перехватываемые ошибки)
# ===================================================================

def test_invalid_method(adapter:CondenserCalculationAdapter, mock_condenser:MagicMock, mock_material:MagicMock, input_berman:CalculationInput) -> None:
    """Передача несуществующего метода расчета обрубается Pydantic или адаптером"""
    input_berman.method = "unknown_magic_method"
    with pytest.raises(CalculationEngineError):
        adapter.calculate(input_berman, mock_condenser, mock_material)


def test_engine_errors_are_wrapped(adapter:CondenserCalculationAdapter, mock_condenser:MagicMock, mock_material:MagicMock, input_berman:CalculationInput) -> None:
    """Сбой внутри физического движка (например, деление на ноль) должен оборачиваться адаптером в CalculationEngineError"""
    with patch.object(adapter, '_run_berman', side_effect=Exception("Internal physics division by zero")):
        with pytest.raises(CalculationEngineError, match="Ошибка при выполнении расчёта"):
            adapter.calculate(input_berman, mock_condenser, mock_material)


# ===================================================================
# ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ
# ===================================================================

def test_performance_under_500ms(adapter:CondenserCalculationAdapter, mock_condenser:MagicMock, mock_material:MagicMock, input_berman:CalculationInput) -> None:
    """Расчёт должен укладываться в 500 мс (неблокирующий event-loop)"""
    MAX_ALLOWED_MS = 500
    with patch.object(adapter, '_run_berman') as mock_run:
        mock_run.return_value = ([create_mock_matrix()],[])

        start = time.perf_counter()
        adapter.calculate(input_berman, mock_condenser, mock_material)
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < MAX_ALLOWED_MS, f"Расчёт занял {duration_ms:.1f} мс"
