from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


# =====================================================================
# REQUEST SCHEMAS (Входящие данные)
# =====================================================================

class CalculationGlobals(BaseModel):
    """Глобальные параметры расчета для всей турбины/группы."""
    P_fresh: float
    P_fresh_unit: str = "кгс/см²"
    
    T_fresh: float | None = None
    T_fresh_unit: str = "°C"
    
    H_fresh: float | None = None
    H_fresh_unit: str = "ккал/кг"
    
    P_air: float = 1.033
    P_air_unit: str = "кгс/см²"
    
    T_air: float = 27.0
    T_air_unit: str = "°C"
    
    P_lst_leak_off: float = 0.97
    P_lst_leak_off_unit: str = "кгс/см²"

    @model_validator(mode='after')
    def check_temperature_and_enthalpy(self) -> "CalculationGlobals":
        """Валидация взаимоисключающих параметров T_fresh и H_fresh."""
        t_given = self.T_fresh is not None
        h_given = self.H_fresh is not None

        if t_given and h_given:
            raise ValueError(
                "Нельзя указывать одновременно температуру и энтальпию свежего пара. "
                "Оставьте одно из полей пустым (null)."
            )
        if not t_given and not h_given:
            raise ValueError(
                "Необходимо указать либо начальную температуру (T_fresh), "
                "либо начальную энтальпию (H_fresh)."
            )
        return self


class ValveGroupInput(BaseModel):
    """Описание одной группы клапанов (с одинаковой геометрией)."""
    valve_id: int = Field(..., description="ID клапана, чью геометрию берем за основу")
    type: str = Field(..., description="Тип группы: 'СК' или 'РК'")
    valve_names: list[str] = Field(..., description="Список имен клапанов, входящих в группу")
    quantity: int = Field(..., ge=1, description="Количество клапанов в группе")
    
    p_values: list[float] = Field(default_factory=list, description="Давления перед участками")
    p_values_unit: str = "кгс/см²"
    
    p_leak_offs: list[float] = Field(default_factory=list, description="Промежуточные отсосы")
    p_leak_offs_unit: str = "кгс/см²"


class MultiCalculationParams(BaseModel):
    """Главная схема входящего запроса на мульти-расчет."""
    turbine_id: int
    globals: CalculationGlobals
    groups: list[ValveGroupInput]


# =====================================================================
# RESPONSE SCHEMAS (Исходящие данные)
# =====================================================================

class GroupCalculationDetails(BaseModel):
    """Детализация результатов для одной конкретной группы."""
    valve_id: int
    type: str
    valve_names: list[str]
    quantity: int

    # Массивы параметров по участкам (для ОДНОГО клапана в группе)
    Gi: list[float]
    Pi_in: list[float]
    Ti: list[float]
    Hi: list[float]
    
    # Отсосы (для ОДНОГО клапана)
    deaerator_props: list[float]
    ejector_props: list[dict[str, float]]
    
    # Итоги по группе (Gi 1-го клапана * quantity)
    group_total_g: float


class TypeSummary(BaseModel):
    """Сводные агрегированные данные для конкретного типа."""
    total_g: float  # Суммарный расход
    mixed_h: float  # Средневзвешенная энтальпия смеси


class CalculationSummary(BaseModel):
    """Главный объект сводных таблиц."""
    sk: TypeSummary
    rk: TypeSummary
    srk: TypeSummary


class MultiCalculationResult(BaseModel):
    """Главная схема ответа на мульти-расчет."""
    details: list[GroupCalculationDetails]
    summary: CalculationSummary


# =====================================================================
# DATABASE SCHEMAS (Хранение)
# =====================================================================

class CalculationResultDB(BaseModel):
    id: int
    user_name: str | None = None
    stock_name: str
    turbine_name: str
    calc_timestamp: datetime
    input_data: dict[str, Any]
    output_data: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Общая схема для отображения ошибок API."""
    error: bool
    message: str
    detail: str | None = None