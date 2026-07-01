import pytest

from app.api.routes.health import health_check


@pytest.mark.asyncio
async def test_health_check():
    """Тест проверки работоспособности API (GET /health)."""
    result = await health_check()

    assert result == {"status": "ok", "service": "balance-orchestrator"}
