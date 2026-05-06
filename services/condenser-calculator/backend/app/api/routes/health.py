from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import get_db


router = APIRouter(tags=["Health"])


@router.get("/", include_in_schema=True)
def health_check():
    """Быстрая проверка доступности сервиса (для Docker/K8s)."""
    return {
        "status": "ok",
        "service": "condenser-calculator",
        "version": "0.1.0"
    }


@router.get("/db", include_in_schema=True)
def health_check_db(db: Session = Depends(get_db)):
    """Глубокая проверка с подключением к PostgreSQL."""
    try:
        # Простая проверка связи
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
