from fastapi import APIRouter

from app.api.routes import utils

api_router = APIRouter()

api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
