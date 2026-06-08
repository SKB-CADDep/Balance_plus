"""
API-маршрутизатор для проверок состояния (Health Checks).

Содержит эндпоинты, используемые оркестраторами (Docker Compose, Kubernetes)
и API Gateway (балансировщиком) для мониторинга жизнеспособности сервиса (Liveness probes)
и его готовности обрабатывать запросы (Readiness probes).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import get_db


router = APIRouter(tags=["Health"])


@router.get("/", include_in_schema=True)
def health_check():
    """
    Легковесная проверка доступности сервиса (Liveness Probe).

    Не выполняет ресурсоемких операций, зависимостей или запросов к БД. Используется
    для подтверждения того, что сам процесс FastAPI запущен и не завис.

    Returns:
        dict: Словарь с базовой информацией о сервисе (статус, имя, версия).
    """
    return {
        "status": "ok",
        "service": "condenser-calculator",
        "version": "0.1.0"
    }


@router.get("/db", include_in_schema=True)
def health_check_db(db: Session = Depends(get_db)):
    """
    Глубокая проверка инфраструктуры с подключением к БД (Readiness Probe).

    Проверяет, может ли сервис успешно общаться с PostgreSQL.
    Если этот эндпоинт возвращает ошибку, балансировщик (например, Nginx) 
    или оркестратор не должен временно направлять клиентский трафик на этот контейнер.

    Args:
        db (Session): Сессия базы данных (Dependency Injection).

    Returns:
        dict: Словарь с подтверждением успешного подключения к БД.

    Raises:
        HTTPException (503): Если база данных недоступна (таймаут, отказ в доступе). 
            Возвращает статус HTTP_503_SERVICE_UNAVAILABLE с деталями ошибки.
    """
    try:
        # Выполняем максимально легковесный SQL-запрос ("пинг" базы данных), 
        # чтобы убедиться, что пул соединений с PostgreSQL функционирует корректно.
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected",
            "details": "PostgreSQL is reachable"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "database": "disconnected",
                "details": str(e)
            }
        )