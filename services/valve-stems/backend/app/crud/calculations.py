import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import CalculationResultDB
from app.schemas import MultiCalculationParams, MultiCalculationResult


logger = logging.getLogger(__name__)

def create_calculation_result(
    db: Session,
    parameters: MultiCalculationParams,
    results: MultiCalculationResult
) -> CalculationResultDB:  # Убрали valve_id: int
    try:
        input_data_json = parameters.model_dump()
        output_data_json = results.model_dump()
        
        db_result = CalculationResultDB(
            user_name="Engineer",
            stock_name="tmp", # Перезапишется в роутере
            turbine_name="tmp",
            calc_timestamp=datetime.utcnow(),
            input_data=input_data_json,
            output_data=output_data_json
        )
        
        db.add(db_result)
        db.flush() 
        return db_result
    except Exception as e:
        logger.error(f"Ошибка при сохранении результата расчета в БД: {e}")
        raise

def get_results_by_valve_drawing(db: Session, valve_drawing: str) -> list[CalculationResultDB]:
    """
    Получает результаты расчетов по названию клапана.
    """
    try:
        results = (
            db.query(CalculationResultDB)
            .filter(CalculationResultDB.stock_name == valve_drawing)
            .order_by(CalculationResultDB.calc_timestamp.desc())
            .all()
        )
        return results
    except Exception as e:
        logger.error(f"Ошибка базы данных при получении результатов по клапану: {e!s}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось получить результаты: {e}")

def get_calculation_result_by_id(db: Session, result_id: int) -> CalculationResultDB | None:
    """
    Получает один результат расчета по его ID.
    """
    try:
        result = db.query(CalculationResultDB).filter(CalculationResultDB.id == result_id).first()
        return result
    except Exception as e:
        logger.error(f"Ошибка базы данных при получении результата расчета по ID {result_id}: {e!s}")
        return None
