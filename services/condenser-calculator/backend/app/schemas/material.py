from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import List


class MaterialListItem(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MaterialDetail(BaseModel):
    id: int
    name: str
    thermal_conductivity_points: List[List[float]] = Field(
        description="Список точек [[t, λ], ...]"
    )

    model_config = ConfigDict(from_attributes=True)

MaterialShort = MaterialListItem