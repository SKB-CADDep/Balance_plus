import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from schemas.task import TaskCreate, BranchInfo
from api.routes.tasks import (
    list_tasks,
    get_task,
    create_task,
    create_task_branch,
)


class TestListTasks:
    """Tests for list_tasks endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_opened_all_users_returns_issues(self, mock_gitlab: MagicMock):
        """Should return issues for opened state and all users."""
        mock_gitlab.get_issues.return_value = [{"iid": 1, "title": "Test"}]
        result = await list_tasks(state="opened", my_only=False)
        assert result == [{"iid": 1, "title": "Test"}]
        mock_gitlab.get_issues.assert_called_once_with(state="opened", assignee=None)

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_opened_my_only_returns_issues(self, mock_gitlab: MagicMock):
        """Should return issues for opened state and my_only=True."""
        mock_gitlab.get_issues.return_value = [{"iid": 2, "title": "My task"}]
        result = await list_tasks(state="opened", my_only=True)
        assert result == [{"iid": 2, "title": "My task"}]
        mock_gitlab.get_issues.assert_called_once_with(state="opened", assignee="me")

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_closed_state_returns_issues(self, mock_gitlab: MagicMock):
        """Should handle closed state correctly."""
        mock_gitlab.get_issues.return_value = []
        result = await list_tasks(state="closed", my_only=False)
        assert result == []
        mock_gitlab.get_issues.assert_called_once_with(state="closed", assignee=None)

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_all_state_returns_issues(self, mock_gitlab: MagicMock):
        """Should handle all state correctly."""
        mock_gitlab.get_issues.return_value = [{"iid": 3}]
        result = await list_tasks(state="all", my_only=False)
        assert result == [{"iid": 3}]
        mock_gitlab.get_issues.assert_called_once_with(state="all", assignee=None)

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_empty_state_passes_to_gitlab(self, mock_gitlab: MagicMock):
        """Should pass empty state to gitlab_client."""
        mock_gitlab.get_issues.return_value = []
        result = await list_tasks(state="")
        assert result == []
        mock_gitlab.get_issues.assert_called_once_with(state="", assignee=None)

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_raises_500_on_gitlab_error(self, mock_gitlab: MagicMock):
        """Should raise HTTPException 500 on gitlab_client error."""
        mock_gitlab.get_issues.side_effect = Exception("Connection failed")
        with pytest.raises(HTTPException) as exc_info:
            await list_tasks()
        assert exc_info.value.status_code == 500
        assert "Ошибка получения задач: Connection failed" == exc_info.value.detail


class TestGetTask:
    """Tests for get_task endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_valid_iid_returns_task(self, mock_gitlab: MagicMock):
        """Should return task info for valid issue_iid."""
        expected_issue = {"iid": 42, "title": "Test task"}
        mock_gitlab.get_issue.return_value = expected_issue
        result = await get_task(42)
        assert result == expected_issue
        mock_gitlab.get_issue.assert_called_once_with(42)

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_zero_iid_calls_gitlab(self, mock_gitlab: MagicMock):
        """Should handle zero issue_iid boundary case."""
        mock_gitlab.get_issue.return_value = {"iid": 0}
        result = await get_task(0)
        assert result["iid"] == 0
        mock_gitlab.get_issue.assert_called_once_with(0)

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_negative_iid_calls_gitlab(self, mock_gitlab: MagicMock):
        """Should handle negative issue_iid edge case."""
        mock_gitlab.get_issue.return_value = {"iid": -1}
        result = await get_task(-1)
        assert result["iid"] == -1
        mock_gitlab.get_issue.assert_called_once_with(-1)

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_large_iid_calls_gitlab(self, mock_gitlab: MagicMock):
        """Should handle large issue_iid boundary case."""
        large_iid = 999999999
        mock_gitlab.get_issue.return_value = {"iid": large_iid}
        result = await get_task(large_iid)
        assert result["iid"] == large_iid
        mock_gitlab.get_issue.assert_called_once_with(large_iid)

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_raises_404_on_gitlab_error(self, mock_gitlab: MagicMock):
        """Should raise HTTPException 404 on gitlab_client error."""
        mock_gitlab.get_issue.side_effect = Exception("Issue not found")
        with pytest.raises(HTTPException) as exc_info:
            await get_task(999)
        assert exc_info.value.status_code == 404
        assert "Задача не найдена: Issue not found" == exc_info.value.detail

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_non_int_iid_passes_to_gitlab(self, mock_gitlab: MagicMock):
        """Should pass non-int issue_iid to gitlab_client (Python typing)."""
        mock_gitlab.get_issue.return_value = {"iid": "str"}
        result = await get_task("123")
        mock_gitlab.get_issue.assert_called_once_with("123")


