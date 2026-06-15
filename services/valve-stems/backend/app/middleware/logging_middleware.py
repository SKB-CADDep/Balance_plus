"""
Middleware для централизованного логирования HTTP-запросов.

Обеспечивает сквозное отслеживание (Distributed Tracing) запросов в микросервисе:
- Генерирует уникальный Request-ID для каждого входящего запроса.
- Замеряет время выполнения эндпоинта (с точностью до миллисекунд).
- Формирует структурированные логи (access logs) при старте, завершении и падении запросов.
"""

import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.logging_config import request_id_ctx

logger = logging.getLogger("app.middleware.access")

# [ENGINEERING CONTEXT]
# Зачем нужен SILENT_PATHS:
# Системы оркестрации (например, Kubernetes или Docker) и инструменты мониторинга 
# (Prometheus) могут опрашивать эндпоинты жизнеспособности (/health) каждую секунду.
# Если мы будем логировать эти технические запросы, наши логи мгновенно засорятся "мусором", 
# скрывая реальную бизнес-активность. Эти пути намеренно исключены из потока логов.
SILENT_PATHS = {"/health", "/health/db", "/api/v1/health", "/openapi.json", "/docs", "/redoc", "/metrics"}

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP Middleware для перехвата и логирования жизненного цикла запросов.

    Класс оборачивает каждый входящий запрос в FastAPI/Starlette, позволяя
    выполнять код ДО передачи запроса в роутер (маршрутизатор) и ПОСЛЕ
    формирования ответа.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Перехватывает запрос, внедряет Request-ID, вызывает обработчик и логирует результат.

        Args:
            request (Request): Объект входящего HTTP-запроса.
            call_next (Callable): Функция, передающая запрос дальше по цепочке 
                middleware вплоть до конечного эндпоинта.

        Returns:
            Response: Сформированный HTTP-ответ (с внедренным заголовком X-Request-ID).

        Raises:
            Exception: Пробрасывает неперехваченные исключения вверх после их логирования.
        """
        # Генерация уникального идентификатора транзакции
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
            
            # [ENGINEERING CONTEXT]
            # Зачем мы добавляем `X-Request-ID` в заголовки (Headers) ответа:
            # Если у пользователя на фронтенде (UI) возникнет ошибка (например, 500 Internal Server Error), 
            # фронтенд может перехватить этот заголовок и показать пользователю сообщение: 
            # "Произошла ошибка. Обратитесь в техподдержку (Код ошибки: 550e8400-e29b-41d4-a716-446655440000)".
            # Разработчики смогут мгновенно найти эту транзакцию в логах (Kibana/ELK) по этому ID.
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
        