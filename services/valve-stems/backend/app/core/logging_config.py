"""
Конфигурация логирования приложения (Structured JSON Logging).

Настраивает корневой логгер для вывода всех сообщений в формате JSON (в `stdout`),
что необходимо для корректного парсинга логов в инфраструктуре (например, ELK-стек).
Внедряет паттерн сквозного логирования (Tracing): к каждой записи автоматически 
прикрепляется `request_id` текущего HTTP-запроса через контекстную переменную.
"""

import logging
import sys
from contextvars import ContextVar

from pythonjsonlogger import json as jsonlogger

# Контекстная переменная для хранения уникального идентификатора запроса.
# Позволяет безопасно пробрасывать request_id через асинхронный код FastAPI,
# не передавая его явно в каждую функцию.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    """
    Фильтр для добавления `request_id` во все логи.
    Автоматически извлекает значение из контекста текущей корутины.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


def setup_logging(level: str = "INFO") -> None:
    """
    Инициализация и глобальная настройка логирования.
    
    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR).
    """

    handler = logging.StreamHandler(sys.stdout)

    # Настройка JSON-форматтера с переименованием стандартных полей 
    # в более читаемые/стандартные для систем мониторинга
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger"
        },
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    # Настраиваем корневой логгер (Root Logger), перехватывая все логи
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)

    # Устанавливаем базовый уровень логирования
    log_level = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(log_level)

    # Подавляем шумные стандартные логгеры Uvicorn и SQLAlchemy,
    # чтобы они не забивали консоль служебной информацией
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    