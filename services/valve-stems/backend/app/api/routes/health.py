import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok", "service": "valve-stems"}


@router.get("/health/db")
async def health_check_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error("Health check: DB connection failed", extra={"error": str(e)})
        db_status = "disconnected"
        
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