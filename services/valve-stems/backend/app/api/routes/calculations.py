import json
import logging

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.adapters.calculation_adapter import CalculationAdapter
from app.crud import (
    create_calculation_result,
    get_calculation_result_by_id,
    get_results_by_valve_drawing,
)
from app.crud.valves import get_valve_by_id
from app.dependencies import get_db
from app.schemas import CalculationResultDB as CalculationResultDBSchema
from app.schemas import MultiCalculationParams, MultiCalculationResult, ValveInfo

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calculate",
    response_model=MultiCalculationResult,
    summary="Выполнить мульти-расчет",
)
async def calculate(params: MultiCalculationParams, db: Session = Depends(get_db)):
    logger.info(
        "API: calculation requested",
        extra={"turbine_id": params.turbine_id, "valve_count": len(params.groups)},
    )

    groups_data = []
    for group in params.groups:
        valve_db = get_valve_by_id(db, valve_id=group.valve_id)
        groups_data.append((group, ValveInfo.model_validate(valve_db)))

    calculation_result = CalculationAdapter.run_multi_calculation(
        params.globals, groups_data
    )

    stock_name_parts = [f"{v_info.name} ({g.quantity}шт)" for g, v_info in groups_data]
    pretty_stock_name = " + ".join(stock_name_parts)
    turbine_name = f"Проект ID: {params.turbine_id}"

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
    summary="Получить результаты расчётов",
)
async def get_calculation_results(valve_name: str, db: Session = Depends(get_db)):
    logger.info("API: fetching results for valve", extra={"valve_name": valve_name})

    db_results = get_results_by_valve_drawing(db, valve_drawing=valve_name)
    if not db_results:
        return []

    calculation_results = []
    for result in db_results:
        input_data = (
            result.input_data
            if isinstance(result.input_data, dict)
            else json.loads(result.input_data)
        )
        output_data = (
            result.output_data
            if isinstance(result.output_data, dict)
            else json.loads(result.output_data)
        )

        calculation_results.append(
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

    return calculation_results


@router.get(
    "/{result_id}",
    response_model=CalculationResultDBSchema,
    summary="Получить результат расчета по ID",
)
async def read_calculation_result(result_id: int, db: Session = Depends(get_db)):
    db_result = get_calculation_result_by_id(db, result_id=result_id)
    return db_result


@router.delete(
    "/{result_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить результат расчёта",
)
async def delete_calculation_result(result_id: int, db: Session = Depends(get_db)):
    logger.info("API: deleting calculation", extra={"result_id": result_id})
    result = get_calculation_result_by_id(db, result_id=result_id)

    db.delete(result)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
