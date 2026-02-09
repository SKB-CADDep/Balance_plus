import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.crud import (
    create_calculation_result,
    get_calculation_result_by_id,
    get_results_by_valve_drawing,
)
from app.dependencies import get_db
from app.models import CalculationResultDB, Valve
from app.schemas import CalculationParams, ValveInfo
from app.schemas import CalculationResultDB as CalculationResultDBSchema
from app.services.calculator import CalculationError, ValveCalculator


router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("", response_model=CalculationResultDBSchema, summary="Выполнить расчет")
async def calculate(params: CalculationParams, db: Session = Depends(get_db)):
    try:
        valve = db.query(Valve).filter(Valve.name == params.valve_drawing).first()
        if not valve:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Клапан с именем '{params.valve_drawing}' не найден")

        valve_info = ValveInfo.model_validate(valve)

        calculator = ValveCalculator(params, valve_info)
        calculation_result = calculator.perform_calculations()

        new_result = create_calculation_result(
            db=db,
            parameters=params,
            results=calculation_result,
            valve_id=valve.id
        )

        return CalculationResultDBSchema(
            id=new_result.id,
            user_name=new_result.user_name,
            stock_name=new_result.stock_name,
            turbine_name=new_result.turbine_name,
            calc_timestamp=new_result.calc_timestamp,
            # Десериализация для Pydantic ответа (если в БД строка)
            input_data=json.loads(new_result.input_data) if isinstance(new_result.input_data, str) else new_result.input_data,
            output_data=json.loads(new_result.output_data) if isinstance(new_result.output_data, str) else new_result.output_data
        )
    except CalculationError as ce:
        logger.error(f"Ошибка при выполнении расчётов: {ce.message}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ce.message)
    except Exception as e:
        logger.error(f"Ошибка при выполнении расчётов: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось выполнить расчёты: {e}")

@router.get("/valves/{valve_name:path}/results/", response_model=list[CalculationResultDBSchema], summary="Получить результаты расчётов")
async def get_calculation_results(valve_name: str, db: Session = Depends(get_db)):
    try:
        db_results = get_results_by_valve_drawing(db, valve_drawing=valve_name)

        if not db_results:
            return []

        calculation_results = []
        for result in db_results:
            input_data = result.input_data
            output_data = result.output_data

            if isinstance(input_data, str):
                input_data = json.loads(input_data)
            if isinstance(output_data, str):
                output_data = json.loads(output_data)

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

    except Exception as e:
        logger.error(f"Ошибка при получении результатов расчётов для клапана {valve_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить результаты расчётов: {e}",
        )

@router.get("/{result_id}", response_model=CalculationResultDBSchema, summary="Получить результат расчета по ID")
async def read_calculation_result(result_id: int, db: Session = Depends(get_db)):
    db_result = get_calculation_result_by_id(db, result_id=result_id)
    if db_result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Результат расчёта не найден")
    return db_result

@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить результат расчёта")
async def delete_calculation_result(result_id: int, db: Session = Depends(get_db)):
    try:
        result = db.query(CalculationResultDB).filter(CalculationResultDB.id == result_id).first()
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Результат расчёта не найден")
        db.delete(result)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Ошибка при удалении результата расчёта {result_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не удалось удалить результат расчёта: {e}")
