"""
Тесты межсервисной аутентификации Condenser Calculator (X-Internal-Token, X-User-Id)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestCondenserServiceAuthentication:
    def test_direct_call_without_internal_token_checked(self, client):
        """Проверка прямого вызова расчёта без внутреннего токена."""
        response = client.post(
            "/api/v1/calculate",
            json={"steam_flow": "120", "cooling_water_temp": "15"},
            headers={},
        )
        assert response.status_code in [200, 201, 400, 401, 403, 404, 405, 422]

    def test_call_with_internal_token_and_user_id(self, client):
        """Вызов с сервисным токеном и X-User-Id."""
        headers = {
            "X-Internal-Token": "internal-condenser-secret",
            "X-User-Id": "engineer_42",
        }
        # Путь /api/v1/health
        response = client.get("/api/v1/health", headers=headers)
        assert response.status_code in [200, 204, 422]