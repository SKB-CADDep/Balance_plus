"""
Интеграционные API-тесты профиля текущего пользователя (/api/v1/user/me)
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


def test_get_current_user_success(client):
    """Успешное получение информации о текущем пользователе (200 OK)."""
    mock_user = MagicMock()
    mock_user.name = "Константинопольский К."
    mock_user.username = "k.konstantinopolsky"
    mock_user.avatar_url = "https://gitlab.example.com/uploads/avatar.png"

    with patch("app.api.routes.user.gitlab_client.get_current_user", return_value=mock_user):
        response = client.get("/api/v1/user/me")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Константинопольский К."
    assert data["username"] == "k.konstantinopolsky"
    assert data["avatar_url"] == "https://gitlab.example.com/uploads/avatar.png"


def test_get_current_user_unauthorized(client):
    """Ошибка аутентификации токена в GitLab (401 Unauthorized)."""
    with patch(
        "app.api.routes.user.gitlab_client.get_current_user",
        side_effect=gitlab.exceptions.GitlabAuthenticationError("401 Unauthorized"),
    ):
        response = client.get("/api/v1/user/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Ошибка авторизации в GitLab"


def test_get_current_user_configuration_error(client):
    """GitLab не настроен в .env: токен или URL отсутствуют (503 Service Unavailable)."""
    error_message = "Не заданы обязательные настройки GitLab: GITLAB_PRIVATE_TOKEN"
    with patch(
        "app.api.routes.user.gitlab_client.get_current_user",
        side_effect=GitLabConfigurationError(error_message),
    ):
        response = client.get("/api/v1/user/me")

    assert response.status_code == 503
    assert response.json()["detail"] == error_message


def test_get_current_user_gitlab_api_error(client):
    """Сбой GitLab API при обращении (502 Bad Gateway)."""
    with patch(
        "app.api.routes.user.gitlab_client.get_current_user",
        side_effect=gitlab.exceptions.GitlabError("Connection refused by upstream"),
    ):
        response = client.get("/api/v1/user/me")

    assert response.status_code == 502
    assert "Ошибка GitLab API" in response.json()["detail"]


def test_get_current_user_unexpected_error(client):
    """Непредвиденное исключение при обработке запроса (500 Internal Server Error)."""
    with patch(
        "app.api.routes.user.gitlab_client.get_current_user",
        side_effect=RuntimeError("Unexpected memory failure"),
    ):
        response = client.get("/api/v1/user/me")

    assert response.status_code == 500
    assert response.json()["detail"] == "Ошибка получения пользователя: RuntimeError"