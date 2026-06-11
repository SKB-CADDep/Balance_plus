"""
Маршрутизатор проверки состояния сервиса (Health Checks).

Предоставляет эндпоинты для инфраструктуры (Docker/Kubernetes),
чтобы оркестратор мог автоматически определять жизнеспособность 
сервиса (liveness) и доступность базы данных (readiness).
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
    """
    Liveness probe: проверяет, что HTTP-сервер FastAPI запущен и принимает запросы.
    (Скрыт из Swagger UI с помощью include_in_schema=False).
    """
    return {"status": "ok", "service": "valve-stems"}


@router.get("/health/db")
async def health_check_db(db: Session = Depends(get_db)):
    """
    Readiness probe: проверяет физическое подключение к PostgreSQL
    путем выполнения простейшего SQL-запроса (SELECT 1).
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error("Health check: DB connection failed", extra={"error": str(e)})
        db_status = "disconnected"
        
        # WARNING (Security / Технический долг):
        # Возврат str(e) прямо в JSON-ответе может случайно раскрыть 
        # чувствительные данные (например, строку подключения с паролем от БД).
        # В продакшене рекомендуется возвращать общий текст "Database unreachable".
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "service": "valve-stems",
                "database": db_status,
                "error": str(e),
            },
        )

    return {
        "status": "ok",
        "service": "valve-stems",
        "database": db_status,
    }
    