import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session, selectinload

from app import dependencies
from app.crud import get_turbine_by_id
from app.crud import turbines as crud_turbines
from app.dependencies import get_db
from app.models import Turbine
from app.schemas import TurbineInfo, TurbineValves, TurbineWithValvesInfo

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/search", response_model=list[TurbineWithValvesInfo])
def search_turbines(
    q: str | None = None,
    station: str | None = None,
    factory: str | None = None,
    valve: str | None = None,
    db: Session = Depends(dependencies.get_db),
) -> Any:
    results = crud_turbines.search_turbines(
        db, query=q, station=station, factory_num=factory, valve_drawing=valve
    )
    return [TurbineWithValvesInfo.model_validate(t) for t in results]


@router.get("/{turbine_id}/valves/", response_model=TurbineValves)
def get_valves_by_turbine(
    turbine_id: int, db: Session = Depends(dependencies.get_db)
) -> Any:
    return crud_turbines.get_valves_by_turbine_id(db, turbine_id=turbine_id)


@router.get(
    "/",
    response_model=list[TurbineWithValvesInfo],
    summary="Получить все турбины с клапанами",
)
async def get_all_turbines_with_valves(db: Session = Depends(get_db)):
    return db.query(Turbine).options(selectinload(Turbine.valves)).all()


@router.post(
    "",
    response_model=TurbineInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Создать турбину",
)
async def create_turbine(turbine: TurbineInfo, db: Session = Depends(get_db)):
    db_turbine = Turbine(name=turbine.name)
    db.add(db_turbine)
    db.commit()
    db.refresh(db_turbine)
    return db_turbine


@router.get(
    "/{turbine_id}", response_model=TurbineInfo, summary="Получить турбину по ID"
)
async def read_turbine_by_id(turbine_id: int, db: Session = Depends(get_db)):
    return get_turbine_by_id(db, turbine_id=turbine_id)


@router.delete(
    "/{turbine_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить турбину"
)
async def delete_turbine(turbine_id: int, db: Session = Depends(get_db)):
    db_turbine = get_turbine_by_id(db, turbine_id=turbine_id)
    db.delete(db_turbine)
    db.commit()
    return {"message": f"Турбина '{db_turbine.name}' успешно удалена"}
