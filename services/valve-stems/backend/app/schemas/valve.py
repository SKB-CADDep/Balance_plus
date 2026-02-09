from pydantic import BaseModel, ConfigDict, computed_field
from typing import List, Optional

class SimpleValveInfo(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class ValveCreate(BaseModel):
    name: str
    type: Optional[str] = None
    diameter: Optional[float] = None
    clearance: Optional[float] = None
    count_parts: Optional[int] = None
    len_part1: Optional[float] = None
    len_part2: Optional[float] = None
    len_part3: Optional[float] = None
    len_part4: Optional[float] = None
    len_part5: Optional[float] = None
    round_radius: Optional[float] = None
    turbine_id: Optional[int] = None

class ValveInfo(ValveCreate):
    """
    Наследуемся от ValveCreate, добавляя ID и вычисляемое поле.
    """
    id: Optional[int] = None

    @computed_field
    @property
    def section_lengths(self) -> List[Optional[float]]:
        return [
            self.len_part1,
            self.len_part2,
            self.len_part3,
            self.len_part4,
            self.len_part5
        ]

    model_config = ConfigDict(from_attributes=True)