class TestCreateTask:
    """Tests for create_task endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_valid_task_creates_and_returns_full_info(self, mock_gitlab: MagicMock):
        """Should create issue and return full task info."""
        task = TaskCreate(title="New Task", description="Details", labels=["feature"])
        created_issue = {"iid": 123}
        full_issue = {"iid": 123, "title": "New Task", "state": "opened"}
        mock_gitlab.create_issue.return_value = created_issue
        mock_gitlab.get_issue.return_value = full_issue
        result = await create_task(task)
        assert result == full_issue
        mock_gitlab.create_issue.assert_called_once_with(
            title="New Task", description="Details", labels=["feature"]
        )
        mock_gitlab.get_issue.assert_called_once_with(123)

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_empty_title_passes_to_gitlab(self, mock_gitlab: MagicMock):
        """Should handle empty title edge case."""
        task = TaskCreate(title="", description=None, labels=None)
        mock_gitlab.create_issue.return_value = {"iid": 456}
        mock_gitlab.get_issue.return_value = {"iid": 456}
        result = await create_task(task)
        mock_gitlab.create_issue.assert_called_once_with(title="", description=None, labels=None)

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_raises_500_on_create_issue_error(self, mock_gitlab: MagicMock):
        """Should raise HTTPException 500 on create_issue error."""
        task = TaskCreate(title="Fail task")
        mock_gitlab.create_issue.side_effect = Exception("Validation failed")
        with pytest.raises(HTTPException) as exc_info:
            await create_task(task)
        assert exc_info.value.status_code == 500
        assert "Ошибка создания задачи: Validation failed" == exc_info.value.detail

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    async def test_raises_500_on_get_issue_error(self, mock_gitlab: MagicMock):
        """Should raise HTTPException 500 on get_issue after create."""
        task = TaskCreate(title="Test")
        mock_gitlab.create_issue.return_value = {"iid": 789}
        mock_gitlab.get_issue.side_effect = Exception("Fetch failed")
        with pytest.raises(HTTPException) as exc_info:
            await create_task(task)
        assert exc_info.value.status_code == 500
        assert "Ошибка создания задачи: Fetch failed" == exc_info.value.detail


class TestCreateTaskBranch:
    """Tests for create_task_branch endpoint."""

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    @patch("api.routes.tasks.slugify")
    async def test_successful_branch_creation(self, mock_slugify: MagicMock, mock_gitlab: MagicMock):
        """Should create branch with slugified title."""
        issue_iid = 42
        issue = {"iid": issue_iid, "title": "Тестовый расчёт"}
        safe_slug = "testovyi-raschet"
        branch_name = f"issue/{issue_iid}-{safe_slug}"
        mock_gitlab.get_issue.return_value = issue
        mock_slugify.return_value = safe_slug
        mock_gitlab.create_branch.return_value = True
        result = await create_task_branch(issue_iid)
        assert result.branch_name == branch_name
        assert result.issue_iid == issue_iid
        assert result.created is True
        mock_gitlab.get_issue.assert_called_once_with(issue_iid)
        mock_slugify.assert_called_once_with("Тестовый расчёт", max_length=40)
        mock_gitlab.create_branch.assert_called_once_with(branch_name)

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    @patch("api.routes.tasks.slugify")
    async def test_empty_slug_uses_fallback(self, mock_slugify: MagicMock, mock_gitlab: MagicMock):
        """Should use 'task' fallback when slug is empty."""
        issue_iid = 10
        issue = {"iid": issue_iid, "title": "!!!"}
        branch_name = f"issue/{issue_iid}-task"
        mock_gitlab.get_issue.return_value = issue
        mock_slugify.return_value = ""
        mock_gitlab.create_branch.return_value = True
        result = await create_task_branch(issue_iid)
        assert result.branch_name == branch_name
        mock_slugify.assert_called_once_with("!!!", max_length=40)

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    @patch("api.routes.tasks.slugify")
    async def test_zero_iid_boundary(self, mock_slugify: MagicMock, mock_gitlab: MagicMock):
        """Should handle zero issue_iid boundary case."""
        issue_iid = 0
        issue = {"iid": issue_iid, "title": "Zero task"}
        safe_slug = "zero-task"
        branch_name = f"issue/{issue_iid}-{safe_slug}"
        mock_gitlab.get_issue.return_value = issue
        mock_slugify.return_value = safe_slug
        mock_gitlab.create_branch.return_value = False
        result = await create_task_branch(issue_iid)
        assert result.branch_name == branch_name
        assert result.created is False

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    @patch("api.routes.tasks.slugify")
    async def test_raises_500_on_get_issue_error(self, mock_slugify: MagicMock, mock_gitlab: MagicMock):
        """Should raise HTTPException 500 on get_issue error."""
        mock_gitlab.get_issue.side_effect = Exception("Issue not found")
        with pytest.raises(HTTPException) as exc_info:
            await create_task_branch(100)
        assert exc_info.value.status_code == 500
        assert "Ошибка создания ветки: Issue not found" == exc_info.value.detail

    @pytest.mark.asyncio
    @patch("api.routes.tasks.gitlab_client")
    @patch("api.routes.tasks.slugify")
    async def test_raises_500_on_create_branch_error(self, mock_slugify: MagicMock, mock_gitlab: MagicMock):
        """Should raise HTTPException 500 on create_branch error."""
        issue = {"iid": 200, "title": "Error task"}
        mock_gitlab.get_issue.return_value = issue
        mock_slugify.return_value = "error"
        mock_gitlab.create_branch.side_effect = Exception("Branch exists")
        with pytest.raises(HTTPException) as exc_info:
            await create_task_branch(200)
        assert exc_info.value.status_code == 500
        assert "Ошибка создания ветки: Branch exists" == exc_info.value.detail