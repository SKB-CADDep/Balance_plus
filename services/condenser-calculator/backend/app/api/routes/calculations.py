import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.adapters.calculation_adapter import CondenserCalculationAdapter
from app.core.condenser_validators import validate_condenser_for_method
from app.core.exceptions import (
    CalculationEngineError,
    EntityNotFoundError,
    UnitConversionError,
    ValidationError,
)
from app.crud.condensers import get_condenser_by_id
from app.crud.materials import get_material_by_id
from app.dependencies import get_db
from app.schemas.calculation import CalculationInput, CalculationOutput
from app.services.excel_exporter import ExcelExporter

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

        # 3. Валидация BR-02 (Полнота геометрии)
        validate_condenser_for_method(condenser, input_data.method)

        # 4. Выполняем расчёт через адаптер
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

    except Exception:
        logger.exception("Unexpected error during calculation")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера при выполнении расчёта.",
        )


@router.post(
    "/calculate/excel",
    summary="Расчёт конденсатора с выгрузкой в Excel (PoC)",
    description="Выполняет расчёт и возвращает результаты в формате XLSX. Матрицы и скаляры разбиты по листам.",
    responses={
        200: {"description": "Успешный расчёт, возвращается файл"},
        400: {"description": "Ошибка валидации или расчёта"},
        404: {"description": "Конденсатор или материал не найден"},
        422: {"description": "Ошибка бизнес-валидации"},
    },
)
async def calculate_excel(
    input_data: CalculationInput,
    db: Session = Depends(get_db),
):
    """
    Эндпоинт расчёта конденсатора с прямым экспортом в Excel.
    """
    logger.info(
        "Received calculation EXCEL export request",
        extra={"condenser_id": input_data.condenser_id,
               "method": input_data.method},
    )

    try:
        condenser = get_condenser_by_id(db, input_data.condenser_id)
        material_id = input_data.material_id or condenser.material_id
        material = get_material_by_id(db, material_id)

        # Валидация BR-02
        validate_condenser_for_method(condenser, input_data.method)

        # Выполняем расчёт через адаптер
        result = adapter.calculate(input_data, condenser, material)

        # Генерируем Excel
        file_stream = ExcelExporter.export_calculation(result)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"calculation_results_condenser_{condenser.id}_{timestamp}.xlsx"

        logger.info("Excel generation completed", extra={"filename": filename})

        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except EntityNotFoundError as e:
        logger.warning("Entity not found", extra={"error": str(e)})
        raise HTTPException(status_code=404, detail=str(e))
    except (ValidationError, UnitConversionError) as e:
        logger.warning("Validation error", extra={"error": str(e)})
        raise HTTPException(status_code=422, detail=str(e))
    except CalculationEngineError as e:
        logger.error("Calculation engine error", extra={"error": str(e)})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Unexpected error during calculation excel export")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера при генерации Excel.",
        )
