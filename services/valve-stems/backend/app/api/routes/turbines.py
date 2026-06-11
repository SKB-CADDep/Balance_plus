"""
API-маршрутизатор для управления справочником турбин (Turbines).

Предоставляет эндпоинты для поиска, создания, извлечения и удаления турбин,
а также для получения связанных с ними клапанов (штоков).
"""

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

# Добавлен тег для группировки эндпоинтов в Swagger UI
router = APIRouter(tags=["Turbines"])
logger = logging.getLogger(__name__)


@router.get("/search", response_model=list[TurbineWithValvesInfo], summary="Поиск турбин")
def search_turbines(
    q: str | None = None,
    station: str | None = None,
    factory: str | None = None,
    valve: str | None = None,
    db: Session = Depends(dependencies.get_db),
) -> Any:
    """
    Комплексный поиск по справочнику турбин.
    Позволяет фильтровать по названию, станции, заводскому номеру
    и связанным клапанам.
    """
    results = crud_turbines.search_turbines(
        db, query=q, station=station, factory_num=factory, valve_drawing=valve
    )
    return [TurbineWithValvesInfo.model_validate(t) for t in results]


@router.get("/{turbine_id}/valves/", response_model=TurbineValves, summary="Получить клапаны турбины")
def get_valves_by_turbine(
    turbine_id: int, db: Session = Depends(dependencies.get_db)
) -> Any:
    """Извлекает список всех клапанов, привязанных к конкретной турбине."""
    return crud_turbines.get_valves_by_turbine_id(db, turbine_id=turbine_id)


@router.get(
    "/",
    response_model=list[TurbineWithValvesInfo],
    summary="Получить все турбины с клапанами",
)
async def get_all_turbines_with_valves(db: Session = Depends(get_db)):
    """Возвращает полный список турбин вместе с их дочерними клапанами."""
    # Использование selectinload - отличная практика для предотвращения N+1 запросов
    return db.query(Turbine).options(selectinload(Turbine.valves)).all()


# WARNING (Технический долг):
# Как и в valves.py, логика изменения БД (db.add, db.commit) написана в роутере,
# а не вынесена в отдельный CRUD-слой.
@router.post(
    "/",
    response_model=TurbineInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Создать турбину",
)
async def create_turbine(turbine: TurbineInfo, db: Session = Depends(get_db)):
    """Добавляет новую турбину в базу данных."""
    db_turbine = Turbine(name=turbine.name)
    db.add(db_turbine)
    db.commit()
    db.refresh(db_turbine)
    return db_turbine


@router.get(
    "/{turbine_id}", response_model=TurbineInfo, summary="Получить турбину по ID"
)
async def read_turbine_by_id(turbine_id: int, db: Session = Depends(get_db)):
    """Получает детальную информацию о турбине по её ID."""
    return get_turbine_by_id(db, turbine_id=turbine_id)


@router.delete(
    "/{turbine_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить турбину"
)
async def delete_turbine(turbine_id: int, db: Session = Depends(get_db)):
    """Удаляет турбину из базы данных."""
    db_turbine = get_turbine_by_id(db, turbine_id=turbine_id)
    db.delete(db_turbine)
    db.commit()
    
    # WARNING (Архитектурный баг):
    # Указан status_code=204 (No Content), но функция возвращает JSON-словарь.
    # FastAPI (в соответствии со стандартами HTTP) автоматически обрежет тело ответа,
    # поэтому клиент (фронтенд) никогда не увидит сообщение "Турбина успешно удалена".
    return {"message": f"Турбина '{db_turbine.name}' успешно удалена"}
    