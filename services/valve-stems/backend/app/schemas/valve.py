"""
Схемы данных Pydantic для клапанов/штоков (Valve Schemas).

Описывают структуру объектов (создание, чтение) для справочника геометрии
клапанов. Обеспечивают удобный интерфейс работы с участками штоков.
"""

from pydantic import BaseModel, ConfigDict, computed_field


class SimpleValveInfo(BaseModel):
    """
    Облегченная (Short) схема клапана. 
    Используется во вложенных структурах (например, в TurbineWithValvesInfo),
    чтобы не перегружать JSON тяжелой геометрией.
    """
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ValveCreate(BaseModel):
    """
    Схема для создания нового клапана.
    Включает все геометрические параметры, необходимые для расчетов.
    """
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
    Полная схема клапана (чтение из БД).
    Наследуется от ValveCreate, добавляя внутренний ID и 
    динамически вычисляемое поле section_lengths.
    """
    id: int | None = None

    @computed_field
    @property
    def section_lengths(self) -> list[float | None]:
        """
        Динамически собирает 5 плоских полей длин в один массив.
        Автоматически попадает в итоговый JSON (удобно для фронтенда и расчетов).
        """
        return [
            self.len_part1,
            self.len_part2,
            self.len_part3,
            self.len_part4,
            self.len_part5,
        ]

    model_config = ConfigDict(from_attributes=True)
    