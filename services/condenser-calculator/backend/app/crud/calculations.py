import logging

from sqlalchemy.orm import Session

from app.models.calculation_result import CalculationResult

logger = logging.getLogger(__name__)


def save_calculation_result(
    db: Session,
    condenser_id: int,
    input_data: dict,
    output_data: dict,
    method: str,
) -> CalculationResult:
    """Сохраняет результаты расчета и входные параметры в БД."""
    logger.info(
        "DB: saving calculation result",
        extra={"condenser_id": condenser_id, "method": method}
    )

    result = CalculationResult(
        condenser_id=condenser_id,
        input_data=input_data,
        output_data=output_data,
        method=method
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    logger.info(
        "DB: calculation result saved successfully",
        extra={"calculation_id": result.id, "condenser_id": condenser_id}
    )

    return result
