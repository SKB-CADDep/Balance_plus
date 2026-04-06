from typing import Generator
from app.core.database import SessionLocal

def get_db() -> Generator:
    """Зависимость для выдачи сессии БД в эндпоинтах."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()