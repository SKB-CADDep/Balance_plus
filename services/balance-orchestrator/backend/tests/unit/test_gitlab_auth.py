"""
Unit-тесты аутентификации, валидации токенов и конфигурации GitLabAdapter
"""

from unittest.mock import MagicMock, patch

import gitlab.exceptions
import pytest

from app.core.gitlab_adapter import GitLabAdapter, GitLabConfigurationError


class TestGitLabAdapterAuth:
    def test_configured_property_true(self):
        """Проверка статуса configured = True при наличии URL и токена."""
        adapter = GitLabAdapter(url="https://gitlab.com", token="glpat-secret-token")
        assert adapter.configured is True

    def test_configured_property_false_when_missing_token(self):
        """Проверка статуса configured = False при отсутствии токена."""
        adapter = GitLabAdapter(url="https://gitlab.com", token="")
        assert adapter.configured is False

    def test_configured_property_false_when_missing_url(self):
        """Проверка статуса configured = False при отсутствии URL."""
        adapter = GitLabAdapter(url="", token="glpat-secret-token")
        assert adapter.configured is False

    def test_gl_raises_configuration_error_when_not_configured(self):
        """Обращение к свойству .gl без токена выбрасывает GitLabConfigurationError."""
        adapter = GitLabAdapter(url="", token="")
        with pytest.raises(GitLabConfigurationError) as exc_info:
            _ = adapter.gl

        assert "GITLAB_URL" in str(exc_info.value)
        assert "GITLAB_PRIVATE_TOKEN" in str(exc_info.value)

    def test_get_current_user_triggers_auth_if_user_none(self):
        """Метод get_current_user вызывает auth() если gl.user еще не инициализирован."""
        adapter = GitLabAdapter(url="https://gitlab.com", token="valid-token")

        mock_gl = MagicMock()
        mock_user = MagicMock()
        mock_user.username = "test_user"

        mock_gl.user = None

        def fake_auth():
            mock_gl.user = mock_user

        mock_gl.auth.side_effect = fake_auth
        adapter._gl = mock_gl

        user = adapter.get_current_user()
        assert user.username == "test_user"
        mock_gl.auth.assert_called_once()

    def test_get_current_user_does_not_reauth_if_already_present(self):
        """Метод get_current_user не вызывает повторный auth(), если пользователь уже получен."""
        adapter = GitLabAdapter(url="https://gitlab.com", token="valid-token")

        mock_gl = MagicMock()
        mock_user = MagicMock()
        mock_user.username = "cached_user"
        mock_gl.user = mock_user
        adapter._gl = mock_gl

        user = adapter.get_current_user()
        assert user.username == "cached_user"
        mock_gl.auth.assert_not_called()

    def test_check_connection_success(self):
        """Метод check_connection успешно авторизуется и возвращает статус ok."""
        adapter = GitLabAdapter(url="https://gitlab.com", token="valid-token", project_id=123)

        mock_gl = MagicMock()
        mock_user = MagicMock()
        mock_user.username = "engineer_user"
        mock_gl.user = mock_user
        adapter._gl = mock_gl

        result = adapter.check_connection(check_project=False)

        mock_gl.auth.assert_called_once()
        assert result["status"] == "ok"
        assert result["username"] == "engineer_user"
        assert result["configured"] is True

    def test_check_connection_auth_failure(self):
        """Метод check_connection пробрасывает GitlabAuthenticationError при невалидном токене."""
        adapter = GitLabAdapter(url="https://gitlab.com", token="invalid-token")

        mock_gl = MagicMock()
        mock_gl.auth.side_effect = gitlab.exceptions.GitlabAuthenticationError("401 Invalid Token")
        adapter._gl = mock_gl

        with pytest.raises(gitlab.exceptions.GitlabAuthenticationError):
            adapter.check_connection()