from fastapi import APIRouter

from app.api.routes import health, calculations

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(
    calculations.router, prefix="/calculate", tags=["Calculations"])
