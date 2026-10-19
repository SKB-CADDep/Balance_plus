"""
Тесты безопасности и авторизации сохранения/чтения расчётов (/api/v1/calculations/save, /latest)
"""

from unittest.mock import MagicMock, patch

import gitlab.exceptions
import pytest
from fastapi.testclient import TestClient

from app.core.gitlab_adapter import GitLabConfigurationError
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


VALID_SAVE_PAYLOAD = {
    "task_iid": 10,
    "project_id": 1,
    "app_type": "valves",
    "input_data": {"P_fresh": 130, "T_fresh": 555},
    "output_data": {"total_leakage": 0.45},
    "commit_message": "Тестовый расчёт штоков",
}


# ============================================================================
# 1. ЗАЩИТА ЭНДПОИНТА СОХРАНЕНИЯ РАСЧЁТА: POST /api/v1/calculations/save
# ============================================================================
class TestCalculationsSaveSecurity:
    def test_save_calculation_success(self, client):
        """Успешное сохранение расчёта и коммит в репозиторий проекта."""
        mock_commit = MagicMock()
        mock_commit.id = "commit-sha-777"
        mock_commit.web_url = "http://git.local/project/-/commit/777"

        with patch("app.api.routes.calculations.gitlab_client.find_branch_by_issue_iid", return_value="issue/10-task"), \
             patch("app.api.routes.calculations.gitlab_client.create_commit_multiple", return_value=mock_commit) as mock_create_commit:
            
            response = client.post("/api/v1/calculations/save", json=VALID_SAVE_PAYLOAD)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "saved"
        assert data["commit_id"] == "commit-sha-777"
        assert data["path"] == "calculations/valves/current"
        mock_create_commit.assert_called_once()

    def test_save_calculation_unauthorized_token_error(self, client):
        """Попытка сохранения с невалидным/отозванным токеном возвращает 401 Unauthorized."""
        auth_error = gitlab.exceptions.GitlabAuthenticationError("401 Token invalid")

        with patch("app.api.routes.calculations.gitlab_client.find_branch_by_issue_iid", side_effect=auth_error):
            response = client.post("/api/v1/calculations/save", json=VALID_SAVE_PAYLOAD)

        assert response.status_code == 401
        assert response.json()["detail"] == "Ошибка авторизации в GitLab"

    def test_save_calculation_unconfigured_gitlab(self, client):
        """Попытка сохранения без заданного токена в .env возвращает 503 Service Unavailable."""
        config_error = GitLabConfigurationError("GITLAB_PRIVATE_TOKEN отсутствует")

        with patch("app.api.routes.calculations.gitlab_client.find_branch_by_issue_iid", side_effect=config_error):
            response = client.post("/api/v1/calculations/save", json=VALID_SAVE_PAYLOAD)

        assert response.status_code == 503
        assert "GITLAB_PRIVATE_TOKEN" in response.json()["detail"]

    def test_save_calculation_branch_missing_returns_400(self, client):
        """Если работа над задачей не начата (ветка отсутствует), возвращается 400 Bad Request."""
        with patch("app.api.routes.calculations.gitlab_client.find_branch_by_issue_iid", return_value=None):
            response = client.post("/api/v1/calculations/save", json=VALID_SAVE_PAYLOAD)

        assert response.status_code == 400
        assert "не найдена в GitLab" in response.json()["detail"]

    def test_save_calculation_gitlab_api_failure(self, client):
        """Сбой GitLab API при коммите возвращает 502 Bad Gateway."""
        api_error = gitlab.exceptions.GitlabError("502 Upstream Failure")

        with patch("app.api.routes.calculations.gitlab_client.find_branch_by_issue_iid", return_value="issue/10-task"), \
             patch("app.api.routes.calculations.gitlab_client.create_commit_multiple", side_effect=api_error):
            
            response = client.post("/api/v1/calculations/save", json=VALID_SAVE_PAYLOAD)

        assert response.status_code == 502
        assert "Ошибка GitLab API" in response.json()["detail"]


# ============================================================================
# 2. ЗАЩИТА ЭНДПОИНТА ЧТЕНИЯ РАСЧЁТА: GET /api/v1/calculations/latest
# ============================================================================
class TestCalculationsLatestSecurity:
    def test_latest_calculation_success(self, client):
        """Успешное чтение сохранённого расчёта из ветки."""
        with patch("app.api.routes.calculations.gitlab_client.find_branch_by_issue_iid", return_value="issue/10-task"), \
             patch("app.api.routes.calculations.gitlab_client.get_file_content_decoded", side_effect=['{"P_fresh": 130}', '{"total": 0.45}']):
            
            response = client.get("/api/v1/calculations/latest?task_iid=10&app_type=valves&project_id=1")

        assert response.status_code == 200
        data = response.json()
        assert data["found"] is True
        assert data["input_data"] == {"P_fresh": 130}
        assert data["output_data"] == {"total": 0.45}

    def test_latest_calculation_unauthorized_token_error(self, client):
        """Ошибка авторизации не крашит сервис, а возвращает безопасный статус found=False с ошибкой."""
        auth_error = gitlab.exceptions.GitlabAuthenticationError("401 Unauthorized")

        with patch("app.api.routes.calculations.gitlab_client.find_branch_by_issue_iid", side_effect=auth_error):
            response = client.get("/api/v1/calculations/latest?task_iid=10&app_type=valves&project_id=1")

        assert response.status_code == 200
        data = response.json()
        assert data["found"] is False
        assert "Ошибка авторизации в GitLab" in data["error"]

    def test_latest_calculation_unconfigured_gitlab(self, client):
        """Отсутствие токена возвращает статус конфигурационной ошибки."""
        config_error = GitLabConfigurationError("GitLab не настроен")

        with patch("app.api.routes.calculations.gitlab_client.find_branch_by_issue_iid", side_effect=config_error):
            response = client.get("/api/v1/calculations/latest?task_iid=10&app_type=valves&project_id=1")

        assert response.status_code == 200
        data = response.json()
        assert data["found"] is False
        assert data["error_type"] == "configuration"