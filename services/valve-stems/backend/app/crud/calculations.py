"""
Репозиторий доступа к данным результатов расчетов (Calculation Results).

Реализует операции сохранения и извлечения исторических расчетов
в базе данных PostgreSQL для сервиса 'Valve Stems'.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFoundError
from app.models import CalculationResultDB
from app.schemas import MultiCalculationParams, MultiCalculationResult

logger = logging.getLogger(__name__)


def create_calculation_result(
    db: Session,
    parameters: MultiCalculationParams,
    results: MultiCalculationResult,
    stock_name: str,
    turbine_name: str,
) -> CalculationResultDB:
    """
    Сохраняет входные параметры и результаты выполнения расчета в базу данных.
    
    Args:
        db: Текущая сессия базы данных.
        parameters: Pydantic-схема с исходными данными для расчета.
        results: Pydantic-схема с вычисленными матрицами результатов.
        stock_name: Наименование/чертеж штока.
        turbine_name: Наименование турбины.

    Returns:
        CalculationResultDB: Созданная ORM-модель записи с присвоенным ID.
    """
    logger.info(
        "DB: saving calculation result",
        extra={"turbine_name": turbine_name, "stock_name": stock_name},
    )

    try:
        # Для сохранения Pydantic моделей в JSON-колонки используется .model_dump()
        db_result = CalculationResultDB(
            user_name="Engineer",
            stock_name=stock_name,
            turbine_name=turbine_name,
            calc_timestamp=datetime.now(timezone.utc),
            input_data=parameters.model_dump(),
            output_data=results.model_dump(),
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        return db_result
    except Exception as e:
        db.rollback()
        logger.error(
            "DB: integrity error", 
            extra={"error": str(e)}, 
            exc_info=True
        )
        raise


def get_results_by_valve_drawing(db: Session, valve_drawing: str) -> list[CalculationResultDB]:
    """
    Ищет историю расчетов по частичному совпадению номера чертежа штока (ILIKE).
    Результаты сортируются от самых новых к старым.
    """
    try:
        # WARNING (Технический долг):
        # В SQLAlchemy 2.0 использование db.query() считается устаревшим (legacy).
        # В будущем рекомендуется переписать на db.execute(select(CalculationResultDB)...).scalars().all()
        results = (
            db.query(CalculationResultDB)
            .filter(CalculationResultDB.stock_name.ilike(f"%{valve_drawing}%"))
            .order_by(CalculationResultDB.calc_timestamp.desc())
            .all()
        )

        if not results:
            logger.info(
                "DB: no calculation results found",
                extra={"valve_drawing": valve_drawing},
            )

        return results
    except Exception as e:
        logger.error(
            "DB: error fetching results",
            extra={"error": str(e), "valve_drawing": valve_drawing},
            exc_info=True,
        )
        return []


def get_calculation_result_by_id(db: Session, result_id: int) -> CalculationResultDB:
    """
    Получает конкретный результат расчета по его уникальному идентификатору.
    
    Raises:
        EntityNotFoundError: Если результат с указанным ID не существует в БД.
    """
    result = (
        db.query(CalculationResultDB)
        .filter(CalculationResultDB.id == result_id)
        .first()
    )
    if not result:
        raise EntityNotFoundError(
            entity_name="Результат расчёта", 
            entity_id=result_id
        )
    return result
    