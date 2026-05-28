from pydantic import ConfigDict, BaseModel, Field
from typing import Optional, List

# Импортируем схему материала (путь может немного отличаться в зависимости от твоей структуры)
from app.schemas.material import MaterialShort


class CondenserBase(BaseModel):
    name_condenser: str = Field(..., description="Наименование конденсатора")
    project_name: Optional[str] = Field(None, description="Название проекта")


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
    builtin_length: Optional[float]
    builtin_count: Optional[int]
    aircooler_count: Optional[int]
    passes_main: int
    passes_builtin: Optional[int]
    ejectors_count: int
    mass_flow_steam_nom: float
    mass_flow_air: float
    water_flow_limits: Optional[dict]

    model_config = ConfigDict(from_attributes=True)


CondenserShort = CondenserListItem