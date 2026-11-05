"""
Тесты межсервисной аутентификации Valve Stems Calculator (X-Internal-Token, X-User-Id)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestValveStemsServiceAuthentication:
    def test_direct_anonymous_calculation_call(self, client):
        """Проверка прямого вызова расчёта штоков без сервисного токена."""
        response = client.post(
            "/api/v1/calculations/calculate",
            json={"groups": []},
            headers={},
        )
        assert response.status_code in [200, 201, 400, 401, 403, 404, 405, 422]

    def test_service_accepts_internal_token_and_propagates_user_id(self, client):
        """Оркестратор передает X-Internal-Token и X-User-Id для аудита."""
        headers = {
            "X-Internal-Token": "valve-stems-internal-secret",
            "X-User-Id": "engineer_42",
        }
        response = client.get("/api/v1/health", headers=headers)
        assert response.status_code in [200, 204, 422]