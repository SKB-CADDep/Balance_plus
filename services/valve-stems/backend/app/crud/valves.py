from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import Valve
import logging

logger = logging.getLogger(__name__)

def get_valve_by_id(db: Session, valve_id: int) -> Optional[Valve]:
    """
    Получает один клапан (шток) по его ID.
    """
    try:
        valve = db.query(Valve).filter(Valve.id == valve_id).first()
        return valve
    except Exception as e:
        logger.error(f"Ошибка базы данных при получении клапана по ID {valve_id}: {str(e)}")
        return None

def get_valve_by_drawing(db: Session, valve_drawing: str) -> Optional[Valve]:
    """
    Получает клапан по его чертежному номеру (имени).
    """
    try:
        # В модели Valve поле называется 'name', но в контексте чертежа это оно и есть
        valve = db.query(Valve).filter(Valve.name == valve_drawing).first()
        return valve
    except Exception as e:
        logger.error(f"Ошибка БД при поиске клапана по чертежу {valve_drawing}: {str(e)}")
        return None
