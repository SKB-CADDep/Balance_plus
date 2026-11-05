from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
class TestOrchestratorNegative:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.transport = ASGITransport(app=app)
        self.base_url = "http://test/api/v1"

    async def test_save_missing_task_id(self):
        """QA-5: Сохранение без task_iid -> 422"""
        url = f"{self.base_url}/calculations/save"
        payload = {"project_id": 41, "app_type": "valves", "input_data": {}, "output_data": {}}
        async with AsyncClient(transport=self.transport, base_url="http://test") as ac:
            response = await ac.post(url, json=payload)
        assert response.status_code == 422

    async def test_save_invalid_project_id_type(self):
        """QA-5: project_id строкой вместо числа -> 422"""
        url = f"{self.base_url}/calculations/save"
        payload = {
            "task_iid": 1,
            "project_id": "NOT_A_NUMBER",
            "app_type": "valves",
            "input_data": {},
            "output_data": {},
        }
        async with AsyncClient(transport=self.transport, base_url="http://test") as ac:
            response = await ac.post(url, json=payload)
        assert response.status_code == 422

    @patch("app.api.routes.tasks.gitlab_client")
    async def test_get_tasks_without_project_id(self, mock_gitlab):
        """Список назначенных задач доступен без фильтра по проекту."""
        mock_gitlab.get_all_assigned_issues.return_value = []
        url = f"{self.base_url}/tasks"  # БЕЗ слэша в конце
        async with AsyncClient(transport=self.transport, base_url="http://test") as ac:
            response = await ac.get(url)
        assert response.status_code == 200
        assert response.json() == []
        mock_gitlab.get_all_assigned_issues.assert_called_once_with(state="opened")
