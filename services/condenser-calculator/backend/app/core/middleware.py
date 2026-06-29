import uuid
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import request_id_ctx_var

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware для проброса X-Request-ID и логирования запросов.
    """

    async def dispatch(self, request: Request, call_next):
        # 1. Генерируем или берем существующий Request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # 2. Устанавливаем в контекст для логгера
        token = request_id_ctx_var.set(request_id)

        start_time = time.perf_counter()

        try:
            # 3. Выполняем запрос
            response = await call_next(request)

            process_time = (time.perf_counter() - start_time) * 1000

            # 4. Логируем результат
            logger.info(
                f"Completed {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "extra_info": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": round(process_time, 2),
                        "client_ip": request.client.host if request.client else "unknown"
                    }
                }
            )

            # 5. Добавляем ID в заголовок ответа
            response.headers["X-Request-ID"] = request_id
            return response

        finally:
            # Сбрасываем контекст
            request_id_ctx_var.reset(token)
