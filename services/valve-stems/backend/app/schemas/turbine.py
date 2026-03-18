
from pydantic import BaseModel, ConfigDict

from .valve import SimpleValveInfo, ValveInfo


class TurbineInfo(BaseModel):
    id: int
    name: str
    station_name: str | None = None
    station_number: str | None = None
    factory_number: str | None = None

    model_config = ConfigDict(from_attributes=True)

class TurbineWithValvesInfo(TurbineInfo):
    valves: list[SimpleValveInfo] = []
    # Полезно знать, нашли ли мы эту турбину через конкретный клапан
    matched_valve_id: int | None = None

    model_config = ConfigDict(from_attributes=True)

class TurbineValves(BaseModel):
    count: int
    valves: list[ValveInfo]
    model_config = ConfigDict(from_attributes=True)
