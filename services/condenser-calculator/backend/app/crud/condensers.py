import logging
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.condenser import Condenser
from app.core.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


def get_condenser_by_id(db: Session, condenser_id: int) -> Condenser:
    """Получает конденсатор по ID. Выбрасывает ошибку, если не найден."""
    logger.info("DB: loading condenser", extra={"condenser_id": condenser_id})
    
    condenser = db.query(Condenser).filter(Condenser.id == condenser_id).first()
    
    if not condenser:
        logger.warning("DB: condenser not found", extra={"condenser_id": condenser_id})
        raise EntityNotFoundError(f"Condenser with id {condenser_id} not found.")
        
    return condenser


def search_condensers(db: Session, search: str | None = None) -> list[Condenser]:
    """Ищет конденсаторы по имени или проекту (case-insensitive)."""
    query = db.query(Condenser)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Condenser.name_condenser.ilike(search_term),
                Condenser.project_name.ilike(search_term)
            )
        )
        
    return query.all()


def get_condensers(db: Session) -> list[Condenser]:
    """Возвращает список всех конденсаторов."""
    return db.query(Condenser).all()