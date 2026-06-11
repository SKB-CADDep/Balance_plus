"""
API-маршрутизатор для управления справочником клапанов/штоков (Valves).

Предоставляет полноценный CRUD интерфейс (Create, Read, Update, Delete) 
для работы с таблицей клапанов в базе данных.
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFoundError, ValidationError
from app.crud.valves import get_valve_by_id
from app.dependencies import get_db
from app.models import Turbine, Valve
from app.schemas import TurbineInfo, ValveCreate, ValveInfo

# Добавлен тег для группировки эндпоинтов в Swagger UI
router = APIRouter(tags=["Valves"])
logger = logging.getLogger(__name__)


# WARNING (Технический долг):
# Логика работы с сессией БД (db.query, db.add, db.commit) частично реализована
# прямо в HTTP-слое. В рамках рефакторинга рекомендуется вынести её
# в абстракцию app/crud/valves.py по аналогии с get_valve_by_id.

@router.get("/", response_model=list[ValveInfo], summary="Получить все клапаны")
async def get_valves(db: Session = Depends(get_db)):
    """Возвращает полный список доступных клапанов (штоков) из справочника."""
    valves = db.query(Valve).all()
    for valve in valves:
        if valve.name is None:
            valve.name = "Unknown"
    return valves


@router.post(
    "/",
    response_model=ValveInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Создать клапан",
)
async def create_valve(valve: ValveCreate, db: Session = Depends(get_db)):
    """
    Добавляет новый клапан в базу данных.
    Выбрасывает ValidationError, если клапан с таким чертежом уже существует.
    """
    existing_valve = db.query(Valve).filter(Valve.name == valve.name).first()
    if existing_valve:
        raise ValidationError(message="Клапан с таким именем (чертежом) уже существует.")

    new_valve = Valve(**valve.model_dump())
    db.add(new_valve)
    db.commit()
    db.refresh(new_valve)
    return new_valve


@router.put("/{valve_id}", response_model=ValveInfo, summary="Обновить клапан")
async def update_valve(valve_id: int, valve: ValveInfo, db: Session = Depends(get_db)):
    """Обновляет параметры существующего клапана по его ID."""
    db_valve = get_valve_by_id(db, valve_id=valve_id)
    
    # Обновляем только те поля, которые были явно переданы в запросе
    for key, value in valve.model_dump(exclude_unset=True).items():
        setattr(db_valve, key, value)

    db.commit()
    db.refresh(db_valve)
    return db_valve


@router.get("/{valve_id}", response_model=ValveInfo, summary="Получить клапан по ID")
async def read_valve_by_id(valve_id: int, db: Session = Depends(get_db)):
    """Запрашивает детальную информацию по конкретному клапану."""
    return get_valve_by_id(db, valve_id=valve_id)


@router.delete("/{valve_id}", response_model=dict, summary="Удалить клапан")
async def delete_valve(valve_id: int, db: Session = Depends(get_db)):
    """
    Полностью удаляет клапан из базы данных по его ID.
    (Внимание: может нарушить ссылочную целостность, если нет каскадного удаления).
    """
    valve = get_valve_by_id(db, valve_id=valve_id)
    db.delete(valve)
    db.commit()
    return {"message": f"Клапан '{valve.name}' успешно удален"}


@router.get(
    "/{valve_name}/turbine",
    response_model=TurbineInfo,
    summary="Получить турбину по имени клапана",
)
async def get_turbine_by_valve_name(valve_name: str, db: Session = Depends(get_db)):
    """
    Обратный поиск: находит турбину, к которой привязан клапан 
    с указанным чертежным номером (именем).
    """
    valve = db.query(Valve).filter(Valve.name == valve_name).first()
    if not valve:
        raise EntityNotFoundError(entity_name="Клапан", entity_id=valve_name)

    turbine = db.query(Turbine).filter(Turbine.id == valve.turbine_id).first()
    if not turbine:
        raise EntityNotFoundError(
            entity_name="Турбина для клапана", entity_id=valve_name
        )

    return TurbineInfo.model_validate(turbine)
