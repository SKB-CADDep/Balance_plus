from pydantic import BaseModel, ConfigDict
from typing import Optional

from .valve import SimpleValveInfo, ValveInfo


class TurbineInfo(BaseModel):
    id: int
    name: str
    station_name: Optional[str] = None
    station_number: Optional[str] = None
    factory_number: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class TurbineWithValvesInfo(TurbineInfo):
    valves: list[SimpleValveInfo] = []
    # Полезно знать, нашли ли мы эту турбину через конкретный клапан
    matched_valve_id: Optional[int] = None 
    
    model_config = ConfigDict(from_attributes=True)

class TurbineValves(BaseModel):
    count: int
    valves: list[ValveInfo]
    model_config = ConfigDict(from_attributes=True)
