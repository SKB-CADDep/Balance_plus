from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


# --- Вспомогательные ---
class MeasureValue(BaseModel):
    """Значение с единицей измерения (чтобы фронт мог слать 'bar', 'MPa')"""
    value: float
    unit: str = "kgf/cm2"


# --- Проект (CRUD) ---
class ProjectCreate(BaseModel):
    turbine_id: int
    station_name: str
    factory_number: str
    station_number: Optional[str] = None


class ProjectResponse(ProjectCreate):
    id: int
    turbine_name: str  # Подтягиваем имя из связи
    model_config = ConfigDict(from_attributes=True)


# --- Расчет (Input) ---
class ValveSelectionRequest(BaseModel):
    valve_id: int
    quantity: int = Field(default=1, ge=1, description="Количество таких клапанов")
    # Пользователь может переопределить давления в отсосах вручную
    custom_leak_offs: Optional[List[MeasureValue]] = None


class MultiCalculationRequest(BaseModel):
    project_id: Optional[int] = None  # Если сохраняем в историю

    # Глобальные параметры пара перед всеми клапанами
    p_fresh: MeasureValue
    t_fresh: MeasureValue

    # Список выбранных клапанов
    valves: List[ValveSelectionRequest]


# --- Результат (Output) ---
class ValveCalculationResult(BaseModel):
    valve_id: int
    valve_name: str
    valve_type: str  # "СК" или "РК" (важно для группировки)
    quantity: int

    # Детальный расчет по камерам (как сейчас)
    segments: List[dict]

    # Итоги
    flow_per_one: float  # Расход на 1 клапан
    flow_total: float  # flow_per_one * quantity


class CalculationSummary(BaseModel):
    total_flow_sk: float  # Сумма по Стопорным
    total_flow_rk: float  # Сумма по Регулирующим
    total_flow_all: float


class MultiCalculationResponse(BaseModel):
    summary: CalculationSummary
    details: List[ValveCalculationResult]