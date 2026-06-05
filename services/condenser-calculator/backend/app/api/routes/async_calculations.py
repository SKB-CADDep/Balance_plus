"""
Маршрутизатор для асинхронных расчетов конденсаторов.

Предоставляет API-эндпоинты для постановки ресурсоемких расчетных задач
в очередь (через Celery и брокер сообщений) и отслеживания их статуса.
Позволяет не блокировать HTTP-запросы клиента при длительных вычислениях.
"""

from fastapi import APIRouter
from app.core.celery_app import celery_app
from app.schemas.calculation import CalculationInput

router = APIRouter(tags=["Async Calculations"])

@router.post("/calculate-async")
def trigger_calculation(input_data: CalculationInput):
    """
    Отправляет задачу на расчет конденсатора в асинхронную очередь.

    Использует Celery для передачи сериализованных входных данных в фоновый воркер.

    Args:
        input_data (CalculationInput): Входные данные для расчета (геометрия, режимы, 
            свойства материалов и т.д.), прошедшие валидацию Pydantic.

    Returns:
        dict: Словарь с идентификатором созданной задачи и начальным статусом.
            Формат: {"task_id": "<uuid>", "status": "Processing"}
    """
    payload = input_data.model_dump()
    
    # Используется явное строковое имя задачи (зарегистрированное в воркере)
    # для предотвращения циклических импортов и жесткой привязки к модулю worker.
    task = celery_app.send_task("app.worker.calculate_async_task", args=[payload])
    
    return {"task_id": task.id, "status": "Processing"}

@router.get("/calculate-async/{task_id}")
def get_task_status(task_id: str):
    """
    Получает текущий статус и результаты выполнения асинхронной задачи по её ID.

    Опрашивает состояние задачи в Celery (через брокер/backend результатов).
    В зависимости от статуса задачи, возвращает либо прогресс, либо готовые 
    результаты вычислений, либо информацию об ошибке.

    Args:
        task_id (str): Уникальный идентификатор (UUID) задачи.

    Returns:
        dict: Объект ответа с полями:
            - task_id (str): Идентификатор запрошенной задачи.
            - status (str): Статус Celery (PENDING, STARTED, SUCCESS, FAILURE и др.).
            - [остальные поля]: Результат выполнения (если SUCCESS) 
              или ключ "error" с текстом ошибки (если FAILURE).
    """
    task_result = celery_app.AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": task_result.state,
    }
    
    if task_result.state == "SUCCESS":
        # При успешном выполнении подмешиваем результаты расчета в корень ответа
        response.update(task_result.result) 
    elif task_result.state == "FAILURE":
        response["error"] = str(task_result.info)
        
    return response