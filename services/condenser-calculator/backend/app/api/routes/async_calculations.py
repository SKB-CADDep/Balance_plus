from fastapi import APIRouter
from celery.result import AsyncResult
from app.worker import calculate_async_task

router = APIRouter(tags=["Async Calculations"])

@router.post("/calculate-async")
def trigger_calculation(input_data: dict):
    """
    Отправляет задачу на расчет в очередь (Redis) через Celery.
    """
    # .delay() ставит задачу в очередь
    task = calculate_async_task.delay(input_data)
    
    return {"task_id": task.id, "status": "Processing"}

@router.get("/calculate-async/{task_id}")
def get_task_status(task_id: str):
    """
    Проверяет статус асинхронной задачи по её ID.
    """
    task_result = AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": task_result.state,
    }
    
    if task_result.state == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.state == "FAILURE":
        response["error"] = str(task_result.info)
        
    return response