from pydantic import BaseModel, ConfigDict
from typing import List
# Теперь можно смело импортировать, т.к. valve.py не импортирует turbine.py
from .valve import SimpleValveInfo, ValveInfo 

class TurbineInfo(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class TurbineWithValvesInfo(BaseModel):
    id: int
    name: str
    valves: List[SimpleValveInfo] = []
    model_config = ConfigDict(from_attributes=True)

class TurbineValves(BaseModel):
    count: int
    valves: List[ValveInfo]
    model_config = ConfigDict(from_attributes=True)