from pydantic import ConfigDict, BaseModel, Field
from typing import Optional, List

# Импортируем схему материала (путь может немного отличаться в зависимости от твоей структуры)
from app.schemas.material import MaterialShort


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

    # --- НОВОЕ ПОЛЕ: Список доступных материалов ---
    materials: List[MaterialShort] = Field(default_factory=list, description="Список доступных материалов для данного аппарата")

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
