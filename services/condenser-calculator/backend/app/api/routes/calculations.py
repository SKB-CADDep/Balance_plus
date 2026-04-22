import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.calculation_adapter import CondenserCalculationAdapter
from app.core.exceptions import EntityNotFoundError, ValidationError
from app.crud.condensers import get_condenser_by_id
from app.crud.materials import get_material_by_id
from app.dependencies import get_db
from app.schemas.calculation import CalculationInput, CalculationOutput

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Calculations"])

adapter = CondenserCalculationAdapter()


@router.post(
    "/calculate",
    response_model=CalculationOutput,
    summary="Расчёт конденсатора",
    description="Выполняет расчёт по методике Бермана или Метро-Виккерса и возвращает матрицы результатов.",
    responses={
        200: {"description": "Успешный расчёт"},
        400: {"description": "Ошибка валидации или расчёта"},
        404: {"description": "Конденсатор или материал не найден"},
        422: {"description": "Ошибка бизнес-валидации"},
    },
)
async def calculate(
    input_data: CalculationInput,
    db: Session = Depends(get_db),
):
    """
    Основной эндпоинт расчёта конденсатора.
    """
    logger.info(
        "Received calculation request",
        extra={
            "condenser_id": input_data.condenser_id,
            "method": input_data.method,
            "tables_expected": len(input_data.coefficient_b) * max(
                len(input_data.W_main), len(input_data.W_builtin or [])
            ),
        },
    )

    try:
        # 1. Получаем конденсатор
        condenser = get_condenser_by_id(db, input_data.condenser_id)

        # 2. Получаем материал
        material_id = input_data.material_id or condenser.material_id
        material = get_material_by_id(db, material_id)

        # 3. Выполняем расчёт через адаптер
        result = adapter.calculate(input_data, condenser, material)

        logger.info(
            "Calculation completed successfully",
            extra={"condenser_id": condenser.id, "tables": len(result.tables)},
        )

        return result

    except EntityNotFoundError as e:
        logger.warning("Entity not found", extra={"error": str(e)})
        raise HTTPException(status_code=404, detail=str(e))

    except (ValidationError, UnitConversionError) as e:
        logger.warning("Validation error", extra={"error": str(e)})
        raise HTTPException(status_code=422, detail=str(e))

    except CalculationEngineError as e:
        logger.error("Calculation engine error", extra={"error": str(e)})
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.exception("Unexpected error during calculation")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера при выполнении расчёта.",
        )