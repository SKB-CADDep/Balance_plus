import logging

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app import dependencies
from app.crud import turbines as crud_turbines
from app.crud import get_turbine_by_id
from app.dependencies import get_db
from app.models import Turbine
from app.schemas import TurbineInfo, TurbineValves, TurbineWithValvesInfo


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/search", response_model=List[TurbineWithValvesInfo])
def search_turbines(
    q: Optional[str] = None, # Марка турбины
    station: Optional[str] = None,
    factory: Optional[str] = None,
    valve: Optional[str] = None,
    db: Session = Depends(dependencies.get_db),
) -> Any:
    """
    Поиск проектов по множеству критериев.
    """
    results = crud_turbines.search_turbines(
        db, query=q, station=station, factory_num=factory, valve_drawing=valve
    )
    
    # Собираем ответ
    response = []
    for t in results:
        t_info = TurbineWithValvesInfo.model_validate(t)
        response.append(t_info)
    
    return response

@router.get("/{turbine_id}/valves/", response_model=TurbineValves)
def get_valves_by_turbine(
    turbine_id: int,
    db: Session = Depends(dependencies.get_db),
) -> Any:
    valves = crud_turbines.get_valves_by_turbine_id(db, turbine_id=turbine_id)
    if not valves:
        raise HTTPException(status_code=404, detail="Турбина или клапаны не найдены")
    return valves

@router.get("/", response_model=list[TurbineWithValvesInfo], summary="Получить все турбины с клапанами")
async def get_all_turbines_with_valves(db: Session = Depends(get_db)):
    """
    Получить список всех турбин вместе с их клапанами.
    """
    try:
        turbines_from_db = db.query(Turbine).options(
            selectinload(Turbine.valves)
        ).all()
        return turbines_from_db
    except Exception as e:
        logger.error(f"Ошибка при получении всех турбин с клапанами: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось получить турбины: {e}")

@router.post("", response_model=TurbineInfo, status_code=status.HTTP_201_CREATED, summary="Создать турбину")
async def create_turbine(turbine: TurbineInfo, db: Session = Depends(get_db)):
    try:
        db_turbine = Turbine(name=turbine.name)
        db.add(db_turbine)
        db.commit()
        db.refresh(db_turbine)
        return db_turbine
    except Exception as e:
        logger.error(f"Ошибка при создании турбины: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось создать турбину: {e}")

@router.get("/{turbine_id}", response_model=TurbineInfo, summary="Получить турбину по ID")
async def read_turbine_by_id(turbine_id: int, db: Session = Depends(get_db)):
    db_turbine = get_turbine_by_id(db, turbine_id=turbine_id)
    if db_turbine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Турбина не найдена")
    return db_turbine

@router.delete("/{turbine_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить турбину")
async def delete_turbine(turbine_id: int, db: Session = Depends(get_db)):
    try:
        db_turbine = db.query(Turbine).filter(Turbine.id == turbine_id).first()
        if db_turbine is None:
            raise HTTPException(status_code=404, detail="Турбина не найдена")
        db.delete(db_turbine)
        db.commit()
        return {"message": f"Турбина '{db_turbine.name}' успешно удалена"}
    except Exception as e:
        logger.error(f"Ошибка при удалении турбины: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось удалить турбину: {e}")
