from fastapi import APIRouter
from app.core.celery_app import celery_app

# Импорт самого calculate_async_task отсюда можно удалить, он нам больше не нужен
from app.schemas.calculation import CalculationInput

router = APIRouter(tags=["Async Calculations"])


@router.post("/calculate-async")
def trigger_calculation(input_data: CalculationInput):
    """
    Отправляет задачу на расчет конденсатора в очередь (Redis) через Celery.
    """
    payload = input_data.model_dump()

    # ЯВНО указываем полное имя задачи, которое зарегистрировал воркер
    task = celery_app.send_task("app.worker.calculate_async_task", args=[payload])

    return {"task_id": task.id, "status": "Processing"}


@router.get("/calculate-async/{task_id}")
def get_task_status(task_id: str):
    """
    Проверяет статус асинхронной задачи по её ID.
    """
    task_result = celery_app.AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "status": task_result.state,
    }

    if task_result.state == "SUCCESS":
        # task_result.result содержит словарь, который мы вернули из worker.py
        response.update(task_result.result)
    elif task_result.state == "FAILURE":
        response["error"] = str(task_result.info)

    return response
