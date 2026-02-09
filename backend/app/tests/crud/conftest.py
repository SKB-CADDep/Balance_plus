import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Фикстура для создания сессии базы данных
@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# Переопределяем зависимость get_db для использования тестовой сессии
@pytest.fixture(scope="function")
def override_get_db(db_session):
    def _get_db():
        try:
            yield db_session
        finally:
            pass

    return _get_db


# Фикстура для использования переопределённого get_db в тестах
@pytest.fixture(scope="function")
def client(override_get_db, monkeypatch):
    monkeypatch.setattr("backend.app.dependencies.get_db", override_get_db)
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    return client
