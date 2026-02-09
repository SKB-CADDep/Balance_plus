from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CalculationParams(BaseModel):
    turbine_name: str | None = None
    valve_drawing: str | None = None
    valve_id: int | None = None
    temperature_start: float
    t_air: float
    count_valves: int
    p_ejector: list[float]
    p_values: list[float]

class CalculationResult(BaseModel):
    Gi: list[float]
    Pi_in: list[float]
    Ti: list[float]
    Hi: list[float]
    deaerator_props: list[float]
    ejector_props: list[dict[str, float]]

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
    error: bool
    message: str
    detail: str | None = None
