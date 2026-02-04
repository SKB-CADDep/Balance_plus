from unittest.mock import MagicMock, patch

import gitlab.exceptions
import pytest
from fastapi import HTTPException

from app.api.routes.projects import list_projects


class TestListProjects:
    """Tests for list_projects endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.routes.projects.gitlab_client")
    async def test_returns_projects_list(self, mock_gitlab: MagicMock):
        """Should return list of projects."""
        mock_projects = [
            {"id": 1, "name": "Project A", "path_with_namespace": "group/project-a"},
            {"id": 2, "name": "Project B", "path_with_namespace": "group/project-b"},
        ]
        mock_gitlab.get_user_projects.return_value = mock_projects

        result = await list_projects(search="")

        assert result == mock_projects
        mock_gitlab.get_user_projects.assert_called_once_with("")

    @pytest.mark.asyncio
    @patch("app.api.routes.projects.gitlab_client")
    async def test_filters_projects_by_search(self, mock_gitlab: MagicMock):
        """Should filter projects by search query."""
        mock_projects = [
            {"id": 1, "name": "Project Alpha", "path_with_namespace": "group/project-alpha"},
        ]
        mock_gitlab.get_user_projects.return_value = mock_projects

        result = await list_projects(search="alpha")

        assert result == mock_projects
        mock_gitlab.get_user_projects.assert_called_once_with("alpha")

    @pytest.mark.asyncio
    @patch("app.api.routes.projects.gitlab_client")
    async def test_returns_empty_list(self, mock_gitlab: MagicMock):
        """Should return empty list when no projects found."""
        mock_gitlab.get_user_projects.return_value = []

        result = await list_projects(search="nonexistent")

        assert result == []
        mock_gitlab.get_user_projects.assert_called_once_with("nonexistent")

    @pytest.mark.asyncio
    @patch("app.api.routes.projects.gitlab_client")
    async def test_raises_401_on_authentication_error(self, mock_gitlab: MagicMock):
        """Should raise HTTPException 401 on GitLab authentication error."""
        mock_gitlab.get_user_projects.side_effect = gitlab.exceptions.GitlabAuthenticationError("Auth failed")

        with pytest.raises(HTTPException) as exc_info:
            await list_projects(search="")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Ошибка авторизации в GitLab"

    @pytest.mark.asyncio
    @patch("app.api.routes.projects.gitlab_client")
    async def test_raises_502_on_gitlab_error(self, mock_gitlab: MagicMock):
        """Should raise HTTPException 502 on GitLab API error."""
        mock_gitlab.get_user_projects.side_effect = gitlab.exceptions.GitlabError("API error")

        with pytest.raises(HTTPException) as exc_info:
            await list_projects(search="")

        assert exc_info.value.status_code == 502
        assert exc_info.value.detail == "Ошибка GitLab API: API error"

    @pytest.mark.asyncio
    @patch("app.api.routes.projects.gitlab_client")
    async def test_raises_500_on_generic_error(self, mock_gitlab: MagicMock):
        """Should raise HTTPException 500 on generic error."""
        mock_gitlab.get_user_projects.side_effect = Exception("Unexpected error")

        with pytest.raises(HTTPException) as exc_info:
            await list_projects(search="")

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Ошибка получения списка проектов: Unexpected error"

