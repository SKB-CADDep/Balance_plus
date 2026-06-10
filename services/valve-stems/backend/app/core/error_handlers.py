"""
Глобальные обработчики исключений (Global Exception Handlers).

Этот модуль перехватывает кастомные исключения доменной логики 
(например, EntityNotFoundError, PhysicsCalculationError) и преобразует их 
в стандартизированные HTTP-ответы (JSONResponse).
Это обеспечивает единый формат ошибок для фронтенда и защищает 
систему от утечки чувствительной информации (tracebacks) при 500-х ошибках.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    EntityNotFoundError,
    PhysicsCalculationError,
    SteamPropertiesError,
    UnitConversionError,
    ValidationError as AppValidationError,
)
from app.core.logging_config import request_id_ctx
from app.schemas.errors import ErrorResponse

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Регистрирует все глобальные обработчики ошибок в FastAPI приложении.
    Вызывается при старте сервера в основном файле main.py.
    """

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
        # 404: Сущность (например, материал или конденсатор) не найдена в БД
        logger.warning("Entity not found", extra={"detail": exc.details})
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="NOT_FOUND",
                message=exc.message,
                details=exc.details,
                request_id=request_id_ctx.get(),
            ).model_dump(),
        )

    @app.exception_handler(AppValidationError)
    async def validation_error_handler(request: Request, exc: AppValidationError):
        # 422: Ошибка бизнес-валидации (например, нарушено бизнес-правило BR)
        logger.warning("Validation error", extra={"detail": exc.message})
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="VALIDATION_ERROR",
                message=exc.message,
                details=exc.details,
                request_id=request_id_ctx.get(),
            ).model_dump(),
        )

    @app.exception_handler(UnitConversionError)
    async def unit_conversion_handler(request: Request, exc: UnitConversionError):
        # 400: Ошибка конвертации физических величин (uniconv)
        logger.error("Unit conversion error", extra={"detail": exc.details})
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="UNIT_CONVERSION_ERROR",
                message=exc.message,
                details=exc.details,
                request_id=request_id_ctx.get(),
            ).model_dump(),
        )

    @app.exception_handler(PhysicsCalculationError)
    async def physics_error_handler(request: Request, exc: PhysicsCalculationError):
        # 400: Математическое ядро не смогло выполнить расчет
        logger.error("Physics calculation error", extra={"detail": exc.message})
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="CALCULATION_ERROR",
                message=exc.message,
                details=exc.details,
                request_id=request_id_ctx.get(),
            ).model_dump(),
        )

    @app.exception_handler(SteamPropertiesError)
    async def steam_error_handler(request: Request, exc: SteamPropertiesError):
        # 400: Не удалось получить свойства водяного пара
        logger.error("Steam properties error", extra={"detail": exc.details})
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="STEAM_PROPERTIES_ERROR",
                message=exc.message,
                details=exc.details,
                request_id=request_id_ctx.get(),
            ).model_dump(),
        )

    # Глобальный перехватчик для любых необработанных 500-х ошибок
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled server error", extra={"error": str(exc)})
        
        # Использование неявной конкатенации строк вместо слэша (\) 
        # по стандарту PEP 8, чтобы избежать лишних пробелов в тексте ответа.
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="INTERNAL_ERROR",
                message=(
                    "Внутренняя ошибка сервера. "
                    "Пожалуйста, сообщите администратору и передайте Request-ID."
                ),
                details=None,  # Важно: прячем Python Traceback от клиента!
                request_id=request_id_ctx.get(),
            ).model_dump(),
        )
        