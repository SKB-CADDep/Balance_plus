import logging
import sys
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger
from app.core.config import settings

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

class RequestIdFilter(logging.Filter):
    """Фильтр для добавления request_id во все логи."""
    def filter(self, record):
        record.request_id = request_id_ctx.get()
        return True

def setup_logging(level: str = "INFO"):
    """Инициализация структурированного JSON логирования."""
    
    handler = logging.StreamHandler(sys.stdout)
    
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

    # Настраиваем корневой логгер
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    
    # Устанавливаем уровень логирования
    log_level = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(log_level)

    # Подавляем шумные стандартные логгеры Uvicorn и SQLAlchemy
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)