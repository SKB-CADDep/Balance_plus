"""
Модуль инициализации подключения к базе данных.

Настраивает синхронный движок (engine) SQLAlchemy для взаимодействия
с PostgreSQL и создает фабрику сессий (SessionLocal) для инъекции
зависимостей (Dependency Injection) в эндпоинты FastAPI.
"""

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


# Создание синхронного движка базы данных на основе настроек из Pydantic
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

# Фабрика сессий. Отключаем autocommit и autoflush для безопасного управления
# транзакциями на уровне бизнес-логики (через явные db.commit() и db.rollback())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# WARNING (Технический долг):
# В других микросервисах (например, condenser-calculator) используется современный 
# подход SQLAlchemy 2.0 с наследованием от класса `DeclarativeBase`.
# Здесь же временно оставлен устаревший (legacy) метод `declarative_base()`.
# В рамках будущего рефакторинга рекомендуется привести все модели к стандарту SA 2.0.
Base = sqlalchemy.orm.declarative_base()


def init_db() -> None:
    """
    Функция-заглушка для первичной инициализации базы данных.
    
    В текущей архитектуре структура БД управляется исключительно
    миграциями Alembic (или SQL-дампами, как указано в README), 
    поэтому прямое создание таблиц через SQLAlchemy здесь не выполняется.
    """
    pass

