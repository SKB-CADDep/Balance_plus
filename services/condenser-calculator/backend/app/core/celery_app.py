import os
from celery import Celery

# По умолчанию используем локальный Redis (для запуска без докера)
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "condenser_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.worker"],  # Указываем, где искать задачи
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
