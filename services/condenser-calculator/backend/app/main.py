"""
Точка входа (Entry point) микросервиса Condenser Calculator.

Инициализирует приложение FastAPI, настраивает глобальные middleware 
(CORS, трейсинг запросов), подключает логирование и собирает все маршруты (routers) 
в единое дерево API. Объект `app` используется ASGI-сервером для запуска.
"""
import logging
from typing import Dict

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Импорты роутеров (исправлено дублирование async_calculations)
from app.api.routes import calculations, condensers, materials, health, async_calculations
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware

# Инициализируем структурированное логирование до старта приложения, 
# чтобы перехватывать ошибки даже на этапе загрузки роутеров.
setup_logging()
logger = logging.getLogger(__name__)

api_router = APIRouter()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Микросервис для выполнения тепловых и гидравлических расчетов конденсаторов.",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
)

# --- Middlewares ---
# Важно: в FastAPI middleware выполняются в обратном порядке от их добавления.
# RequestIDMiddleware вешает уникальный ID на каждый запрос для сквозного логгирования.
app.add_middleware(RequestIDMiddleware)

# Настройка CORS для взаимодействия с фронтендом (Vue/React).
# TODO: Для production окружения заменить allow_origins=["*"] на конкретные домены.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Маршрутизация (Routing) ---
# Группируем все эндпоинты в api_router, чтобы потом разом повесить на них 
# глобальный префикс API (по умолчанию /api/v1).
api_router.include_router(health.router, prefix="/health")
api_router.include_router(calculations.router)
api_router.include_router(condensers.router)
api_router.include_router(materials.router)
api_router.include_router(async_calculations.router)

# Подключаем собранный роутер к основному приложению
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["System"])
async def root() -> Dict[str, str]:
    """
    Корневой эндпоинт приложения (Landing route).
    
    Используется балансировщиками нагрузки (Load Balancers) и разработчиками 
    для быстрой проверки того, что приложение запущено и отвечает на запросы, 
    без необходимости дергать базу данных или сложную логику.

    Returns:
        Dict: Базовая метаинформация о сервисе и ссылки на документацию.
    """
    return {
        "service": "condenser-calculator",
        "docs": "/docs",
        # Динамически подставляем префикс API, чтобы ссылка всегда была актуальной
        "health": f"{settings.API_V1_STR}/health", 
        "status": "running",
    }
