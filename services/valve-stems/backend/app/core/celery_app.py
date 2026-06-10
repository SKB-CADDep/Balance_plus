"""
Конфигурация Celery-приложения (Worker) для фоновых задач.

Отвечает за инициализацию асинхронной очереди задач для микросервиса 'Valve Stems' 
(Штоки клапанов). Тяжелые математические вычисления делегируются в этот воркер, 
чтобы не блокировать основной Event Loop FastAPI (HTTP-запросы).
В качестве брокера сообщений и backend'а для хранения результатов используется Redis.
"""

import os

from celery import Celery

# WARNING (Технический долг):
# Использование os.getenv напрямую в обход Pydantic Settings (например, app.core.config) 
# является антипаттерном для крупных FastAPI-приложений. В будущем рекомендуется 
# перенести REDIS_URL в единый класс конфигурации для строгой типизации и валидации.
# 
# Значение по умолчанию "redis://redis:6379/0" ориентировано на запуск внутри Docker-сети.
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "valve_stems_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.worker"]  # Указываем модуль, в котором зарегистрированы задачи (@celery_app.task)
)

# Строгая настройка сериализации задач исключительно в JSON для безопасности 
# (предотвращение атак через pickle) и кросс-платформенной совместимости.
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
