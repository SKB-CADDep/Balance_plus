import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Turbine
from app.schemas import TurbineValves, ValveInfo


logger = logging.getLogger(__name__)

def get_turbine_by_id(db: Session, turbine_id: int) -> Turbine | None:
    """
    Получает одну турбину по ее ID.
    """
    try:
        turbine = db.query(Turbine).filter(Turbine.id == turbine_id).first()
        return turbine
    except Exception as e:
        logger.error(f"Ошибка базы данных при получении турбины по ID {turbine_id}: {e!s}")
        return None

def get_valves_by_turbine(db: Session, turbine_name: str) -> TurbineValves | None:
    """
    Получает список клапанов для заданной турбины.
    """
    try:
        turbine = db.query(Turbine).filter(Turbine.name == turbine_name).first()

        if not turbine:
            return None

        # Получаем клапаны
        valves = turbine.valves

        # Создаем список ValveInfo объектов
        valve_info_list = []
        for valve in valves:
            # Pydantic v2 from_attributes делает это автоматически, но оставим явное создание как было
            valve_info = ValveInfo.model_validate(valve)
            valve_info_list.append(valve_info)

        return TurbineValves(
            count=len(valve_info_list),
            valves=valve_info_list
        )
    except Exception as e:
        logger.error(f"Ошибка базы данных при получении клапанов по турбине: {e!s}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось получить клапаны: {e}")
