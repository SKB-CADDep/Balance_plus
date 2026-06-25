"""
Репозиторий доступа к данным клапанов/штоков (Valves).

Предоставляет базовые операции (Read) для извлечения параметров
оборудования из базы данных PostgreSQL по внутренним идентификаторам
или чертежным номерам.
"""

import logging

from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFoundError
from app.models import Valve

logger = logging.getLogger(__name__)


def get_valve_by_id(db: Session, valve_id: int) -> Valve:
    """
    Получает один клапан (шток) по его внутреннему ID в базе данных.
    
    Raises:
        EntityNotFoundError: Если клапан с указанным ID не существует.
    """
    # WARNING (Технический долг):
    # В SQLAlchemy 2.0 рекомендуется использовать db.execute(select(Valve)...).scalars().first()
    # вместо устаревшего метода db.query().
    valve = db.query(Valve).filter(Valve.id == valve_id).first()
    if not valve:
        raise EntityNotFoundError(entity_name="Клапан (шток)", entity_id=valve_id)
    return valve


def get_valve_by_drawing(db: Session, valve_drawing: str) -> Valve:
    """
    Получает клапан (шток) по его чертежному номеру (строковому имени).
    
    Raises:
        EntityNotFoundError: Если клапан с указанным чертежом не найден.
    """
    valve = db.query(Valve).filter(Valve.name == valve_drawing).first()
    if not valve:
        raise EntityNotFoundError(
            entity_name="Клапан (шток) по чертежу", 
            entity_id=valve_drawing
        )
    return valve
    