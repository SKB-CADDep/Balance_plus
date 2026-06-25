from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# =====================================================================
# REQUEST SCHEMAS (Входящие данные)
# =====================================================================


class CalculationGlobals(BaseModel):
    """Глобальные параметры расчета для всей турбины/группы."""

    P_fresh: float = Field(..., gt=0, description="Давление свежего пара")
    P_fresh_unit: Literal["кгс/см²", "МПа", "бар"] = "кгс/см²"

    T_fresh: float | None = None
    T_fresh_unit: Literal["°C", "K"] = "°C"

    H_fresh: float | None = None
    H_fresh_unit: Literal["ккал/кг", "кДж/кг"] = "ккал/кг"

    P_air: float = Field(default=1.033, gt=0)
    P_air_unit: Literal["кгс/см²", "МПа", "бар"] = "кгс/см²"

    T_air: float = 27.0
    T_air_unit: Literal["°C", "K"] = "°C"

    P_lst_leak_off: float = Field(default=0.97, gt=0)
    P_lst_leak_off_unit: Literal["кгс/см²", "МПа", "бар"] = "кгс/см²"

    @model_validator(mode="after")
    def check_temperature_and_enthalpy(self) -> "CalculationGlobals":
        """Валидация взаимоисключающих параметров T_fresh и H_fresh."""
        t_given = self.T_fresh is not None
        h_given = self.H_fresh is not None

        if t_given and h_given:
            raise ValueError(
                "Нельзя указывать одновременно температуру (T_fresh) и энтальпию (H_fresh) свежего пара."
            )
        if not t_given and not h_given:
            raise ValueError(
                "Необходимо указать либо начальную температуру (T_fresh), либо начальную энтальпию (H_fresh)."
            )
        return self


class ValveGroupInput(BaseModel):
    """Описание одной группы клапанов (c одинаковой геометрией)."""

    valve_id: int = Field(..., description="ID клапана, чью геометрию берем за основу")
    type: Literal["СК", "РК", "СРК"] = Field(..., description="Тип группы")

    valve_names: list[str] = Field(..., min_length=1, description="Список имен клапанов (напр. ['СК-1', 'СК-2'])")
    quantity: int = Field(..., ge=1, description="Количество клапанов в группе")

    p_values: list[float] = Field(default_factory=list, description="Давления перед участками")
    p_values_unit: Literal["кгс/см²", "МПа", "бар"] = "кгс/см²"

    p_leak_offs: list[float] = Field(default_factory=list, description="Промежуточные отсосы")
    p_leak_offs_unit: Literal["кгс/см²", "МПа", "бар"] = "кгс/см²"

    @model_validator(mode="after")
    def validate_names_and_quantity(self) -> "ValveGroupInput":
        """Проверка, что количество имен совпадает с заявленным количеством."""
        if len(self.valve_names) != self.quantity:
            raise ValueError(
                f"Поле quantity ({self.quantity}) не совпадает с количеством переданных имен клапанов ({len(self.valve_names)})."
            )
        return self


class MultiCalculationParams(BaseModel):
    """Главная схема входящего запроса на мульти-расчет."""
    turbine_id: int
    globals: CalculationGlobals
    groups: list[ValveGroupInput] = Field(..., min_length=1)


# =====================================================================
# RESPONSE SCHEMAS (Исходящие данные)
# =====================================================================


class GroupCalculationDetails(BaseModel):
    """Детализация результатов для одной конкретной группы."""
    valve_id: int
    type: Literal["СК", "РК", "СРК"]
    valve_names: list[str]
    quantity: int

    # Массивы параметров по участкам
    Gi: list[float]
    Pi_in: list[float]
    Ti: list[float]
    Hi: list[float]

    # Отсосы
    deaerator_props: list[float]
    ejector_props: list[dict[str, float]]

    # Итоги по группе
    group_total_g: float


class TypeSummary(BaseModel):
    """Сводные агрегированные данные для конкретного типа (Σ СК или Σ РК)."""
    total_g: float
    mixed_h: float


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
