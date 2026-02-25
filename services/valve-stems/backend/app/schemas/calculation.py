from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class CalculationParams(BaseModel):
    turbine_name: str | None = None
    valve_drawing: str | None = None
    valve_id: int | None = None
    
    # ---------------------------------------------------------
    # Взаимоисключающие параметры: Температура ИЛИ Энтальпия
    # ---------------------------------------------------------
    temperature_start: float | None = None
    temperature_start_unit: str = "°C"
    
    enthalpy_start: float | None = None
    enthalpy_start_unit: str = "ккал/кг"
    
    # ---------------------------------------------------------
    # Остальные физические параметры
    # ---------------------------------------------------------
    t_air: float
    t_air_unit: str = "°C"
    
    count_valves: int
    
    p_ejector: list[float]
    p_ejector_unit: str = "кгс/см²"
    
    p_values: list[float]
    p_values_unit: str = "кгс/см²"

    @model_validator(mode='after')
    def check_temperature_and_enthalpy(self) -> "CalculationParams":
        """
        Валидатор проверяет, что указана либо температура, либо энтальпия.
        Любая выброшенная здесь ValueError автоматически превратится 
        FastAPI в красивую ошибку 422 Unprocessable Entity для фронтенда.
        """
        t_given = self.temperature_start is not None
        h_given = self.enthalpy_start is not None

        if t_given and h_given:
            raise ValueError(
                "Нельзя указывать одновременно температуру и энтальпию свежего пара. "
                "Оставьте одно из полей пустым (null)."
            )
            
        if not t_given and not h_given:
            raise ValueError(
                "Необходимо указать либо начальную температуру (temperature_start), "
                "либо начальную энтальпию (enthalpy_start)."
            )

        return self


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