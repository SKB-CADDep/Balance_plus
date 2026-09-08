import logging
import os

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import calculations, config, geometries, health, projects, tasks, user
from app.core.security import get_current_user


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


app = FastAPI(
    title="Balance+ Orchestrator",
    description="Сервис оркестрации задач для инженерных расчётов",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Публичные маршруты
app.include_router(health.router)

# Все маршруты /api/v1 требуют валидный access token.
api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_current_user)])
api_router.include_router(geometries.router)
api_router.include_router(tasks.router)
api_router.include_router(user.router)
api_router.include_router(calculations.router)
api_router.include_router(projects.router)
api_router.include_router(config.router)
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "service": "Balance+ Orchestrator",
        "docs": "/docs",
        "health": "/health",
    }
