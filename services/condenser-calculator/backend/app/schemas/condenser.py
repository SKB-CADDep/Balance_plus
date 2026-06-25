
from pydantic import BaseModel, ConfigDict, Field


class CondenserBase(BaseModel):
    name_condenser: str = Field(..., description="Наименование конденсатора")
    project_name: str | None = Field(None, description="Название проекта")


class CondenserListItem(CondenserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CondenserDetail(CondenserBase):
    id: int
    diameter_internal: float
    wall_thickness: float
    main_length: float
    main_count: int
    builtin_length: float | None
    builtin_count: int | None
    aircooler_count: int | None
    passes_main: int
    passes_builtin: int | None
    ejectors_count: int
    mass_flow_steam_nom: float
    mass_flow_air: float
    water_flow_limits: dict | None

    model_config = ConfigDict(from_attributes=True)

CondenserShort = CondenserListItem
