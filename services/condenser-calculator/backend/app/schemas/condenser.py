# app/schemas/condenser.py

from pydantic import BaseModel, Field
from typing import Optional


class CondenserBase(BaseModel):
    name_condenser: str = Field(..., description="Наименование конденсатора")
    project_name: Optional[str] = Field(None, description="Название проекта")


class CondenserListItem(CondenserBase):
    id: int

    class Config:
        from_attributes = True


class CondenserDetail(CondenserBase):
    id: int
    diameter_internal: float
    wall_thickness: float
    main_length: float
    main_count: int
    builtin_length: Optional[float]
    builtin_count: Optional[int]
    aircooler_count: Optional[int]
    passes_main: int
    passes_builtin: Optional[int]
    ejectors_count: int
    mass_flow_steam_nom: float
    mass_flow_air: float
    water_flow_limits: Optional[dict]

    class Config:
        from_attributes = True