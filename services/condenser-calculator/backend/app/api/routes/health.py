from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import get_db

router = APIRouter(tags=["Health"])

@router.get("/health", include_in_schema=False)
def health_check() -> dict:
    """Быстрая проверка доступности сервиса (для Docker)."""
    return {"status": "ok", "service": "condenser-calculator"}

@router.get("/health/db", include_in_schema=False)
def health_check_db(db: Session = Depends(get_db)) -> dict:
    """Глубокая проверка с подключением к PostgreSQL."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "database": "disconnected", "details": str(e)}
        )
