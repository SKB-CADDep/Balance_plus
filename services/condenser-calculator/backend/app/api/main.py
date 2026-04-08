from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter()
# Подключаем роутеры (condensers, materials, calculations добавим в следующих задачах)
api_router.include_router(health.router)
