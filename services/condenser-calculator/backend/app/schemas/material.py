
from pydantic import BaseModel, ConfigDict, Field


class MaterialListItem(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MaterialDetail(BaseModel):
    id: int
    name: str
    thermal_conductivity_points: list[list[float]] = Field(
        description="Список точек [[t, λ], ...]"
    )

    model_config = ConfigDict(from_attributes=True)

MaterialShort = MaterialListItem
