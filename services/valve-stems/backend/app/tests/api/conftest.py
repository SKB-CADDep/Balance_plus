import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.dependencies import get_db
from app.main import app


@pytest.fixture(scope="session")
def engine():
    """
    Создаёт engine с SQLite in-memory.
    Прикрепляем схему 'autocalc' через ATTACH DATABASE
    """
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def _attach_autocalc_schema(dbapi_conn, connection_record):
        dbapi_conn.execute("ATTACH DATABASE ':memory:' AS autocalc")

    Base.metadata.create_all(bind=test_engine)

    yield test_engine

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    """
    Создаёт сессию для каждого теста с rollback после завершения.
    """
    connection = engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def override_get_db(db_session):
    """Переопределяет get_db для тестов."""

    def _get_db():
        try:
            yield db_session
        finally:
            pass

    return _get_db


@pytest_asyncio.fixture
async def async_client(override_get_db):
    """Создает async HTTP-клиент с подменой get_db на тестовую сессию."""
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client
    finally:
        app.dependency_overrides.clear()
