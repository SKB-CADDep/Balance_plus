"""
Скрипт предстартовой проверки базы данных для тестового окружения (Test Environment).

Используется в CI/CD пайплайнах (например, GitLab CI) или при локальном запуске 
автотестов (pytest) для гарантии того, что изолированная тестовая БД полностью поднялась 
и готова принимать соединения. Предотвращает ложное падение тестов из-за состояния 
"гонки контейнеров" (race condition).
"""

import logging

from sqlalchemy import Engine
from sqlmodel import Session, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.database import engine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


# [ENGINEERING CONTEXT]
# Зачем нужен отдельный скрипт для тестов (похожий на backend_pre_start.py):
# В современных CI/CD пайплайнах запуск основного приложения и запуск тестов 
# разнесены по разным стадиям (stages) и изолированным контейнерам. 
# Тестовому контейнеру требуется собственный независимый механизм ожидания 
# поднятия тестовой (не production!) базы данных перед запуском набора тестов.

@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init(db_engine: Engine) -> None:
    """
    Проверяет активность базы данных путем выполнения простого SQL-запроса.

    Функция обернута в декоратор @retry, который будет повторять попытки
    подключения каждые `wait_seconds` до достижения лимита `max_tries`.

    Args:
        db_engine (Engine): Настроенный движок SQLAlchemy для подключения к БД.

    Raises:
        Exception: Если БД недоступна, исключение перехватывается декоратором @retry.
    """
    try:
        # Try to create session to check if DB is awake
        with Session(db_engine) as session:
            # [ENGINEERING CONTEXT]
            # Выполнение `select(1)` выступает в роли "ping" для базы данных.
            # Это самый легковесный запрос, который гарантированно проверяет
            # работоспособность пула соединений и самого SQL-сервера, не нагружая диск.
            session.exec(select(1))
    except Exception as e:
        logger.error(e)
        raise e


def main() -> None:
    """
    Точка входа в скрипт. Запускает цикл ожидания доступности тестовой БД.
    """
    logger.info("Initializing service")
    init(engine)
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
    