
from pydantic import BaseModel, ConfigDict, computed_field


class SimpleValveInfo(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class ValveCreate(BaseModel):
    name: str
    type: str | None = None
    diameter: float | None = None
    clearance: float | None = None
    count_parts: int | None = None
    len_part1: float | None = None
    len_part2: float | None = None
    len_part3: float | None = None
    len_part4: float | None = None
    len_part5: float | None = None
    round_radius: float | None = None
    turbine_id: int | None = None

class ValveInfo(ValveCreate):
    """
    Наследуемся от ValveCreate, добавляя ID и вычисляемое поле.
    """
    id: int | None = None

    @computed_field
    @property
    def section_lengths(self) -> list[float | None]:
        return [
            self.len_part1,
            self.len_part2,
            self.len_part3,
            self.len_part4,
            self.len_part5
        ]

    model_config = ConfigDict(from_attributes=True)
