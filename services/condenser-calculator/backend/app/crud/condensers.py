import logging

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFoundError
from app.models.condenser import Condenser

logger = logging.getLogger(__name__)


def get_condenser_by_id(db: Session, condenser_id: int) -> Condenser:
    """Получает конденсатор по ID. Выбрасывает ошибку, если не найден."""
    logger.info("DB: loading condenser", extra={"condenser_id": condenser_id})

    condenser = db.query(Condenser).filter(Condenser.id == condenser_id).first()

    if not condenser:
        logger.warning("DB: condenser not found", extra={"condenser_id": condenser_id})
        raise EntityNotFoundError(f"Condenser with id {condenser_id} not found.")

    return condenser


def search_condensers(
    db: Session, search: str | None = None, skip: int = 0, limit: int = 100
) -> list[Condenser]:
    """Ищет конденсаторы по имени или проекту (case-insensitive) с пагинацией."""
    query = db.query(Condenser)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Condenser.name_condenser.ilike(search_term),
                Condenser.project_name.ilike(search_term),
            )
        )

    return query.order_by(Condenser.name_condenser).offset(skip).limit(limit).all()


def get_condensers(db: Session, skip: int = 0, limit: int = 100) -> list[Condenser]:
    """Возвращает список всех конденсаторов с пагинацией."""
    return db.query(Condenser).offset(skip).limit(limit).all()
