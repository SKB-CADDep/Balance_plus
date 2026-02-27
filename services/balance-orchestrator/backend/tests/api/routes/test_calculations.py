import json
from unittest.mock import MagicMock, patch

import gitlab.exceptions
import pytest
from fastapi import HTTPException

from app.api.routes.calculations import get_latest_calculation, save_calculation_result
from app.schemas.calculation import CalculationSaveRequest


class TestSaveCalculationResult:
    """Tests for save_calculation_result endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_successful_save(self, mock_gitlab: MagicMock):
        """Should successfully save calculation result."""
        # Setup mocks
        branch_name = "issue/42-test-task"
        mock_commit = MagicMock()
        mock_commit.id = "abc123"
        mock_commit.web_url = "https://gitlab.com/project/repo/-/commit/abc123"

        mock_gitlab.find_branch_by_issue_iid.return_value = branch_name
        mock_gitlab.create_commit_multiple.return_value = mock_commit

        # Prepare request
        request = CalculationSaveRequest(
            task_iid=42,
            project_id=123,
            app_type="valves",
            input_data={"param1": "value1"},
            output_data={"result": "success"},
            commit_message="Test commit"
        )

        # Execute
        result = await save_calculation_result(request)

        # Assertions
        assert result["status"] == "saved"
        assert result["commit_id"] == "abc123"
        assert result["path"] == "calculations/valves/current"
        assert result["web_url"] == "https://gitlab.com/project/repo/-/commit/abc123"

        # Verify calls
        mock_gitlab.find_branch_by_issue_iid.assert_called_once_with(42, 123)
        mock_gitlab.create_commit_multiple.assert_called_once()

        # Check files in commit
        call_args = mock_gitlab.create_commit_multiple.call_args
        assert call_args.kwargs["branch"] == branch_name
        assert call_args.kwargs["project_id"] == 123
        assert "Calc Result: Test commit" in call_args.kwargs["commit_message"]
        assert "calculations/valves/current/input.json" in call_args.kwargs["files"]
        assert "calculations/valves/current/result.json" in call_args.kwargs["files"]

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_returns_400_when_branch_not_found(self, mock_gitlab: MagicMock):
        """Should return 400 Bad Request when branch is not found."""
        mock_gitlab.find_branch_by_issue_iid.return_value = None

        request = CalculationSaveRequest(
            task_iid=999,
            project_id=123,
            app_type="valves",
            input_data={"param1": "value1"},
            output_data={"result": "success"}
        )

        with pytest.raises(HTTPException) as exc_info:
            await save_calculation_result(request)

        assert exc_info.value.status_code == 400
        assert "Ветка для задачи #999 не найдена" in exc_info.value.detail
        mock_gitlab.find_branch_by_issue_iid.assert_called_once_with(999, 123)
        mock_gitlab.create_commit_multiple.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_raises_401_on_authentication_error(self, mock_gitlab: MagicMock):
        """Should raise HTTPException 401 on GitLab authentication error."""
        mock_gitlab.find_branch_by_issue_iid.return_value = "issue/42-test"
        mock_gitlab.create_commit_multiple.side_effect = gitlab.exceptions.GitlabAuthenticationError("Auth failed")

        request = CalculationSaveRequest(
            task_iid=42,
            project_id=123,
            app_type="valves",
            input_data={"param1": "value1"},
            output_data={"result": "success"}
        )

        with pytest.raises(HTTPException) as exc_info:
            await save_calculation_result(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Ошибка авторизации в GitLab"

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_raises_404_on_get_error(self, mock_gitlab: MagicMock):
        """Should raise HTTPException 404 on GitLabGetError."""
        mock_gitlab.find_branch_by_issue_iid.return_value = "issue/42-test"
        mock_gitlab.create_commit_multiple.side_effect = gitlab.exceptions.GitlabGetError("Not found")

        request = CalculationSaveRequest(
            task_iid=42,
            project_id=123,
            app_type="valves",
            input_data={"param1": "value1"},
            output_data={"result": "success"}
        )

        with pytest.raises(HTTPException) as exc_info:
            await save_calculation_result(request)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Объект не найден в GitLab"

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_raises_502_on_gitlab_error(self, mock_gitlab: MagicMock):
        """Should raise HTTPException 502 on GitLab API error."""
        mock_gitlab.find_branch_by_issue_iid.return_value = "issue/42-test"
        mock_gitlab.create_commit_multiple.side_effect = gitlab.exceptions.GitlabError("API error")

        request = CalculationSaveRequest(
            task_iid=42,
            project_id=123,
            app_type="valves",
            input_data={"param1": "value1"},
            output_data={"result": "success"}
        )

        with pytest.raises(HTTPException) as exc_info:
            await save_calculation_result(request)

        assert exc_info.value.status_code == 502
        assert exc_info.value.detail == "Ошибка GitLab API: API error"

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_raises_500_on_generic_error(self, mock_gitlab: MagicMock):
        """Should raise HTTPException 500 on generic error."""
        mock_gitlab.find_branch_by_issue_iid.return_value = "issue/42-test"
        mock_gitlab.create_commit_multiple.side_effect = Exception("Unexpected error")

        request = CalculationSaveRequest(
            task_iid=42,
            project_id=123,
            app_type="valves",
            input_data={"param1": "value1"},
            output_data={"result": "success"}
        )

        with pytest.raises(HTTPException) as exc_info:
            await save_calculation_result(request)

        assert exc_info.value.status_code == 500


class TestGetLatestCalculation:
    """Tests for get_latest_calculation endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_returns_calculation_data_when_found(self, mock_gitlab: MagicMock):
        """Should return calculation data when files exist."""
        branch_name = "issue/42-test-task"
        input_data = {"param1": "value1", "param2": 100}
        output_data = {"result": "success", "value": 42.5}

        mock_gitlab.find_branch_by_issue_iid.return_value = branch_name
        mock_gitlab.get_file_content_decoded.side_effect = [
            json.dumps(input_data),
            json.dumps(output_data)
        ]

        result = await get_latest_calculation(task_iid=42, app_type="valves", project_id=123)

        assert result["found"] is True
        assert result["input_data"] == input_data
        assert result["output_data"] == output_data

        # Verify calls
        mock_gitlab.find_branch_by_issue_iid.assert_called_once_with(42, 123)
        assert mock_gitlab.get_file_content_decoded.call_count == 2
        mock_gitlab.get_file_content_decoded.assert_any_call(
            "calculations/valves/current/input.json",
            ref=branch_name,
            project_id=123
        )
        mock_gitlab.get_file_content_decoded.assert_any_call(
            "calculations/valves/current/result.json",
            ref=branch_name,
            project_id=123
        )

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_returns_found_false_when_branch_not_found(self, mock_gitlab: MagicMock):
        """Should return found=False when branch is not found."""
        mock_gitlab.find_branch_by_issue_iid.return_value = None

        result = await get_latest_calculation(task_iid=999, app_type="valves", project_id=123)

        assert result["found"] is False
        assert result["reason"] == "Branch not found"
        mock_gitlab.find_branch_by_issue_iid.assert_called_once_with(999, 123)
        mock_gitlab.get_file_content_decoded.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_returns_found_false_when_input_file_missing(self, mock_gitlab: MagicMock):
        """Should return found=False when input file is missing."""
        branch_name = "issue/42-test-task"
        mock_gitlab.find_branch_by_issue_iid.return_value = branch_name
        mock_gitlab.get_file_content_decoded.return_value = None

        result = await get_latest_calculation(task_iid=42, app_type="valves", project_id=123)

        assert result["found"] is False
        assert result["reason"] == "Files missing"

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_handles_missing_output_file(self, mock_gitlab: MagicMock):
        """Should handle missing output file gracefully."""
        branch_name = "issue/42-test-task"
        input_data = {"param1": "value1"}

        mock_gitlab.find_branch_by_issue_iid.return_value = branch_name
        mock_gitlab.get_file_content_decoded.side_effect = [
            json.dumps(input_data),
            None  # output file missing
        ]

        result = await get_latest_calculation(task_iid=42, app_type="valves", project_id=123)

        assert result["found"] is True
        assert result["input_data"] == input_data
        assert result["output_data"] is None

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_returns_found_false_on_authentication_error(self, mock_gitlab: MagicMock):
        """Should return found=False on GitLab authentication error."""
        mock_gitlab.find_branch_by_issue_iid.side_effect = gitlab.exceptions.GitlabAuthenticationError("Auth failed")

        result = await get_latest_calculation(task_iid=42, app_type="valves", project_id=123)

        assert result["found"] is False
        assert "Ошибка авторизации в GitLab" in result["error"]

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_returns_found_false_on_get_error(self, mock_gitlab: MagicMock):
        """Should return found=False on GitLabGetError."""
        mock_gitlab.find_branch_by_issue_iid.side_effect = gitlab.exceptions.GitlabGetError("Not found")

        result = await get_latest_calculation(task_iid=42, app_type="valves", project_id=123)

        assert result["found"] is False
        assert result["reason"] == "Branch or files not found"

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_returns_found_false_on_gitlab_error(self, mock_gitlab: MagicMock):
        """Should return found=False on GitLab API error."""
        mock_gitlab.find_branch_by_issue_iid.side_effect = gitlab.exceptions.GitlabError("API error")

        result = await get_latest_calculation(task_iid=42, app_type="valves", project_id=123)

        assert result["found"] is False
        assert "Ошибка GitLab API" in result["error"]

    @pytest.mark.asyncio
    @patch("app.api.routes.calculations.gitlab_client")
    async def test_returns_found_false_on_generic_error(self, mock_gitlab: MagicMock):
        """Should return found=False on generic error."""
        mock_gitlab.find_branch_by_issue_iid.side_effect = Exception("Unexpected error")

        result = await get_latest_calculation(task_iid=42, app_type="valves", project_id=123)

        assert result["found"] is False
        assert "error" in result
        assert "Unexpected error" in result["error"]

