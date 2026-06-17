"""
Pydantic-схемы для валидации данных расчетного ядра конденсаторов.

Определяют строгие API-контракты для запросов и ответов. Включают в себя
кросс-валидацию физических параметров (бизнес-правила BR) перед тем, как 
передать управление в слои адаптеров и математических движков.
"""

from pydantic import BaseModel, Field, model_validator, ConfigDict, field_validator
from typing import Literal, Annotated, Any

from app.core.range_parser import parse_range_input


# Тип для коэффициента чистоты труб (строго от 0 до 1)
FractionValue = Annotated[float, Field(ge=0.0, le=1.0)]


# =====================================================================
# REQUEST SCHEMAS (Входящие данные)
# =====================================================================
class CalculationInput(BaseModel):
    """
    Входные данные для мультирежимного расчета конденсатора.
    
    Агрегирует параметры геометрии, термодинамики пара и гидравлики охлаждающей воды.
    Позволяет передавать массивы значений для генерации матриц результатов.
    """
    
    condenser_id: int = Field(..., description="ID конденсатора из БД оборудования (DB-EQUIP-CONDENSER)")
    
    # Если материал не передан, логика контроллера (router) должна подтянуть 
    # материал по умолчанию из карточки конденсатора.
    material_id: int | None = Field(
        default=None, 
        description="ID материала трубок. Если не передан, возьмется дефолтный для данного конденсатора"
    )
    
    method: Literal["berman", "metro-vickers"] = Field(..., description="Методика расчета (BR-01)")
    
    coefficient_b: str | list[FractionValue] = Field(
        default=[1.0], 
        description="Массив коэффициентов чистоты поверхности теплообмена (от 0 до 1)"
    )
    G_steam: str | list[float] = Field(..., description="Массив расходов пара (Ось X)")
    W_main: str | list[float] = Field(..., description="Массив расходов основной охл. воды")
    W_builtin: str | list[float] | None = Field(default=None, description="Массив расходов воды встроенного пучка")
    t1_main: str | list[float] = Field(..., description="Массив температур воды на входе (Ось Y)")
    t1_builtin: str | list[float] | None = Field(default=None, description="Температуры встроенного пучка")
    
    # --- Скалярные параметры (Конструктив) ---
    Z_ejectors: int = Field(default=1, ge=0, description="Количество работающих основных эжекторов")
    Z_main: int = Field(default=2, ge=1, description="Число ходов основной охлаждающей воды")
    Z_builtin: int | None = Field(default=None, ge=1, description="Число ходов воды во встроенном пучке")
    
    # --- Термодинамика пара ---
    H_steam: float | None = Field(default=None, description="Энтальпия отработавшего пара (обязательно для метода Бермана)")
    X_steam: float = Field(default=0.950, le=1.0, description="Степень сухости пара (используется в методе Метро-Виккерс)")
    
    # --- Единицы измерения (для конвертеров) ---
    G_steam_unit: Literal["т/ч", "кг/с"] = "т/ч"
    W_main_unit: Literal["т/ч", "кг/с", "м3/ч", "т/с"] = "т/ч"
    t1_main_unit: Literal["°C", "K"] = "°C"
    H_steam_unit: Literal["ккал/кг", "кДж/кг"] = "ккал/кг"

    @field_validator("G_steam", "W_main", "t1_main", mode="before")
    @classmethod
    def parse_required_range_fields(cls, value):
        if isinstance(value, str):
            parsed = parse_range_input(value)
            if not parsed:
                raise ValueError("Поле не может быть пустым.")
            return parsed
        return value

    @field_validator("W_builtin", "t1_builtin", mode="before")
    @classmethod
    def parse_optional_range_fields(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            if not value.strip():
                return None
            return parse_range_input(value)
        return value

    @field_validator("coefficient_b", mode="before")
    @classmethod
    def parse_coefficient_b(cls, value):
        if isinstance(value, str):
            if not value.strip():
                return [1.0]
            parsed = parse_range_input(value)
            for v in parsed:
                if v < 0.0 or v > 1.0:
                    raise ValueError("coefficient_b должен быть в диапазоне [0..1].")
            return parsed
        return value

    @model_validator(mode="after")
    def validate_cross_dependencies(self) -> "CalculationInput":
        """
        Кросс-валидация параметров согласно бизнес-требованиям (BR-01, BR-04, BR-09).

        Проверяет логическую целостность запроса, где наличие одних полей 
        зависит от значений других (например, зависимость энтальпии от метода расчета).

        Returns:
            CalculationInput: Провалидированный экземпляр текущей модели.

        Raises:
            ValueError: Если нарушены физические или бизнес-правила (например,
                выбран метод Бермана, но не передана энтальпия пара).
        """
        if self.method == "berman" and self.H_steam is None:
            raise ValueError("Для метода 'berman' параметр энтальпии (H_steam) является обязательным.")
        
        if self.W_builtin is not None:
            if self.Z_builtin is None:
                raise ValueError("Если задан расход встроенного пучка (W_builtin), число ходов (Z_builtin) обязательно.")
            
            # Автоматическое наследование температур для встроенного пучка, 
            # если они не переданы явно (упрощение для пользователя)
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
    """
    Схема одной таблицы (матрицы) результатов для конкретной комбинации b и W.
    Обычно содержит рассчитанное давление пара в конденсаторе (P_c).
    """
    
    meta: dict[str, Any] = Field(..., description="Метаданные (например, значения W и b, для которых построена матрица)")
    columns: list[float] = Field(..., description="Заголовки столбцов (как правило, расходы пара G_steam)")
    rows: list[float] = Field(..., description="Заголовки строк (как правило, температуры воды t1_main)")
    values: list[list[float]] = Field(..., description="Двумерный массив рассчитанных значений (давлений)")
    warnings: list[str] = Field(default_factory=list, description="Предупреждения ядра (выход за диапазоны, экстраполяция)")


class EjectorResult(BaseModel):
    """
    Результаты расчета характеристик воздухоудаляющего устройства (эжектора).
    Применимо преимущественно в методике ВТИ (Бермана).
    """
    
    number_of_ejectors: int = Field(..., description="Количество задействованных аппаратов")
    P_ejector_kPa: float = Field(..., description="Давление у эжектора в кПа")
    P_ejector_atm: float = Field(..., description="Давление у эжектора в ата (атмосферах абсолютных)")


class CalculationOutput(BaseModel):
    """
    Главная схема ответа (Агрегированные результаты расчета).
    
    Содержит все сгенерированные матрицы, метаданные об оборудовании
    и телеметрию выполнения (время расчета).
    """
    
    condenser_id: int = Field(..., description="ID рассчитанного конденсатора")
    condenser_name: str = Field(..., description="Наименование или маркировка конденсатора")
    method: Literal["berman", "metro-vickers"] = Field(..., description="Использованная методика расчета")
    
    tables: list[MatrixResult] = Field(..., description="Массив сгенерированных матриц (таблиц) результатов")
    ejector_results: list[EjectorResult] = Field(default_factory=list, description="Результаты расчета эжекторной установки")
    
    total_tables: int = Field(..., description="Общее количество сгенерированных матриц")
    calculation_time_ms: float = Field(..., description="Время, затраченное математическим ядром, в миллисекундах")
    