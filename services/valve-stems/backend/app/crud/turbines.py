import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Turbine
from app.schemas import TurbineValves, ValveInfo


logger = logging.getLogger(__name__)

def get_turbine_by_id(db: Session, turbine_id: int) -> Turbine | None:
    return db.query(Turbine).filter(Turbine.id == turbine_id).first()

def search_turbines(
    db: Session, 
    query: Optional[str] = None, 
    station: Optional[str] = None,
    factory_num: Optional[str] = None,
    valve_drawing: Optional[str] = None
) -> List[Turbine]:
    """
    Универсальный поиск проектов.
    """
    try:
        sql_query = db.query(Turbine).options(joinedload(Turbine.valves))

        filters = []

        # Фильтр по названию турбины (марке)
        if query:
            filters.append(Turbine.name.ilike(f"%{query}%"))
        
        # Фильтр по станции
        if station:
            filters.append(Turbine.station_name.ilike(f"%{station}%"))

        # Фильтр по заводскому номеру
        if factory_num:
            filters.append(Turbine.factory_number.ilike(f"%{factory_num}%"))

        # Самый интересный фильтр: поиск по чертежу клапана
        if valve_drawing:
            # Находим турбины, у которых есть клапан с таким именем
            sql_query = sql_query.join(Turbine.valves).filter(Valve.name.ilike(f"%{valve_drawing}%"))
        
        if filters:
            sql_query = sql_query.filter(and_(*filters))
            
        return sql_query.all()

    except Exception as e:
        logger.error(f"Ошибка поиска турбин: {e!s}")
        return []

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
        logger.error(f"Ошибка получения клапанов: {e}")
        return None
