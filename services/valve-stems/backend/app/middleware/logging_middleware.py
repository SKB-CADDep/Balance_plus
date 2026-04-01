import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.logging_config import request_id_ctx

logger = logging.getLogger("app.middleware.access")

SILENT_PATHS = {"/health", "/health/db", "/api/v1/health", "/openapi.json", "/docs", "/redoc", "/metrics"}

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = str(uuid.uuid4())
        request_id_ctx.set(rid)

        path = request.url.path
        method = request.method
        is_silent = path in SILENT_PATHS

        if not is_silent:
            logger.info(
                "Incoming request", 
                extra={"method": method, "path": path}
            )

        start = time.perf_counter()
        
        try:
            response = await call_next(request)
            
            response.headers["X-Request-ID"] = rid
            
            duration = round((time.perf_counter() - start) * 1000, 1)
            
            if not is_silent:
                logger.info(
                    "Request completed", 
                    extra={"status_code": response.status_code, "duration_ms": duration, "method": method, "path": path}
                )
                
            return response
            
        except Exception as e:
            duration = round((time.perf_counter() - start) * 1000, 1)
            logger.error(
                "Request failed with unhandled exception",
                extra={"status_code": 500, "duration_ms": duration, "method": method, "path": path, "error": str(e)},
                exc_info=True
            )
            raise