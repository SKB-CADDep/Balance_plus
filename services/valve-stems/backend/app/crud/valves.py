import logging
from sqlalchemy.orm import Session
from app.models import Valve
from app.core.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


def get_valve_by_id(db: Session, valve_id: int) -> Valve:
    """
    Получает один клапан (шток) по его ID.
    Если не найден - выбрасывает EntityNotFoundError.
    """
    valve = db.query(Valve).filter(Valve.id == valve_id).first()
    if not valve:
        raise EntityNotFoundError(entity_name="Клапан (шток)", entity_id=valve_id)
    return valve


def get_valve_by_drawing(db: Session, valve_drawing: str) -> Valve:
    """
    Получает клапан по его чертежному номеру (имени).
    Если не найден - выбрасывает EntityNotFoundError.
    """
    valve = db.query(Valve).filter(Valve.name == valve_drawing).first()
    if not valve:
        raise EntityNotFoundError(
            entity_name="Клапан (шток) по чертежу", entity_id=valve_drawing
        )
    return valve
