"""
Интеграционные тесты матрицы авторизации, RBAC и изоляции данных (Projects & Tasks)
"""

from unittest.mock import MagicMock, patch

import gitlab.exceptions
import pytest
from fastapi.testclient import TestClient

from app.core.gitlab_adapter import GitLabAdapter
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)

class TestUnauthorizedAccessMatrix:
    """Проверка, что все защищенные эндпоинты возвращают 401 при невалидном токене."""

    auth_error = gitlab.exceptions.GitlabAuthenticationError("401 Unauthorized")

    def test_list_projects_unauthorized(self, client):
        with patch("app.api.routes.projects.gitlab_client.get_user_projects", side_effect=self.auth_error):
            response = client.get("/api/v1/projects")
        assert response.status_code == 401
        assert response.json()["detail"] == "Ошибка авторизации в GitLab"

    def test_list_tasks_unauthorized(self, client):
        with patch("app.api.routes.tasks.gitlab_client.get_all_assigned_issues", side_effect=self.auth_error):
            response = client.get("/api/v1/tasks")
        assert response.status_code == 401
        assert response.json()["detail"] == "Ошибка авторизации в GitLab"

    def test_get_single_task_unauthorized(self, client):
        with patch("app.api.routes.tasks.gitlab_client.get_issue", side_effect=self.auth_error):
            response = client.get("/api/v1/tasks/10?project_id=1")
        assert response.status_code == 401
        assert response.json()["detail"] == "Ошибка авторизации в GitLab"

    def test_create_task_unauthorized(self, client):
        payload = {"title": "Новая задача", "description": "Описание", "project_id": 1, "labels": []}
        with patch("app.api.routes.tasks.gitlab_client.create_issue", side_effect=self.auth_error):
            response = client.post("/api/v1/tasks", json=payload)
        assert response.status_code == 401
        assert response.json()["detail"] == "Ошибка авторизации в GitLab"

    def test_create_branch_unauthorized(self, client):
        payload = {"project_id": 1}
        with patch("app.api.routes.tasks.gitlab_client.get_issue", side_effect=self.auth_error):
            response = client.post("/api/v1/tasks/10/branch", json=payload)
        assert response.status_code == 401
        assert response.json()["detail"] == "Ошибка авторизации в GitLab"

    def test_submit_task_unauthorized(self, client):
        with patch("app.api.routes.tasks.gitlab_client.get_issue", side_effect=self.auth_error):
            response = client.post("/api/v1/tasks/10/submit?project_id=1")
        assert response.status_code == 401
        assert response.json()["detail"] == "Ошибка авторизации в GitLab"

class TestDataIsolation:
    """Тесты проверки изоляции данных: пользователь работает только со своими задачами."""

    def test_get_tasks_filters_strictly_by_current_user_id(self):
        """Метод адаптера get_all_assigned_issues обязан запрашивать задачи строго с assignee_id=user.id."""
        adapter = GitLabAdapter(url="https://gitlab.example.com", token="test-token")
        mock_gl = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 42
        mock_gl.user = mock_user

        mock_issues_manager = MagicMock()
        mock_issues_manager.list.return_value = []
        mock_gl.issues = mock_issues_manager
        adapter._gl = mock_gl

        adapter.get_all_assigned_issues(state="opened")

        mock_issues_manager.list.assert_called_once_with(
            assignee_id=42,
            state="opened",
            scope="all",
            get_all=True,
        )

    def test_create_task_automatically_assigns_to_author(self):
        """Создание задачи обязано автоматически назначать исполнителя на текущего пользователя."""
        adapter = GitLabAdapter(url="https://gitlab.example.com", token="test-token", project_id=1)
        mock_gl = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 42
        mock_gl.user = mock_user

        mock_project = MagicMock()
        mock_project.id = 1
        mock_issue = MagicMock()
        mock_issue.iid = 101
        mock_project.issues.create.return_value = mock_issue

        mock_gl.projects.get.return_value = mock_project
        adapter._gl = mock_gl

        adapter.create_issue(title="Задача инженера", description="Детали", project_id=1)

        mock_project.issues.create.assert_called_once_with(
            {
                "title": "Задача инженера",
                "description": "Детали",
                "labels": [],
                "assignee_ids": [42],
            }
        )

class TestRBACAccessLevels:
    """Тестирование проверки прав и уровней доступа (Developer=30 vs Guest/Reporter)."""

    def test_projects_query_enforces_developer_min_access_level(self):
        """Запрос списка проектов обязан передавать min_access_level=30 (уровень Developer)."""
        adapter = GitLabAdapter(url="https://gitlab.example.com", token="test-token")
        mock_gl = MagicMock()
        mock_gl.projects.list.return_value = []
        adapter._gl = mock_gl

        adapter.get_user_projects(search="test")

        call_kwargs = mock_gl.projects.list.call_args[1]
        assert call_kwargs["membership"] is True
        assert call_kwargs["min_access_level"] == 30

    def test_insufficient_permissions_on_create_branch_raises_error(self, client):
        """Попытка создания ветки пользователем без прав записи мапится в ошибку шлюза."""
        forbidden_error = gitlab.exceptions.GitlabError("403 Forbidden - Insufficient branch creation rights")

        with patch("app.api.routes.tasks.gitlab_client.get_issue", return_value={"title": "Задача", "iid": 1}), \
             patch("app.api.routes.tasks.gitlab_client.create_branch", side_effect=forbidden_error):
            response = client.post("/api/v1/tasks/1/branch", json={"project_id": 1})

        assert response.status_code == 502
        assert "403 Forbidden" in response.json()["detail"]

class TestCrossProjectAccessProtection:
    """Проверка защиты от чтения/модификации недоступных или чужих проектов."""

    def test_get_task_from_inaccessible_project_returns_404(self, client):
        """Запрос задачи из чужого/несуществующего проекта возвращает 404 (сокрытие существования)."""
        not_found_error = gitlab.exceptions.GitlabGetError("404 Project Not Found")

        with patch("app.api.routes.tasks.gitlab_client.get_issue", side_effect=not_found_error):
            response = client.get("/api/v1/tasks/999?project_id=888")

        assert response.status_code == 404
        assert "не найдена в GitLab" in response.json()["detail"]

    def test_create_task_in_inaccessible_project_returns_404(self, client):
        """Попытка создать задачу в проекте, к которому нет доступа, возвращает 404."""
        not_found_error = gitlab.exceptions.GitlabGetError("404 Project Not Found")

        with patch("app.api.routes.tasks.gitlab_client.create_issue", side_effect=not_found_error):
            response = client.post(
                "/api/v1/tasks",
                json={"title": "Задача в чужом проекте", "project_id": 99999},
            )

        assert response.status_code == 404
        assert "Проект не найден в GitLab" in response.json()["detail"]

    def test_submit_task_in_inaccessible_project_returns_404(self, client):
        """Попытка создания MR в чужом/несуществующем проекте возвращает 404."""
        not_found_error = gitlab.exceptions.GitlabGetError("404 Project Not Found")

        with patch("app.api.routes.tasks.gitlab_client.get_issue", side_effect=not_found_error):
            response = client.post("/api/v1/tasks/10/submit?project_id=888")

        assert response.status_code == 404
        assert "не найдены в GitLab" in response.json()["detail"]