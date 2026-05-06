import json
import logging
from contextvars import ContextVar
from typing import Any

# ContextVar для хранения request_id в текущем контексте выполнения
request_id_ctx_var: ContextVar[str] = ContextVar(
    "request_id", default="nosession")


class JSONFormatter(logging.Formatter):
    """
    Кастомный логгер для вывода в формате JSON.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx_var.get(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }

        # Добавляем дополнительные поля из extra, если они есть
        if hasattr(record, "extra_info"):
            log_record.update(record.extra_info)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


def setup_logging():
    """
    Настройка логирования: замена стандартного обработчика на JSON.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Очищаем существующие обработчики
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Создаем консольный обработчик с JSON форматированием
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    # Подавляем лишние логи от сторонних библиотек
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("uvicorn.error").disabled = False
