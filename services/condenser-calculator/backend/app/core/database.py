"""
Модуль инициализации подключения к базе данных (SQLAlchemy).

Отвечает за создание пула соединений (Engine) и фабрики сессий (SessionLocal).
Этот модуль является фундаментом для работы с PostgreSQL и напрямую используется 
в слое внедрения зависимостей (dependencies.py) для выдачи независимых сессий 
каждому HTTP-запросу (или фоновой задаче Celery).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Создание глобального движка базы данных (Connection Pool).
# pool_pre_ping=True: Включает пессимистическую проверку соединений. Перед тем как выдать 
# соединение из пула для выполнения запроса, SQLAlchemy делает легкий тестовый "ping" к БД. 
# Это надежно предотвращает ошибки обрыва соединения (connection closed/dropped), 
# если база данных была перезагружена или сетевое подключение временно пропало.
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
)

# Создание фабрики сессий.
# Каждый вызов SessionLocal() возвращает новую изолированную сессию (транзакцию) к БД.
# autocommit=False: Мы управляем транзакциями вручную (требуется явный вызов db.commit()), 
#   что позволяет откатывать изменения (db.rollback) при возникновении ошибок.
# autoflush=False: Изменения объектов в памяти не отправляются в БД автоматически 
#   перед каждым SQL-запросом, что дает разработчику больший контроль над производительностью.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)