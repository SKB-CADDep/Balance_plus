import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.api.router import api_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.error_handlers import setup_exception_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.api.routes import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up", extra={"log_level": log_level})
    yield

log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(log_level)

logger = logging.getLogger(__name__)


class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/health") == -1


logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_exception_handlers(app)

app.include_router(health.router)  # healthcheck
app.include_router(api_router, prefix=settings.API_V1_STR)
