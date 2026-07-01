"""
Тесты эндпоинтов user (GET /user/me).
"""
from unittest.mock import MagicMock, patch

import gitlab.exceptions
import pytest
from fastapi import HTTPException

from app.api.routes.user import get_current_user


class TestGetCurrentUser:
    """Тесты эндпоинта get_current_user."""

    @pytest.mark.asyncio
    @patch("app.api.routes.user.gitlab_client")
    async def test_returns_current_user(self, mock_gitlab: MagicMock):
        """Должен вернуть текущего пользователя."""
        mock_user = MagicMock()
        mock_user.name = "Test User"
        mock_user.username = "test-user"
        mock_user.avatar_url = "https://gitlab.com/avatar/test-user.png"
        mock_gitlab.gl.user = mock_user

        result = await get_current_user()

        assert result == {
            "name": "Test User",
            "username": "test-user",
            "avatar_url": "https://gitlab.com/avatar/test-user.png",
        }
        mock_gitlab.check_connection.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.api.routes.user.gitlab_client")
    async def test_authentication_error(self, mock_gitlab: MagicMock):
        """Должен вернуть 401 при ошибке авторизации."""
        mock_gitlab.check_connection.side_effect = gitlab.exceptions.GitlabAuthenticationError(
            "Authentication error"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user()

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Ошибка авторизации в GitLab"

    @pytest.mark.asyncio
    @patch("app.api.routes.user.gitlab_client")
    async def test_gitlab_error(self, mock_gitlab: MagicMock):
        """Должен вернуть 502 при ошибке GitLab."""
        mock_gitlab.check_connection.side_effect = gitlab.exceptions.GitlabError("GitLab error")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user()

        assert exc_info.value.status_code == 502
        assert exc_info.value.detail == "Ошибка GitLab API: GitLab error"

    @pytest.mark.asyncio
    @patch("app.api.routes.user.gitlab_client")
    async def test_generic_error_returns_guest(self, mock_gitlab: MagicMock):
        """Должен вернуть гостевого пользователя при неожиданной ошибке."""
        mock_gitlab.check_connection.side_effect = Exception("Generic error")

        result = await get_current_user()

        assert result == {"name": "Гость", "username": "guest", "avatar_url": ""}
