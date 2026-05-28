from celery import Celery
import os

# Берем URL из переменных окружения (в Docker это обычно redis://redis:6379/0)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "valve_stems_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.worker"]  # Указываем, где лежат наши задачи
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)