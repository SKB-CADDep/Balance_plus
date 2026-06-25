"""
Предстартовый скрипт инициализации и проверки доступности базы данных.

Выполняется перед основным запуском приложения (обычно в Docker entrypoint).
Обеспечивает защиту от состояния "гонки контейнеров" (race condition), гарантируя,
что микросервис не начнет работу до тех пор, пока база данных не будет
полностью готова принимать TCP-соединения.
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
# Зачем здесь декоратор @retry (из библиотеки tenacity):
# Вместо написания ручных циклов "while True" с "time.sleep()", декоратор элегантно 
# оборачивает функцию. Если внутри возникает исключение (база еще не поднялась), 
# tenacity автоматически подождет `wait_seconds` и вызовет функцию снова, 
# вплоть до достижения лимита `max_tries` (5 минут), после чего скрипт упадет окончательно.
@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init(db_engine: Engine) -> None:
    """
    Проверяет активность базы данных путем выполнения тестового SQL-запроса.

    Функция будет выполняться повторно (retries) в случае возникновения исключений
    (например, ConnectionRefusedError).

    Args:
        db_engine (Engine): Настроенный движок SQLAlchemy для подключения к БД.

    Raises:
        Exception: Если база данных недоступна, исключение пробрасывается вверх
            для перехвата декоратором @retry.
    """
    try:
        with Session(db_engine) as session:
            # [ENGINEERING CONTEXT]
            # Почему используется `select(1)`:
            # Это аналог команды "ping" для баз данных. Запрос `SELECT 1;` 
            # не обращается ни к каким таблицам и не нагружает диск, 
            # но при этом проходит полный цикл обработки SQL-сервером. 
            # Если запрос успешен — СУБД 100% жива и готова к работе.
            session.exec(select(1))
    except Exception as e:
        logger.error(e)
        raise e


def main() -> None:
    """
    Точка входа в скрипт предстартовой проверки.
    """
    logger.info("Initializing service")
    init(engine)
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
    