"""
Unit-тесты жизненного цикла токена: ротация, отзыв, безопасность и инвалидация кэша
"""

import time
from unittest.mock import MagicMock, patch

import gitlab.exceptions
import pytest

from app.core.gitlab_adapter import GitLabAdapter, GitLabConfigurationError


class TestTokenSecurityAndLeakage:
    """Проверка предотвращения утечки токенов в логах и диагностических методах."""

    def test_connection_summary_never_exposes_token(self):
        """Диагностика подключения connection_summary() не содержит токен авторизации."""
        secret_token = "glpat-VERY-SECRET-TOKEN-12345"
        adapter = GitLabAdapter(
            url="https://gitlab.example.com",
            token=secret_token,
            project_id=10,
        )

        summary = adapter.connection_summary()

        assert "token" not in summary
        assert "private_token" not in summary
        assert secret_token not in str(summary)
        assert summary["configured"] is True
        assert summary["url"] == "https://gitlab.example.com"
        assert summary["project_id"] == 10


class TestTokenRotationAndReconfiguration:
    """Тестирование смены (ротации) токенов и реакции на их отзыв."""

    def test_token_rotation_reinitializes_gitlab_client(self):
        """При ротации токена и сбросе _gl новый клиент создается со свежим токеном."""
        adapter = GitLabAdapter(url="https://gitlab.example.com", token="old-token-111")

        with patch("gitlab.Gitlab") as mock_gitlab_cls:
            _ = adapter.gl
            mock_gitlab_cls.assert_called_once_with(
                "https://gitlab.example.com",
                private_token="old-token-111",
                ssl_verify=False,
                timeout=10.0,
                retry_transient_errors=True,
            )

            adapter.token = "new-rotated-token-222"
            adapter._gl = None

            _ = adapter.gl
            assert mock_gitlab_cls.call_count == 2
            mock_gitlab_cls.assert_called_with(
                "https://gitlab.example.com",
                private_token="new-rotated-token-222",
                ssl_verify=False,
                timeout=10.0,
                retry_transient_errors=True,
            )

    def test_revoked_token_raises_authentication_error_on_check_connection(self):
        """Отзыв токена приводит к выбросу GitlabAuthenticationError при проверке соединения."""
        adapter = GitLabAdapter(url="https://gitlab.example.com", token="revoked-token")

        mock_gl = MagicMock()
        mock_gl.auth.side_effect = gitlab.exceptions.GitlabAuthenticationError("401 Token has been revoked")
        adapter._gl = mock_gl

        with pytest.raises(gitlab.exceptions.GitlabAuthenticationError) as exc_info:
            adapter.check_connection()

        assert "revoked" in str(exc_info.value).lower()

    def test_empty_token_marks_adapter_unconfigured_and_blocks_access(self):
        """При очистке токена доступ к клиенту блокируется с понятным исключением."""
        adapter = GitLabAdapter(url="https://gitlab.example.com", token="")

        assert adapter.configured is False
        with pytest.raises(GitLabConfigurationError) as exc_info:
            _ = adapter.gl

        assert "GITLAB_PRIVATE_TOKEN" in str(exc_info.value)


class TestProjectCacheTTLAndExpiration:
    """Тестирование инвалидации кэша проектов по TTL (защита от устаревших прав)."""

    def test_cache_hits_within_ttl(self):
        """В пределах TTL (300 сек) метод возвращает проект из кэша без повторных сетевых вызовов."""
        adapter = GitLabAdapter(url="https://gitlab.example.com", token="valid-token")

        mock_gl = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 100
        mock_gl.projects.get.return_value = mock_project
        adapter._gl = mock_gl

        p1 = adapter.get_project_by_id(100)
        assert p1 == mock_project
        assert mock_gl.projects.get.call_count == 1

        with patch("time.time", return_value=time.time() + 60):
            p2 = adapter.get_project_by_id(100)
            assert p2 == mock_project
            assert mock_gl.projects.get.call_count == 1

    def test_cache_invalidates_after_ttl_expires(self):
        """После истечения TTL (>= 300 сек) кэш инвалидируется и выполняется свежий запрос."""
        adapter = GitLabAdapter(url="https://gitlab.example.com", token="valid-token")

        mock_gl = MagicMock()
        mock_project_v1 = MagicMock()
        mock_project_v2 = MagicMock()
        mock_gl.projects.get.side_effect = [mock_project_v1, mock_project_v2]
        adapter._gl = mock_gl

        p1 = adapter.get_project_by_id(100)
        assert p1 == mock_project_v1
        assert mock_gl.projects.get.call_count == 1

        with patch("time.time", return_value=time.time() + 301):
            p2 = adapter.get_project_by_id(100)
            assert p2 == mock_project_v2
            assert mock_gl.projects.get.call_count == 2