import logging
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_

from app.models import Turbine, Valve
from app.schemas import TurbineValves, ValveInfo

logger = logging.getLogger(__name__)

def search_turbines(
    db: Session, 
    query: Optional[str] = None, 
    station: Optional[str] = None,
    factory_num: Optional[str] = None,
    valve_drawing: Optional[str] = None
) -> List[Turbine]:
    try:
        sql_query = db.query(Turbine).options(joinedload(Turbine.valves))
        filters = []

        if query: filters.append(Turbine.name.ilike(f"%{query}%"))
        if station: filters.append(Turbine.station_name.ilike(f"%{station}%"))
        if factory_num: filters.append(Turbine.factory_number.ilike(f"%{factory_num}%"))
        if valve_drawing:
            sql_query = sql_query.join(Turbine.valves).filter(Valve.name.ilike(f"%{valve_drawing}%"))
        
        if filters:
            sql_query = sql_query.filter(and_(*filters))
            
        return sql_query.all()
    except Exception as e:
        logger.error(f"Ошибка поиска турбин: {e!s}")
        return []

def get_turbine_by_id(db: Session, turbine_id: int) -> Turbine | None:
    return db.query(Turbine).filter(Turbine.id == turbine_id).first()

# Новая функция для нашего обновленного поиска фронтенда
def get_valves_by_turbine_id(db: Session, turbine_id: int) -> TurbineValves | None:
    try:
        turbine = db.query(Turbine).filter(Turbine.id == turbine_id).first()
        if not turbine:
            return None
        
        valves = turbine.valves
        valve_info_list = [ValveInfo.model_validate(v) for v in valves]

        return TurbineValves(
            count=len(valve_info_list),
            valves=valve_info_list
        )
    except Exception as e:
        logger.error(f"Ошибка БД при получении клапанов по ID: {e!s}")
        return None

# СТАРАЯ функция для обратной совместимости (чтобы не сломать calculations.py)
def get_valves_by_turbine(db: Session, turbine_name: str) -> TurbineValves | None:
    try:
        turbine = db.query(Turbine).filter(Turbine.name == turbine_name).first()
        if not turbine:
            return None
        
        valves = turbine.valves
        valve_info_list = [ValveInfo.model_validate(v) for v in valves]

        return TurbineValves(
            count=len(valve_info_list),
            valves=valve_info_list
        )
    except Exception as e:
        logger.error(f"Ошибка базы данных при получении клапанов по турбине: {e!s}")
        raise