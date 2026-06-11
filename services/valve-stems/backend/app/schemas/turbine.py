"""
Схемы данных Pydantic для турбин (Turbine Schemas).

Описывают структуру объектов, возвращаемых эндпоинтами справочника турбин.
Включают в себя как базовую информацию о турбине, так и расширенные DTO 
с вложенными массивами клапанов (штоков).
"""

from pydantic import BaseModel, ConfigDict

from .valve import SimpleValveInfo, ValveInfo


class TurbineInfo(BaseModel):
    """Базовая схема с информацией о турбине."""
    id: int
    name: str
    station_name: str | None = None
    station_number: str | None = None
    factory_number: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TurbineWithValvesInfo(TurbineInfo):
    """
    Расширенная схема турбины, включающая список привязанных к ней клапанов.
    Используется в основном для поиска по каталогу.
    """
    valves: list[SimpleValveInfo] = []
    
    # Полезно знать, нашли ли мы эту турбину через конкретный клапан
    # (заполняется динамически на уровне API, если поиск шел по чертежу клапана)
    matched_valve_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class TurbineValves(BaseModel):
    """
    Схема-обертка (Wrapper) для отдачи списка клапанов конкретной турбины.
    Помимо самого массива, возвращает общее количество (count).
    """
    count: int
    valves: list[ValveInfo]
    
    model_config = ConfigDict(from_attributes=True)
    