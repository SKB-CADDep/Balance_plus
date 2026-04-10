import logging
from sqlalchemy.orm import Session

from app.models.material import Material
from app.core.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


def get_materials(db: Session) -> list[Material]:
    """Возвращает список всех материалов, отсортированный по имени."""
    return db.query(Material).order_by(Material.name).all()


def get_material_by_id(db: Session, material_id: int) -> Material:
    """Получает материал по ID. Выбрасывает ошибку, если не найден."""
    logger.info("DB: loading material", extra={"material_id": material_id})
    
    material = db.query(Material).filter(Material.id == material_id).first()
    
    if not material:
        logger.warning("DB: material not found", extra={"material_id": material_id})
        raise EntityNotFoundError(f"Material with id {material_id} not found.")
        
    return material


def get_material_by_uuid(db: Session, material_uuid: str) -> Material | None:
    """Получает материал по UUID. Если не найден - возвращает None."""
    logger.info("DB: loading material by uuid", extra={"material_uuid": material_uuid})
    return db.query(Material).filter(Material.uuid == material_uuid).first()