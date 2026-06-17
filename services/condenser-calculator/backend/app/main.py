"""
Главный модуль приложения (Entrypoint) микросервиса condenser-calculator.

Отвечает за инициализацию экземпляра FastAPI, настройку глобальных конфигураций 
(CORS, документация OpenAPI), подключение промежуточного ПО (Middlewares), 
инициализацию системы логирования и регистрацию всех API-маршрутизаторов.
"""

import logging

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    calculations, 
    condensers, 
    materials, 
    health, 
    async_calculations
)
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware

# Настройка структурированного JSON-логирования для всего микросервиса
setup_logging()
logger = logging.getLogger(__name__)

api_router = APIRouter()

# Инициализация ядра FastAPI с подтягиванием метаданных из настроек
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
)

# --- Настройка промежуточного ПО (Middlewares) ---
# RequestIDMiddleware добавляет уникальный ID каждому запросу для сквозного трассирования логов
app.add_middleware(RequestIDMiddleware)
# Настройка кросс-доменных запросов (позволяет фронтенду общаться с API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Регистрация маршрутизаторов (Routers) ---
# Сборка всех бизнес-эндпоинтов в единый API-роутер
api_router.include_router(health.router, prefix="/health")
api_router.include_router(calculations.router)
api_router.include_router(condensers.router)
api_router.include_router(materials.router)
api_router.include_router(async_calculations.router)

# Подключение собранного роутера к приложению с глобальным префиксом (обычно /api/v1)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """
    Корневой эндпоинт приложения (Index).

    Служит точкой входа по умолчанию. Часто используется балансировщиками нагрузки 
    в качестве резервного healthcheck-эндпоинта. Возвращает навигационную информацию.

    Returns:
        dict: Краткая информация о сервисе и путях к документации.
    """
    return {
        "service": "condenser-calculator",
        "docs": "/docs",
        "health": "/health",
        "status": "running",
    }
    