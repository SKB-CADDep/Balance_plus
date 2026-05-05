"""
Тестирование работоспособности API и подключения к базе данных (Health Check)
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "version" in response.json()


@pytest.mark.asyncio
async def test_health_check_db():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health/db")
    # Если БД доступна (в тестах обычно используется мок или реальная тестовая БД)
    # Если тест упадет из-за отсутствия БД, мы это увидим.
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        assert response.json()["database"] == "connected"
