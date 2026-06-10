"""
Конфигурация асинхронной очереди задач (Celery).

Инициализирует экземпляр приложения Celery, который используется как веб-сервером (FastAPI) 
для постановки задач в очередь, так и фоновым процессом (Worker) для их выполнения.
В качестве брокера сообщений (message broker) и хранилища результатов (result backend) 
используется Redis.
"""

import os
from celery import Celery

# URL для подключения к брокеру сообщений. 
# По умолчанию используем локальный Redis (удобно для локальной разработки и запуска без докера).
# В production (или Docker Compose) URL перезаписывается через переменную окружения.
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

# Инициализация приложения Celery
celery_app = Celery(
    "condenser_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    # Указываем модули, в которых Celery должен искать функции с декоратором @celery_app.task
    include=["app.worker"] 
)

# Глобальные настройки поведения Celery
celery_app.conf.update(
    # Использование JSON для сериализации защищает от уязвимостей (в отличие от pickle)
    # и позволяет легко читать сообщения в брокере (например, через Redis CLI).
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Настройки часового пояса для отложенных или периодических задач (Celery Beat)
    timezone="UTC",
    enable_utc=True,
    
    # Включаем отслеживание состояния "STARTED" (в работе). 
    # Позволяет фронтенду отличать задачи, ожидающие в очереди (PENDING), от уже выполняющихся.
    task_track_started=True,
)
