"""
Главный маршрутизатор (Root Router) API сервиса 'Valve Stems'.

Собирает (агрегирует) все дочерние роутеры из модуля `app.api.routes`
и подключает их к единому объекту `api_router`. Этот объект затем
импортируется в `main.py` для инициализации FastAPI приложения.
"""

from fastapi import APIRouter

from app.api.routes import (
    async_calculations,
    calculations,
    drawio,
    turbines,
    utils,
    valves,
)

api_router = APIRouter()

# Подключение предметных (бизнес) маршрутов
api_router.include_router(turbines.router, prefix="/turbines", tags=["turbines"])
api_router.include_router(valves.router, prefix="/valves", tags=["valves"])

# Синхронные и асинхронные расчеты (эндпоинты вынесены в корень или имеют свои префиксы внутри)
api_router.include_router(calculations.router, tags=["calculations"])
api_router.include_router(async_calculations.router)

# Вспомогательные сервисы (справочники, генерация схем)
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(drawio.router)
