from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "valve_stems_worker",
    broker=settings.CELERY_REDIS_URL,
    backend=settings.CELERY_REDIS_URL,
    include=["app.worker"],  # Указываем, где лежат наши задачи
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
