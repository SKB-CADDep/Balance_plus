import logging

from celery.result import AsyncResult
from fastapi import APIRouter
from pydantic import BaseModel

# Импортируем схему входящего запроса
from app.schemas.calculation import MultiCalculationParams

# Импортируем нашу фоновую задачу Celery
from app.worker import calculate_valve_stems_async


router = APIRouter(tags=["Async Calculations"])
logger = logging.getLogger(__name__)


# =====================================================================
# СХЕМЫ ОТВЕТОВ (Используются только для асинхронного API)
# =====================================================================
class TaskResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None
    error_type: str | None = None
    message: str | None = None


# =====================================================================
# ЭНДПОИНТЫ
# =====================================================================
@router.post(
    "/calculate-async",
    response_model=TaskResponse,
    summary="Отправить мульти-расчет в очередь",
)
async def calculate_async(params: MultiCalculationParams):
    """
    Отправляет задачу на расчет клапанов в очередь (Redis) через Celery.
    """
    logger.info(
        "API: async calculation requested",
        extra={"turbine_id": params.turbine_id, "valve_count": len(params.groups)},
    )

    # Сериализуем Pydantic модель в dict перед отправкой в Celery
    payload = params.model_dump()

    # Отправляем задачу в очередь
    task = calculate_valve_stems_async.delay(payload)

    return TaskResponse(task_id=task.id, status="Processing")


@router.get(
    "/calculate-async/{task_id}",
    response_model=TaskStatusResponse,
    summary="Получить статус асинхронной задачи",
)
async def get_async_calculation_status(task_id: str):
    """
    Проверяет статус асинхронной задачи по её ID.
    """
    task_result = AsyncResult(task_id)

    response = TaskStatusResponse(task_id=task_id, status=task_result.status)

    if task_result.status == "SUCCESS":
        # Наш воркер возвращает dict вида {"status": "success", "result": {...}}
        worker_data = task_result.result

        if worker_data.get("status") == "error":
            response.status = "error"
            response.error_type = worker_data.get("error_type")
            response.message = worker_data.get("message")
        else:
            response.result = worker_data.get("result")

    elif task_result.status == "FAILURE":
        response.status = "error"
        response.error_type = "CeleryWorkerError"
        response.message = str(task_result.result)

    return response
