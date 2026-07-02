import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    EntityNotFoundError,
    PhysicsCalculationError,
    SteamPropertiesError,
    UnitConversionError,
)
from app.core.exceptions import (
    ValidationError as AppValidationError,
)
from app.core.logging_config import request_id_ctx
from app.schemas.errors import ErrorResponse


logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """Регистрирует все глобальные обработчики ошибок в FastAPI приложении."""

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
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
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="INTERNAL_ERROR",
                message="Внутренняя ошибка сервера. \
                    Пожалуйста, сообщите администратору и передайте Request-ID.",
                details=None,  # Важно: прячем Python Traceback от клиента!
                request_id=request_id_ctx.get(),
            ).model_dump(),
        )
