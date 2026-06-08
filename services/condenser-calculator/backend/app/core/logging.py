"""
Настройка глобальной системы логирования микросервиса.

Обеспечивает вывод всех логов приложения в структурированном формате JSON. 
Это необходимо для автоматического сбора, парсинга и агрегации логов 
внешними системами мониторинга (например, ELK-стеком: Elasticsearch/Kibana, 
или Datadog). Также модуль реализует сквозное логирование (tracing) запросов 
через механизм ContextVar.
"""

import json
import logging
from contextvars import ContextVar
from typing import Any

# Контекстная переменная (ContextVar) для хранения уникального идентификатора 
# текущего HTTP-запроса или фоновой задачи. В отличие от глобальных переменных, 
# ContextVar изолирован для каждой асинхронной корутины (asyncio), 
# что предотвращает перемешивание логов разных пользователей при высоких нагрузках.
request_id_ctx_var: ContextVar[str] = ContextVar(
    "request_id", default="nosession"
)


class JSONFormatter(logging.Formatter):
    """
    Кастомный форматтер (обработчик формата) для библиотеки logging.
    
    Перехватывает стандартные текстовые сообщения логгера и упаковывает их 
    (вместе с метаданными вызова и контекстом запроса) в единую JSON-строку.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Форматирует объект записи лога (LogRecord) в JSON.

        Args:
            record (logging.LogRecord): Сырой объект события логирования.

        Returns:
            str: Сериализованная строка в формате JSON без экранирования Unicode.
        """
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx_var.get(),  # Извлекаем ID текущего контекста (запроса)
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }

        # Если логгер был вызван с аргументом `extra={...}`, 
        # подмешиваем эти дополнительные бизнес-поля в корень JSON-объекта.
        if hasattr(record, "extra_info"):
            log_record.update(record.extra_info)

        # Если логгер был вызван с `exc_info=True` (или внутри logger.exception), 
        # извлекаем и форматируем стек вызовов (Traceback) ошибки.
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


def setup_logging():
    """
    Инициализирует и применяет глобальные настройки логирования для приложения.

    Функция перехватывает корневой (root) логгер, удаляет стандартные 
    текстовые обработчики и устанавливает `JSONFormatter`. 
    Также фильтрует (отключает) избыточный "шум" от системных библиотек, 
    таких как веб-сервер Uvicorn.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Очищаем существующие стандартные обработчики (предотвращает дублирование логов)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Создаем консольный обработчик (вывод в stdout) с нашим JSON-форматированием
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    # Подавляем лишние логи доступа от веб-сервера (access logs),
    # так как они дублируют информацию и засоряют систему мониторинга.
    # Ошибки сервера (error logs) оставляем включенными.
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("uvicorn.error").disabled = False