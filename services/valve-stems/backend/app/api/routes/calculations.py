import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.adapters.calculation_adapter import CalculationAdapter
from app.crud import (
    create_calculation_result,
    get_calculation_result_by_id,
    get_results_by_valve_drawing,
)
from app.dependencies import get_db
from app.models import CalculationResultDB, Valve
from app.schemas import ValveInfo
from app.schemas import CalculationResultDB as CalculationResultDBSchema
from app.schemas import MultiCalculationParams, MultiCalculationResult

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/calculate", response_model=MultiCalculationResult, summary="Выполнить мульти-расчет")
async def calculate(params: MultiCalculationParams, db: Session = Depends(get_db)):
    try:
        # 1. Собираем данные по всем клапанам из БД
        groups_data = []
        for group in params.groups:
            valve_db = db.query(Valve).filter(Valve.id == group.valve_id).first()
            if not valve_db:
                raise HTTPException(status_code=404, detail=f"Клапан ID={group.valve_id} не найден")
            groups_data.append((group, ValveInfo.model_validate(valve_db)))

        # 2. Вызываем мульти-адаптер
        try:
            calculation_result = CalculationAdapter.run_multi_calculation(params.globals, groups_data)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

        # 3. Формируем имя для истории
        stock_name_parts = []
        for g in params.groups:
            stock_name_parts.append(f"{g.type}({g.quantity}шт)")
        stock_name = ", ".join(stock_name_parts)

        # 4. Сохраняем (твоя функция)
        new_result = create_calculation_result(
            db=db,
            parameters=params, # Pydantic v2 сам корректно сериализуется
            results=calculation_result,
            valve_id=params.groups[0].valve_id if params.groups else 0 # Просто для совместимости старого поля
        )
        
        # Обновляем имя в сохраненном объекте (т.к. функция create_calc... могла записать старое)
        new_result.stock_name = stock_name
        db.commit()

        return calculation_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Критическая ошибка сервера: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")


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
