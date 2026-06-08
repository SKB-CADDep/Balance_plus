"""
Модуль для работы с базой данных (CRUD) справочника материалов.

Обеспечивает доступ к теплофизическим свойствам материалов трубок 
(например, массивам теплопроводности), а также управляет связями 
материалов с конкретными моделями конденсаторов.
"""

import logging
from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.condenser import Condenser
from app.core.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


def get_materials(db: Session, skip: int = 0, limit: int = 100) -> list[Material]:
    """
    Извлекает полный список доступных материалов из базы данных.

    Данные автоматически сортируются по алфавиту (по названию материала) 
    для корректного отображения в выпадающих списках на фронтенде.

    Args:
        db (Session): Активная сессия базы данных.
        skip (int): Смещение для пагинации. По умолчанию 0.
        limit (int): Максимальное количество записей в ответе. По умолчанию 100.

    Returns:
        list[Material]: Список ORM-объектов материалов.
    """
    return db.query(Material).order_by(Material.name).offset(skip).limit(limit).all()


def get_material_by_id(db: Session, material_id: int) -> Material:
    """
    Ищет конкретный материал по его внутреннему целочисленному ID.

    Используется преимущественно при выполнении расчетов, когда ID материала 
    передается от фронтенда или извлекается из настроек конденсатора по умолчанию.

    Args:
        db (Session): Активная сессия базы данных.
        material_id (int): Внутренний идентификатор материала в таблице БД.

    Returns:
        Material: ORM-объект найденного материала.

    Raises:
        EntityNotFoundError: Если материал с указанным ID не существует.
    """
    logger.info("DB: loading material", extra={"material_id": material_id})
    
    material = db.query(Material).filter(Material.id == material_id).first()
    
    if not material:
        logger.warning("DB: material not found", extra={"material_id": material_id})
        raise EntityNotFoundError(f"Material with id {material_id} not found.")
        
    return material


def get_material_by_uuid(db: Session, material_uuid: str) -> Material:
    """
    Ищет материал по его глобальному уникальному идентификатору (UUID).

    В микросервисной архитектуре поиск по UUID часто используется для 
    синхронизации справочников между разными системами (например, внешним PDM/PLM), 
    где внутренние автоинкрементные ID могут не совпадать.

    Args:
        db (Session): Активная сессия базы данных.
        material_uuid (str): Строковое представление UUID материала.

    Returns:
        Material: ORM-объект найденного материала.

    Raises:
        EntityNotFoundError: Если материал с указанным UUID не существует.
    """
    logger.info("DB: loading material by uuid", extra={"material_uuid": material_uuid})
    
    material = db.query(Material).filter(Material.material_uuid == material_uuid).first()
    
    if not material:
        logger.warning("DB: material not found by uuid", extra={"material_uuid": material_uuid})
        raise EntityNotFoundError(f"Material with uuid {material_uuid} not found.")
        
    return material


def get_materials_by_condenser(db: Session, condenser_id: int) -> list[Material]:
    """
    Извлекает список материалов, совместимых с конкретным конденсатором.

    Опирается на связь 'Many-to-Many' (многие-ко-многим) между таблицами 
    конденсаторов и материалов. Сначала проверяет существование самого аппарата, 
    а затем лениво (lazy load) подгружает связанные материалы.

    Args:
        db (Session): Активная сессия базы данных.
        condenser_id (int): Идентификатор конденсатора.

    Returns:
        list[Material]: Список материалов, разрешенных для данного аппарата.

    Raises:
        EntityNotFoundError: Если запрошенный конденсатор не найден в БД.
    """
    condenser = db.query(Condenser).filter(Condenser.id == condenser_id).first()
    
    if not condenser:
        raise EntityNotFoundError(f"Condenser with id {condenser_id} not found.")
        
    # Обращение к атрибуту `.materials` автоматически генерирует скрытый SQL-запрос 
    # в промежуточную таблицу связей благодаря настройкам relationship в SQLAlchemy.
    return condenser.materials