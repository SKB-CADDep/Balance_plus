from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.crud.materials import (
    get_materials, 
    get_materials_by_condenser
)
from app.dependencies import get_db
from app.schemas.material import MaterialShort

router = APIRouter(tags=["Materials"])


@router.get(
    "/materials",
    response_model=list[MaterialShort],
    summary="Список всех материалов в базе",
)
async def list_materials(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_materials(db, skip=skip, limit=limit)


@router.get(
    "/condensers/{condenser_id}/materials",
    response_model=list[MaterialShort],
    summary="Список материалов для конкретного конденсатора",
)
async def list_condenser_materials(
    condenser_id: int = Path(..., description="ID конденсатора"), 
    db: Session = Depends(get_db)
):
    """
    Возвращает только те материалы, из которых может быть изготовлен выбранный конденсатор.
    """
    return get_materials_by_condenser(db, condenser_id)