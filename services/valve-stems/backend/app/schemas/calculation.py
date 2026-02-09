from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

class CalculationParams(BaseModel):
    turbine_name: Optional[str] = None
    valve_drawing: Optional[str] = None
    valve_id: Optional[int] = None
    temperature_start: float
    t_air: float
    count_valves: int
    p_ejector: List[float]
    p_values: List[float]

class CalculationResult(BaseModel):
    Gi: List[float]
    Pi_in: List[float]
    Ti: List[float]
    Hi: List[float]
    deaerator_props: List[float]
    ejector_props: List[Dict[str, float]]

class CalculationResultDB(BaseModel):
    id: int
    user_name: Optional[str] = None
    stock_name: str
    turbine_name: str
    calc_timestamp: datetime
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class ErrorResponse(BaseModel):
    error: bool
    message: str
    detail: Optional[str] = None