from fastapi import APIRouter
from app.api.routes import turbines, valves, calculations, utils, drawio

api_router = APIRouter()

# Подключаем наши новые модули
api_router.include_router(turbines.router, prefix="/turbines", tags=["turbines"])
api_router.include_router(valves.router, prefix="/valves", tags=["valves"])
api_router.include_router(calculations.router, tags=["calculations"]) 

# Старые роутеры
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(drawio.router, tags=["drawio"])
