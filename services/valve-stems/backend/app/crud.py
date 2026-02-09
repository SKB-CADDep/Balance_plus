from fastapi import HTTPException, status
from app.models import CalculationResultDB
from sqlalchemy.orm import Session
from app import models, schemas
from typing import Optional
from datetime import datetime, timezone
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_valves_by_turbine(db: Session, turbine_name: str) -> Optional[schemas.TurbineValves]:
    """
        Получает список клапанов для заданной турбины.

        Args:
            db: Сессия базы данных.
            turbine_name: Название турбины.

        Returns:
            Список клапанов или None, если турбина не найдена.

        Raises:
            HTTPException: Если произошла ошибка базы данных (500).
        """
    try:
        turbine = db.query(models.Turbine) \
            .filter(models.Turbine.name == turbine_name) \
            .first()

        if not turbine:
            return None

        # Получаем клапаны
        valves = turbine.valves

        # Создаем список ValveInfo объектов
        valve_info_list = []
        for valve in valves:
            valve_info = schemas.ValveInfo(
                id=valve.id,
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
                round_radius=valve.round_radius
            )
            valve_info_list.append(valve_info)

        return schemas.TurbineValves(
            count=len(valve_info_list),
            valves=valve_info_list
        )
    except Exception as e:
        logger.error(f"Ошибка базы данных при получении клапанов по турбине: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось получить клапаны: {e}")


def create_calculation_result(db: Session, parameters: schemas.CalculationParams, results: schemas.CalculationResult,
                              valve_id: int) -> CalculationResultDB:
    """
        Создает запись о результате расчета в базе данных.

        Args:
            db: Сессия базы данных.
            parameters: Входные параметры расчета.
            results: Результаты расчета.
            valve_id: ID клапана.

        Returns:
            Созданный объект CalculationResultDB.

        Raises:
            HTTPException: Если произошла ошибка при сохранении результата (500).
        """
    try:
        db_result = CalculationResultDB(
            user_name="default_user",
            stock_name=parameters.valve_drawing,
            turbine_name=parameters.turbine_name,
            calc_timestamp=datetime.now(timezone.utc),
            input_data=json.dumps(parameters.model_dump()),
            output_data=json.dumps(results.model_dump()),
            valve_id=valve_id
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        return db_result
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка базы данных при сохранении результата расчета: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось сохранить результат расчета: {e}")


def get_results_by_valve_drawing(db: Session, valve_drawing: str):
    """
        Получает результаты расчетов по названию клапана.

        Args:
            db: Сессия базы данных.
            valve_drawing: Название клапана.

        Returns:
            Список результатов расчетов.

        Raises:
            HTTPException: Если произошла ошибка при получении результатов (500).
        """
    try:
        results = (
            db.query(models.CalculationResultDB)
            .filter(models.CalculationResultDB.stock_name == valve_drawing)
            .order_by(models.CalculationResultDB.calc_timestamp.desc())
            .all()
        )

        # Если данные уже являются словарями, то десериализация не нужна
        for result in results:
            if isinstance(result.input_data, str):
                result.input_data = json.loads(result.input_data)
            if isinstance(result.output_data, str):
                result.output_data = json.loads(result.output_data)
        return results
    except Exception as e:
        logger.error(f"Ошибка базы данных при получении результатов по клапану: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось получить результаты: {e}")


def get_calculation_result_by_id(db: Session, result_id: int) -> Optional[CalculationResultDB]:
    """
    Получает один результат расчета по его ID.
    """
    try:
        result = db.query(CalculationResultDB).filter(CalculationResultDB.id == result_id).first()
        if result:
            if isinstance(result.input_data, str):
                result.input_data = json.loads(result.input_data)
            if isinstance(result.output_data, str):
                result.output_data = json.loads(result.output_data)
        return result
    except Exception as e:
        logger.error(f"Ошибка базы данных при получении результата расчета по ID {result_id}: {str(e)}")
        return None


def get_turbine_by_id(db: Session, turbine_id: int) -> Optional[models.Turbine]:
    """
    Получает одну турбину по ее ID.
    """
    try:
        turbine = db.query(models.Turbine).filter(models.Turbine.id == turbine_id).first()
        return turbine
    except Exception as e:
        logger.error(f"Ошибка базы данных при получении турбины по ID {turbine_id}: {str(e)}")
        return None


def get_valve_by_id(db: Session, valve_id: int) -> Optional[models.Valve]:
    """
    Получает один клапан (шток) по его ID.
    """
    try:
        valve = db.query(models.Valve).filter(models.Valve.id == valve_id).first()
        return valve
    except Exception as e:
        logger.error(f"Ошибка базы данных при получении клапана по ID {valve_id}: {str(e)}")
        return None


def get_valve_by_drawing(db: Session, valve_drawing: str) -> Optional[models.Valve]:
    """
    Получает клапан по его названию (чертежу).
    """
    try:
        valve = (
            db.query(models.Valve)
            .filter(models.Valve.name == valve_drawing)
            .first()
        )
        return valve
    except Exception as e:
        logger.error(f"Ошибка при получении клапана по чертежу {valve_drawing}: {str(e)}")
        return None
