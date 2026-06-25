"""
Промежуточное ПО (Middleware) для сквозного трассирования HTTP-запросов.

Реализует паттерн перехвата всех входящих запросов к приложению. 
Модуль отвечает за генерацию уникальных идентификаторов запроса (Request ID),
измерение времени ответа API и передачу этих метаданных в глобальную систему 
структурированного логирования.
"""

import uuid
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import request_id_ctx_var

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware для внедрения X-Request-ID и профилирования запросов.

    Каждый HTTP-запрос, поступающий в FastAPI, проходит через метод `dispatch`.
    Класс генерирует уникальный токен (или читает его из заголовков балансировщика 
    нагрузки Nginx/Ingress) и пробрасывает его во все логи, созданные во время 
    выполнения этого запроса. Это критически важно для дебаггинга в микросервисной 
    архитектуре (Tracing).
    """

    async def dispatch(self, request: Request, call_next):
        """
        Перехватывает запрос до и после его обработки роутерами FastAPI.

        Args:
            request (Request): Объект входящего HTTP-запроса от клиента.
            call_next (Callable): Функция (корутина), передающая управление 
                следующему слою приложения (или конечному эндпоинту).

        Returns:
            Response: Объект HTTP-ответа, в который внедрен заголовок X-Request-ID.
        """
        # 1. Извлечение или генерация Request ID:
        # Если API Gateway (например, Nginx) уже присвоил запросу ID, используем его.
        # Иначе генерируем новый уникальный UUID версии 4.
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # 2. Устанавливаем ID в изолированный контекст переменной (ContextVar).
        # Все логи (logger.info), вызванные в рамках этого запроса где угодно в коде, 
        # будут автоматически подтягивать этот ID.
        token = request_id_ctx_var.set(request_id)

        start_time = time.perf_counter()

        try:
            # 3. Передача управления внутрь приложения (к эндпоинту).
            # Выполнение кода здесь приостанавливается до завершения расчета.
            response = await call_next(request)

            process_time = (time.perf_counter() - start_time) * 1000

            # 4. Логирование результатов запроса (Access Log).
            # Словарь `extra_info` будет распарсен кастомным JSONFormatter (из logging.py)
            # и помещен в корень JSON-объекта лога для удобного поиска в ELK/Kibana.
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

            # 5. Внедряем ID в заголовки ответа, чтобы фронтенд или клиент 
            # мог сообщить его техподдержке в случае ошибки.
            response.headers["X-Request-ID"] = request_id
            return response

        finally:
            # 6. Очистка контекста.
            # Обязательно сбрасываем ContextVar, чтобы предотвратить утечки памяти 
            # в пуле асинхронных воркеров веб-сервера.
            request_id_ctx_var.reset(token)