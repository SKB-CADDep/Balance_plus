"""
Модуль для работы с базой данных (CRUD) конденсаторов.

Содержит функции для извлечения информации об оборудовании из БД.
Включает механизмы жадной загрузки (eager loading) связанных сущностей 
(материалов), чтобы предотвратить проблему N+1 запросов при сериализации 
результатов в Pydantic-схемы.
"""

import logging
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_

from app.models.condenser import Condenser
from app.core.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


def get_condenser_by_id(db: Session, condenser_id: int) -> Condenser:
    """
    Извлекает полную информацию о конденсаторе по его уникальному ID.

    Использует жадную загрузку (selectinload) для немедленного извлечения 
    связанных материалов труб из таблицы Many-to-Many. Это необходимо 
    для корректного заполнения поля `materials` в схеме CondenserDetail.

    Args:
        db (Session): Активная сессия подключения к базе данных.
        condenser_id (int): Уникальный идентификатор искомого аппарата.

    Returns:
        Condenser: ORM-объект конденсатора со всеми геометрическими и 
            связанными данными.

    Raises:
        EntityNotFoundError: Если аппарат с указанным `condenser_id` 
            отсутствует в базе данных.
    """
    logger.info("DB: loading condenser", extra={"condenser_id": condenser_id})
    
    # Использование selectinload предотвращает ленивую (lazy) загрузку материалов,
    # которая могла бы вызвать ошибку при доступе к condenser.materials вне сессии БД.
    condenser = db.query(Condenser)\
        .options(selectinload(Condenser.materials))\
        .filter(Condenser.id == condenser_id).first()
    
    if not condenser:
        logger.warning("DB: condenser not found", extra={"condenser_id": condenser_id})
        raise EntityNotFoundError(f"Condenser with id {condenser_id} not found.")
        
    return condenser


def search_condensers(
    db: Session, 
    search: str | None = None, 
    skip: int = 0, 
    limit: int = 100
) -> list[Condenser]:
    """
    Выполняет текстовый поиск аппаратов по названию или проекту.

    Использует регистронезависимый поиск (ILIKE) с подстановочными знаками (%).
    Поддерживает пагинацию для ограничения объема передаваемых данных.

    Args:
        db (Session): Активная сессия подключения к базе данных.
        search (str | None): Строка для поиска. Если None, поведение аналогично `get_condensers`.
        skip (int): Смещение (количество пропускаемых записей). По умолчанию 0.
        limit (int): Максимальное количество возвращаемых записей. По умолчанию 100.

    Returns:
        list[Condenser]: Список ORM-объектов конденсаторов, удовлетворяющих условиям поиска.
    """
    query = db.query(Condenser).options(selectinload(Condenser.materials))
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Condenser.name_condenser.ilike(search_term),
                # Примечание: выполняется текстовый поиск по полю project_id
                Condenser.project_id.ilike(search_term)
            )
        )
        
    return query.order_by(Condenser.name_condenser).offset(skip).limit(limit).all()


def get_condensers(db: Session, skip: int = 0, limit: int = 100) -> list[Condenser]:
    """
    Возвращает общий список всех конденсаторов из базы данных.

    Используется для формирования полных каталогов оборудования на фронтенде.
    Поддерживает пагинацию.

    Args:
        db (Session): Активная сессия подключения к базе данных.
        skip (int): Смещение для пагинации. По умолчанию 0.
        limit (int): Лимит количества записей в ответе. По умолчанию 100.

    Returns:
        list[Condenser]: Список ORM-объектов конденсаторов.
    """
    return db.query(Condenser)\
        .options(selectinload(Condenser.materials))\
        .offset(skip).limit(limit).all()