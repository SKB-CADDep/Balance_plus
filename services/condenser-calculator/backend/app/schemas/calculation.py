from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Literal, Annotated, Any


FractionValue = Annotated[float, Field(ge=0.0, le=1.0)]


# =====================================================================
# REQUEST SCHEMAS (Входящие данные)
# =====================================================================
class CalculationInput(BaseModel):
    """Входные данные для расчета матрицы режимов конденсатора."""
    
    condenser_id: int = Field(..., description="ID конденсатора из БД оборудования (DB-EQUIP-CONDENSER)")
    
    # --- НОВАЯ ЛОГИКА: material_id теперь опциональный ---
    material_id: int | None = Field(
        default=None, 
        description="ID материала трубок. Если не передан, возьмется первый доступный для данного конденсатора"
    )
    
    method: Literal["berman", "metro-vickers"] = Field(..., description="Методика расчета (BR-01)")
    
    coefficient_b: list[FractionValue] = Field(
        default=[1.0], 
        description="Коэффициент чистоты (от 0 до 1)"
    )
    G_steam: list[float] = Field(..., min_length=1, description="Массив расходов пара (Ось X)")
    W_main: list[float] = Field(..., min_length=1, description="Массив расходов основной охл. воды")
    W_builtin: list[float] | None = Field(default=None, description="Массив расходов воды встроенного пучка")
    t1_main: list[float] = Field(..., min_length=1, description="Массив температур воды на входе (Ось Y)")
    t1_builtin: list[float] | None = Field(default=None, description="Температуры встроенного пучка")
    
    # Скалярные параметры (Конструктив)
    Z_ejectors: int = Field(default=1, ge=0, description="Количество рабочих эжекторов")
    Z_main: int = Field(default=2, ge=1, description="Число ходов основной воды")
    Z_builtin: int | None = Field(default=None, ge=1, description="Число ходов встроенного пучка")
    
    # Термодинамика пара
    H_steam: float | None = Field(default=None, description="Энтальпия пара (Обязательно для Бермана)")
    X_steam: float = Field(default=0.950, le=1.0, description="Степень сухости пара (Метро-Виккерс)")
    
    G_steam_unit: Literal["т/ч", "кг/с"] = "т/ч"
    W_main_unit: Literal["т/ч", "кг/с", "м3/ч", "т/с"] = "т/ч"
    t1_main_unit: Literal["°C", "K"] = "°C"
    H_steam_unit: Literal["ккал/кг", "кДж/кг"] = "ккал/кг"

    @model_validator(mode="after")
    def validate_cross_dependencies(self) -> "CalculationInput":
        """
        Кросс-валидация параметров согласно спецификации (BR-01, BR-04, BR-09).
        """
        if self.method == "berman" and self.H_steam is None:
            raise ValueError("Для метода 'berman' параметр энтальпии (H_steam) является обязательным.")
        
        if self.W_builtin is not None:
            if self.Z_builtin is None:
                raise ValueError("Если задан W_builtin, параметр Z_builtin обязателен.")
            
            if self.t1_builtin is None:
                self.t1_builtin = self.t1_main.copy()

        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "condenser_id": 1,
                "method": "berman",
                "coefficient_b": [0.8, 1.0],
                "G_steam": [10.0, 20.0, 30.0],
                "W_main": [4000, 8000],
                "t1_main": [10, 20],
                "H_steam": 560.5
            }
        }
    )


# =====================================================================
# RESPONSE SCHEMAS (Исходящие данные)
# =====================================================================

class MatrixResult(BaseModel):
    """Схема одной таблицы (матрицы) результатов для конкретной комбинации b и W."""
    
    meta: dict[str, Any] = Field(..., description="Метаданные (какие W и b использовались для этой матрицы)")
    columns: list[float] = Field(..., description="Заголовки столбцов (G_steam)")
    rows: list[float] = Field(..., description="Заголовки строк (t1_main)")
    values: list[list[float]] = Field(..., description="Матрица значений давления (P_steam)")
    warnings: list[str] = Field(default_factory=list, description="Предупреждения (выход за диапазоны, экстраполяция)")


class EjectorResult(BaseModel):
    """Результаты расчета эжекторов (Только для метода Бермана)."""
    
    number_of_ejectors: int
    P_ejector_kPa: float
    P_ejector_atm: float


class CalculationOutput(BaseModel):
    """Главная схема ответа (Результаты расчета)."""
    
    condenser_id: int
    condenser_name: str
    method: Literal["berman", "metro-vickers"]
    
    tables: list[MatrixResult] = Field(..., description="Сгенерированные матрицы P_steam")
    ejector_results: list[EjectorResult] = Field(default_factory=list, description="Данные эжекторов")
    
    total_tables: int = Field(..., description="Общее количество сгенерированных матриц")
    calculation_time_ms: float = Field(..., description="Время расчета в миллисекундах")