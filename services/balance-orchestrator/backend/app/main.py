# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, geometries, tasks, user, calculations, projects

app = FastAPI(
    title="Balance+ Orchestrator",
    description="Сервис оркестрации задач для инженерных расчётов",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(health.router)
app.include_router(geometries.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(calculations.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "service": "Balance+ Orchestrator",
        "docs": "/docs",
        "health": "/health",
    }