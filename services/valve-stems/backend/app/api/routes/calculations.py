"""
API-маршрутизатор для выполнения расчетов штоков клапанов.

Отвечает за запуск мультирасчёта, сохранение результатов в историю
и предоставление доступа к архиву расчетов.
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.calculation_adapter import CalculationAdapter
from app.crud import (
    create_calculation_result,
    get_calculation_result_by_id,
    get_results_by_valve_drawing,
)
from app.crud.valves import get_valves_by_ids
from app.dependencies import get_db
from app.schemas import (
    CalculationResultDB as CalculationResultDBSchema,
    MultiCalculationParams,
    MultiCalculationResult,
    ValveInfo,
)

router = APIRouter(tags=["Calculations"])
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=MultiCalculationResult,
    summary="Выполнить мульти-расчет",
)
async def calculate(params: MultiCalculationParams, db: Session = Depends(get_db)):
    """
    Выполняет расчет для нескольких штоков клапанов одновременно.

    Оптимизировано: все клапаны загружаются одним запросом (IN), а не в цикле.
    """
    logger.info(
        "Запрошен мультирасчёт",
        extra={
            "turbine_id": params.turbine_id,
            "valve_count": len(params.groups),
        },
    )

    # === ИСПРАВЛЕНИЕ N+1 ===
    # Собираем все valve_id из запроса
    valve_ids = [group.valve_id for group in params.groups]

    # Один запрос к БД вместо N запросов
    valves_db = get_valves_by_ids(db, valve_ids=valve_ids)
    valve_dict = {v.id: v for v in valves_db}

    # Формируем данные для расчёта
    groups_data = []
    for group in params.groups:
        valve_db = valve_dict.get(group.valve_id)
        if not valve_db:
            logger.warning("Valve with id=%s not found", group.valve_id)
            continue
        groups_data.append((group, ValveInfo.model_validate(valve_db)))

    if not groups_data:
        return MultiCalculationResult(results=[])

    # Выполнение математического расчёта
    calculation_result = CalculationAdapter.run_multi_calculation(
        params.globals, groups_data
    )

    # Формирование красивого названия для истории
    stock_name_parts = [f"{v_info.name} ({g.quantity}шт)" for g, v_info in groups_data]
    pretty_stock_name = " + ".join(stock_name_parts)
    turbine_name = f"Проект ID: {params.turbine_id}"

    # Сохранение результата в базу
    create_calculation_result(
        db=db,
        parameters=params,
        results=calculation_result,
        stock_name=pretty_stock_name,
        turbine_name=turbine_name,
    )

    return calculation_result


@router.get(
    "/valves/{valve_name:path}/results/",
    response_model=list[CalculationResultDBSchema],
    summary="Получить историю расчетов по чертежу",
)
async def get_calculation_results(valve_name: str, db: Session = Depends(get_db)):
    """
    Возвращает историю всех расчетов для указанного чертежного номера штока.
    """
    logger.info("Запрошена история расчетов", extra={"valve_name": valve_name})

    db_results = get_results_by_valve_drawing(db, valve_drawing=valve_name)
    if not db_results:
        return []

    results = []
    for result in db_results:
        input_data = (
            result.input_data
            if isinstance(result.input_data, dict)
            else json.loads(result.input_data or "{}")
        )
        output_data = (
            result.output_data
            if isinstance(result.output_data, dict)
            else json.loads(result.output_data or "{}")
        )

        results.append(
            CalculationResultDBSchema(
                id=result.id,
                user_name=result.user_name,
                stock_name=result.stock_name,
                turbine_name=result.turbine_name,
                calc_timestamp=result.calc_timestamp,
                input_data=input_data,
                output_data=output_data,
            )
        )

    return results


@router.get(
    "/{result_id}",
    response_model=CalculationResultDBSchema,
    summary="Получить результат расчета по ID",
)
async def read_calculation_result(result_id: int, db: Session = Depends(get_db)):
    """Возвращает конкретный результат расчета по его идентификатору."""
    return get_calculation_result_by_id(db, result_id=result_id)


@router.delete(
    "/{result_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить результат расчёта",
)
async def delete_calculation_result(result_id: int, db: Session = Depends(get_db)):
    """Удаляет запись результата расчета из истории."""
    logger.info("Удаление результата расчета", extra={"result_id": result_id})

    result = get_calculation_result_by_id(db, result_id=result_id)
    db.delete(result)
    db.commit()

    return None
