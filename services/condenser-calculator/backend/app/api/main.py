from fastapi import APIRouter

from app.api.routes import calculations, condensers, materials, health

api_router = APIRouter()

api_router.include_router(calculations.router)
api_router.include_router(condensers.router)
api_router.include_router(materials.router)
api_router.include_router(health.router)