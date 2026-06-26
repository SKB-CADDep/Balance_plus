import logging

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import calculations, condensers, health, materials
from app.core.config import settings

# Если вы хотите, чтобы таблицы создались мгновенно без настройки Alembic
# from app.core.database import engine
# from app.models.base import Base

api_router = APIRouter()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck на корневом уровне
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(
    calculations.router, prefix="/calculations", tags=["calculations"]
)
api_router.include_router(condensers.router, prefix="/condensers", tags=["condensers"])
api_router.include_router(materials.router, prefix="/materials", tags=["materials"])

# Все бизнес-роуты под /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root() -> dict:
    return {
        "service": "condenser-calculator",
        "docs": "/docs",
        "health": "/health",
        "status": "running",
    }
