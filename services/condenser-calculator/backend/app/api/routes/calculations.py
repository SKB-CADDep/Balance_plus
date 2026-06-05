"""
API-маршрутизатор для выполнения синхронных расчетов конденсаторов.

Предоставляет эндпоинты для прямого расчета с возвратом JSON-результатов
и для выгрузки результатов в формате Excel. Связывает HTTP-слой с
расчетным ядром через паттерн Адаптер (CondenserCalculationAdapter).
Обеспечивает валидацию бизнес-правил (например, BR-02) перед вызовом математики.
"""

import logging
import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.adapters.calculation_adapter import CondenserCalculationAdapter
from app.core.exceptions import EntityNotFoundError, ValidationError, UnitConversionError, CalculationEngineError
from app.crud.condensers import get_condenser_by_id
from app.crud.materials import get_material_by_id
from app.dependencies import get_db
from app.schemas.calculation import CalculationInput, CalculationOutput
from app.core.condenser_validators import validate_condenser_for_method

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
    Выполняет расчет конденсатора на основе переданной геометрии, режимов и параметров.

    Связывает входные параметры HTTP-запроса с расчетным ядром через адаптер.
    Перед запуском математического движка проверяет полноту исходных данных (BR-02).

    Args:
        input_data (CalculationInput): Входные данные (ID конденсатора, метод расчета, 
            матрицы расходов охлаждающей воды W и т.д.).
        db (Session): Сессия базы данных, инжектится автоматически (Dependency Injection).

    Returns:
        CalculationOutput: Объект с результатами расчета (таблицы и скалярные значения).

    Raises:
        HTTPException (404): Если запрашиваемый конденсатор или материал труб не найдены в БД.
        HTTPException (422): При ошибках конвертации единиц измерения или неполной геометрии (провал BR-02).
        HTTPException (400): Если расчетное ядро не смогло сойтись или выдало математическую ошибку.
        HTTPException (500): При непредвиденных внутренних ошибках сервера.
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
        # Загрузка сущностей из БД. Если ID материала труб не передан в запросе, 
        # используется материал по умолчанию, жестко привязанный к конденсатору.
        condenser = get_condenser_by_id(db, input_data.condenser_id)
        
        material_id = input_data.material_id or condenser.material_id
        material = get_material_by_id(db, material_id)

        # Бизнес-валидация BR-02: проверка наличия всех необходимых геометрических 
        # параметров конденсатора для выбранного метода расчета (Берман/Метро-Виккерс).
        validate_condenser_for_method(condenser, input_data.method)

        # Передача валидных доменных объектов в слой адаптера для расчета
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
    Выполняет расчет конденсатора и генерирует отчет в формате Excel (XLSX).

    Логика инициализации и расчета идентична эндпоинту `/calculate`, однако 
    результаты пропускаются через сервис `ExcelExporter` для формирования 
    бинарного потока данных, а не JSON.

    Args:
        input_data (CalculationInput): Входные данные для расчета.
        db (Session): Сессия базы данных (Dependency Injection).

    Returns:
        StreamingResponse: Поток байтов файла `.xlsx` с заголовками для скачивания (Content-Disposition).

    Raises:
        HTTPException (404, 422, 400, 500): Различные бизнес-ошибки и системные сбои (см. эндпоинт `/calculate`).
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

        # Преобразование результатов расчетов в бинарный поток Excel-файла
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
    except Exception as e:
        logger.exception("Unexpected error during calculation excel export")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера при генерации Excel.",
        )