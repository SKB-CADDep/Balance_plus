# schemas/geometry.py
from pydantic import BaseModel
from typing import Optional


class GeometryInfo(BaseModel):
    """Краткая информация о геометрии (для списка)"""
    id: str
    name: str
    type: str
    description: Optional[str] = None
    file: str


class GeometriesManifest(BaseModel):
    """Манифест со списком всех геометрий"""
    schema_version: str
    geometries: list[GeometryInfo]


class Dimension(BaseModel):
    value: float
    unit: str


class CondenserDimensions(BaseModel):
    length: Dimension
    diameter: Dimension
    tube_count: int
    tube_diameter: Dimension


class CondenserMaterials(BaseModel):
    shell: str
    tubes: str


class CondenserGeometry(BaseModel):
    """Полная геометрия конденсатора"""
    id: str
    type: str
    version: str
    dimensions: CondenserDimensions
    materials: CondenserMaterials