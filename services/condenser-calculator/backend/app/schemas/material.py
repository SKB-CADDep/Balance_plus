from pydantic import BaseModel, Field
from typing import Optional, List


class MaterialListItem(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MaterialDetail(BaseModel):
    id: int
    name: str
    thermal_conductivity_points: List[List[float]] = Field(
        description="Список точек [[t, λ], ...]"
    )

    class Config:
        from_attributes = True
