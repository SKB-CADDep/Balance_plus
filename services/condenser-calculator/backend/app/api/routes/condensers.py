from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.crud.condensers import get_condenser_by_id, get_condensers, search_condensers
from app.dependencies import get_db
from app.models.condenser import Condenser
from app.schemas.condenser import CondenserDetail, CondenserShort

router = APIRouter(tags=["Condensers"])


@router.get(
    "/condensers",
    response_model=list[CondenserShort],
    summary="Список конденсаторов",
)
async def list_condensers(
    search: str | None = Query(None, description="Поиск по названию или проекту"),
    db: Session = Depends(get_db),
) -> list[Condenser]:
    if search:
        return search_condensers(db, search)
    return get_condensers(db)


@router.get(
    "/condensers/{condenser_id}",
    response_model=CondenserDetail,
    summary="Получить конденсатор по ID",
)
async def get_condenser(condenser_id: int, db: Session = Depends(get_db)) -> Condenser:
    return get_condenser_by_id(db, condenser_id)
