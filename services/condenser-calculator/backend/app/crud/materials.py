import logging

from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFoundError
from app.models.material import Material

logger = logging.getLogger(__name__)


def get_materials(db: Session, skip: int = 0, limit: int = 100) -> list[Material]:
    """Возвращает список всех материалов, отсортированный по имени, с пагинацией."""
    return db.query(Material).order_by(Material.name).offset(skip).limit(limit).all()


def get_material_by_id(db: Session, material_id: int) -> Material:
    """Получает материал по ID. Выбрасывает ошибку, если не найден."""
    logger.info("DB: loading material", extra={"material_id": material_id})

    material = db.query(Material).filter(Material.id == material_id).first()

    if not material:
        logger.warning("DB: material not found", extra={"material_id": material_id})
        raise EntityNotFoundError(f"Material with id {material_id} not found.")

    return material


def get_material_by_uuid(db: Session, material_uuid: str) -> Material:
    """Получает материал по UUID. Выбрасывает ошибку, если не найден."""
    logger.info("DB: loading material by uuid", extra={"material_uuid": material_uuid})

    material = db.query(Material).filter(Material.uuid == material_uuid).first()

    if not material:
        logger.warning(
            "DB: material not found by uuid", extra={"material_uuid": material_uuid}
        )
        raise EntityNotFoundError(f"Material with uuid {material_uuid} not found.")

    return material
