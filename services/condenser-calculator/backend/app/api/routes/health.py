from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import get_db


router = APIRouter(tags=["Health"])


@router.get("/", include_in_schema=True)
def health_check():
    """Быстрая проверка доступности сервиса (для Docker/K8s)."""
    return {"status": "ok", "service": "condenser-calculator", "version": "0.1.0"}


@router.get("/db", include_in_schema=True)
def health_check_db(db: Session = Depends(get_db)):
    """Глубокая проверка PostgreSQL и обязательных таблиц приложения."""
    try:
        tables = db.execute(
            text(
                "SELECT to_regclass('public.condensers'), "
                "to_regclass('public.materials')"
            )
        ).one()
        if any(table is None for table in tables):
            raise RuntimeError("Required database tables are missing")
        return {
            "status": "ok",
            "database": "connected",
            "details": "PostgreSQL is reachable and schema is initialized",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "database": "disconnected", "details": str(e)},
        )
