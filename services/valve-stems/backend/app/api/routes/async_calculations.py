"""
Маршрутизатор асинхронных вычислений.

Отвечает за постановку тяжелых задач по расчету штоков клапанов
в фоновую очередь (Celery + Redis) и предоставление эндпоинтов 
для поллинга (проверки) статуса выполнения этих задач со стороны фронтенда.
"""

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


# WARNING (Технический долг):
# Объявление Pydantic моделей прямо в файле роутера является нарушением
# принципа единой ответственности (SRP). В рамках рефакторинга эти модели
# следует перенести в app/schemas/async_tasks.py.

# =====================================================================
# СХЕМЫ ОТВЕТОВ (Используются только для асинхронного API)
# =====================================================================

class TaskResponse(BaseModel):
    """Схема ответа при успешной постановке задачи в очередь."""
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    """Схема ответа при проверке статуса фоновой задачи."""
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
    Отправляет задачу на расчет клапанов в брокер сообщений (Redis) через Celery.
    Возвращает task_id для последующего отслеживания статуса.
    """
    logger.info(
        "API: async calculation requested",
        extra={"turbine_id": params.turbine_id, "valve_count": len(params.groups)},
    )
    
    # Сериализуем Pydantic модель в dict перед отправкой в Celery,
    # так как брокер настроен на прием исключительно JSON (безопасность)
    payload = params.model_dump()
    
    # Отправляем задачу в очередь (.delay() — это асинхронный вызов)
    task = calculate_valve_stems_async.delay(payload)
    
    return TaskResponse(task_id=task.id, status="Processing")


@router.get(
    "/calculate-async/{task_id}",
    response_model=TaskStatusResponse,
    summary="Получить статус асинхронной задачи",
)
async def get_async_calculation_status(task_id: str):
    """
    Проверяет статус асинхронной задачи в Celery по её уникальному ID.
    Возвращает статус обработки, а в случае успеха — и сам результат.
    """
    task_result = AsyncResult(task_id)
    
    response = TaskStatusResponse(task_id=task_id, status=task_result.status)
    
    if task_result.status == "SUCCESS":
        # Наш воркер возвращает dict вида {"status": "success", "result": {...}}
        worker_data = task_result.result
        
        if worker_data.get("status") == "error":
            # Перехват бизнес-ошибок (Business Logic Errors), которые не уронили воркер
            response.status = "error"
            response.error_type = worker_data.get("error_type")
            response.message = worker_data.get("message")
        else:
            response.result = worker_data.get("result")
            
    elif task_result.status == "FAILURE":
        # Перехват системных падений самого воркера Celery (Tracebacks)
        response.status = "error"
        response.error_type = "CeleryWorkerError"
        response.message = str(task_result.result)
        
    return response
    