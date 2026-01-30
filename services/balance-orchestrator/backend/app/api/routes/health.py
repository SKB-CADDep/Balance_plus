# api/routes/health.py
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {"status": "ok", "service": "balance-orchestrator"}