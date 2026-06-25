"""
Маршрутизатор проверки состояния сервиса (Health Checks).

Предоставляет liveness и readiness probes для использования
в Docker, Kubernetes и других системах оркестрации.
"""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", include_in_schema=False)
async def health_check():
    """Liveness probe — проверяет, что приложение запущено."""
    return {"status": "ok", "service": "valve-stems"}


@router.get("/health/db")
async def health_check_db(db: Session = Depends(get_db)):
    """
    Readiness probe — проверяет подключение к базе данных.

    Возвращает:
        - 200 OK, если БД доступна
        - 503 Service Unavailable, если БД недоступна

    Никогда не возвращает детали ошибки пользователю/оркестратору
    (в целях безопасности).
    """
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "service": "valve-stems",
            "database": "connected",
        }

    except Exception as exc:
        logger.error("Health check: Database connection failed", exc_info=True)

        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "valve-stems",
                "database": "unreachable",
            },
        )

