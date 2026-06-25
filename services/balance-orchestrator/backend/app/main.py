# main.py

"""
Главный модуль (Entrypoint) микросервиса balance-orchestrator.

Оркестратор выступает в роли API-шлюза (BFF - Backend for Frontend) и 
координатора бизнес-логики. Он связывает клиентскую часть (UI) с внешними 
системами (GitLab, базы данных) и расчетными ядрами (модули БТР, БПР, БВП).
Отвечает за инициализацию FastAPI, настройку middleware и сборку всех роутеров.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import calculations, config, geometries, health, projects, tasks, user

# Инициализация приложения FastAPI с расширенным описанием для Swagger UI
app = FastAPI(
    title="Balance+ Orchestrator API",
    description=(
        "Центральный сервис оркестрации задач для инженерных расчетов.\n\n"
        "**Основные функции микросервиса:**\n"
        "* Управление жизненным циклом расчетных задач (интеграция с GitLab Issues).\n"
        "* Сохранение и версионирование математических расчетов.\n"
        "* Управление манифестами геометрий оборудования.\n\n"
        "_Документация сгенерирована автоматически на основе исходного кода._"
    ),
    version="0.1.0",
)

# [ENGINEERING CONTEXT]
# Почему allow_origins=["*"]: На этапе активной разработки и во внутреннем защищенном контуре 
# предприятия мы разрешаем любые Origin (CORS), чтобы фронтенд-разработчики могли 
# стучаться к API с локалхоста. При выходе в строгий Production этот список 
# рекомендуется ограничить конкретными доменами UI для предотвращения CSRF-атак.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ПОДКЛЮЧЕНИЕ РОУТЕРОВ (API ЭНДПОИНТОВ) ---
# Системные роуты (без префикса v1)
app.include_router(health.router)

# Бизнес-роуты предметной области (API Version 1)
app.include_router(geometries.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(calculations.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(config.router, prefix="/api/v1")


@app.get(
    "/",
    tags=["System"],
    summary="Приветственный экран сервиса",
)
async def root() -> dict[str, str]:
    """
    Корневой эндпоинт приложения.

    Используется для быстрой проверки доступности сервиса из браузера 
    и маршрутизации инженеров/разработчиков к интерактивной документации.

    Returns:
        dict[str, str]: JSON-объект с названием сервиса и ссылками на Swagger (/docs) 
        и эндпоинт проверки жизнеспособности (/health).
    """
    return {
        "service": "Balance+ Orchestrator",
        "docs": "/docs",
        "health": "/health",
    }
    