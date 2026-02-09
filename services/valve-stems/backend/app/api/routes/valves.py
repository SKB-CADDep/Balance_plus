import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import get_valve_by_id
from app.dependencies import get_db
from app.models import Turbine, Valve
from app.schemas import TurbineInfo, ValveCreate, ValveInfo


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("", response_model=list[ValveInfo], summary="Получить все клапаны")
async def get_valves(db: Session = Depends(get_db)):
    try:
        valves = db.query(Valve).all()
        # Ваша старая логика для Unknown имен
        for valve in valves:
            if valve.name is None:
                valve.name = "Unknown"
        return valves
    except Exception as e:
        logger.error(f"Ошибка при получении всех клапанов: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка сервера: {e}")

@router.post("/", response_model=ValveInfo, status_code=status.HTTP_201_CREATED, summary="Создать клапан")
async def create_valve(valve: ValveCreate, db: Session = Depends(get_db)):
    try:
        existing_valve = db.query(Valve).filter(Valve.name == valve.name).first()
        if existing_valve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Клапан с таким именем уже существует.")

        new_valve = Valve(
            name=valve.name,
            type=valve.type,
            diameter=valve.diameter,
            clearance=valve.clearance,
            count_parts=valve.count_parts,
            len_part1=valve.len_part1,
            len_part2=valve.len_part2,
            len_part3=valve.len_part3,
            len_part4=valve.len_part4,
            len_part5=valve.len_part5,
            round_radius=valve.round_radius,
            turbine_id=valve.turbine_id
        )

        db.add(new_valve)
        db.commit()
        db.refresh(new_valve)
        return new_valve
    except Exception as e:
        logger.error(f"Ошибка при создании клапана: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Не удалось создать клапан: {e}")

@router.put("/{valve_id}", response_model=ValveInfo, summary="Обновить клапан")
async def update_valve(valve_id: int, valve: ValveInfo, db: Session = Depends(get_db)):
    try:
        db_valve = db.query(Valve).filter(Valve.id == valve_id).first()
        if db_valve is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клапан не найден")

        # Обновляем поля (лучше использовать Pydantic dict exclude_unset=True, но оставим как есть)
        db_valve.name = valve.name
        db_valve.type = valve.type
        db_valve.diameter = valve.diameter
        db_valve.clearance = valve.clearance
        db_valve.count_parts = valve.count_parts
        db_valve.len_part1 = valve.len_part1
        db_valve.len_part2 = valve.len_part2
        db_valve.len_part3 = valve.len_part3
        db_valve.len_part4 = valve.len_part4
        db_valve.len_part5 = valve.len_part5
        db_valve.round_radius = valve.round_radius
        db_valve.turbine_id = valve.turbine_id

        db.commit()
        db.refresh(db_valve)
        return db_valve
    except Exception as e:
        logger.error(f"Ошибка при обновлении клапана {valve_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось обновить клапан: {e}")

@router.get("/{valve_id}", response_model=ValveInfo, summary="Получить клапан по ID")
async def read_valve_by_id(valve_id: int, db: Session = Depends(get_db)):
    db_valve = get_valve_by_id(db, valve_id=valve_id)
    if db_valve is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клапан (шток) не найден")
    return db_valve

@router.delete("/{valve_id}", response_model=dict, summary="Удалить клапан")
async def delete_valve(valve_id: int, db: Session = Depends(get_db)):
    try:
        valve = db.query(Valve).filter(Valve.id == valve_id).first()
        if valve is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клапан не найден")
        db.delete(valve)
        db.commit()
        return {"message": f"Клапан '{valve.name}' успешно удален"}
    except Exception as e:
        logger.error(f"Ошибка при удалении клапана {valve_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Не удалось удалить клапан: {e}")

@router.get("/{valve_name}/turbine", response_model=TurbineInfo, summary="Получить турбину по имени клапана")
async def get_turbine_by_valve_name(valve_name: str, db: Session = Depends(get_db)):
    try:
        valve = db.query(Valve).filter(Valve.name == valve_name).first()
        if not valve:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Клапан с именем '{valve_name}' не найден")

        turbine = db.query(Turbine).filter(Turbine.id == valve.turbine_id).first()
        if not turbine:
            raise HTTPException(status_code=404, detail=f"Турбина для клапана '{valve_name}' не найдена")

        return TurbineInfo.model_validate(turbine)
    except Exception as e:
        logger.error(f"Ошибка при получении турбины для клапана {valve_name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка сервера: {e}")
