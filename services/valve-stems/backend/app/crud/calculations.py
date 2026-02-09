import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import CalculationResultDB
from app.schemas import CalculationParams, CalculationResult


logger = logging.getLogger(__name__)

def create_calculation_result(
    db: Session,
    parameters: CalculationParams,
    results: CalculationResult,
    valve_id: int
) -> CalculationResultDB:
    """
    Создает запись о результате расчета в базе данных.
    """
    try:
        db_result = CalculationResultDB(
            user_name="default_user",
            stock_name=parameters.valve_drawing,
            turbine_name=parameters.turbine_name,
            calc_timestamp=datetime.now(timezone.utc),
            # В Pydantic v2 model_dump() возвращает dict, который SQLAlchemy JSON тип принимает напрямую
            # Но если у вас в базе тип JSON (Native), то dumps не нужен.
            # Если в базе строка - то нужен. Судя по старому коду, вы делали json.dumps.
            # Оставим json.dumps для совместимости, если колонка текстовая или драйвер требует.
            # Если колонка реально JSONB, то лучше передавать dict.
            # В старом коде было: input_data=json.dumps(...)
            input_data=parameters.model_dump(mode='json'),
            output_data=results.model_dump(mode='json'),
            valve_id=valve_id
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        return db_result
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка базы данных при сохранении результата расчета: {e!s}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось сохранить результат расчета: {e}")

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
