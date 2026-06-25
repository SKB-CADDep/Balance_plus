from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.materials import get_materials
from app.dependencies import get_db
from app.schemas.material import MaterialShort

router = APIRouter(tags=["Materials"])


@router.get(
    "/materials",
    response_model=list[MaterialShort],
    summary="Список материалов",
)
async def list_materials(db: Session = Depends(get_db)):
    return get_materials(db)
