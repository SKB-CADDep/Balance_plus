from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
import re


class ProjectBase(BaseModel):
    station_name: str = Field(min_length=1, description="Название станции")
    factory_number: str = Field(..., description="Заводской номер")
    station_number: Optional[str] = None
    turbine_id: int

    @field_validator("factory_number")
    @classmethod
    def validate_factory_no(cls, v: str) -> str:
        """Проверка: не более 10 символов (расширил, т.к. бывают буквы)"""
        if len(v) > 10:
            raise ValueError("Длина заводского номера не может превышать 10 символов")
        return v

    @field_validator("station_number")
    @classmethod
    def validate_station_no(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 5:
            raise ValueError("Длина станционного номера не может превышать 5 символов")
        return v


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: int
    # turbine_name можно подтянуть, если использовать ORM mode и связь
    # turbine_name: str

    model_config = ConfigDict(from_attributes=True)