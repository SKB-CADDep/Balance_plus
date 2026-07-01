from collections.abc import Generator

from app.core.database import SessionLocal


def get_db() -> Generator:
    """
    Инъекция зависимости для получения сессии базы данных.
    После завершения запроса сессия автоматически закрывается.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
