"""
Тесты для health check endpoints.
"""
import pytest



async def test_health_check(async_client):
    """Тест проверки работоспособности API (GET /health)."""
    response = await async_client.get("/health")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "ok"



async def test_health_check_db(async_client, db_session):
    """Тест проверки коннекта к тестовой БД (GET /health/db)."""
    response = await async_client.get("/health/db")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["database"] == "connected"
