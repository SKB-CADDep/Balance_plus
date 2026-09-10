from unittest.mock import MagicMock, patch

import pytest

from app.core.gitlab_adapter import GitLabAdapter, GitLabConfigurationError


def test_missing_configuration_is_reported_lazily() -> None:
    adapter = GitLabAdapter(url="", token="")

    assert adapter.configured is False
    assert adapter.connection_summary()["configured"] is False

    with pytest.raises(GitLabConfigurationError, match="GITLAB_URL"):
        adapter.check_connection()


@patch("app.core.gitlab_adapter.gitlab.Gitlab")
def test_client_uses_internal_gitlab_options(mock_gitlab: MagicMock) -> None:
    adapter = GitLabAdapter(
        url="http://git.utz.local/",
        token="test-token",
        project_id=41,
        ssl_verify=False,
        timeout=7,
    )

    client = adapter.gl

    assert client is mock_gitlab.return_value
    mock_gitlab.assert_called_once_with(
        "http://git.utz.local",
        private_token="test-token",
        ssl_verify=False,
        timeout=7,
        retry_transient_errors=True,
    )


def test_connection_check_returns_sanitized_diagnostics() -> None:
    adapter = GitLabAdapter(url="http://git.utz.local", token="test-token")
    client = MagicMock()
    client.user.username = "engineer"
    adapter._gl = client

    result = adapter.check_connection()

    client.auth.assert_called_once_with()
    assert result["status"] == "ok"
    assert result["username"] == "engineer"
    assert "token" not in result


def test_project_filter_is_used_for_assigned_issues() -> None:
    adapter = GitLabAdapter(url="http://git.utz.local", token="test-token")
    client = MagicMock()
    client.user.id = 17
    adapter._gl = client

    project = MagicMock()
    project.id = 41
    project.name = "Factory project"
    issue = MagicMock()
    issue.iid = 5
    issue.project_id = 41
    issue.title = "Calculation"
    issue.description = None
    issue.state = "opened"
    issue.labels = []
    issue.assignee = {"username": "engineer"}
    issue.created_at = "2026-08-19T00:00:00Z"
    issue.due_date = None
    issue.web_url = "http://git.utz.local/project/-/issues/5"
    project.issues.list.return_value = [issue]
    adapter.get_project_by_id = MagicMock(return_value=project)

    result = adapter.get_all_assigned_issues(state="opened", project_id=41)

    project.issues.list.assert_called_once_with(
        assignee_id=17,
        state="opened",
        get_all=True,
    )
    assert result[0]["project_id"] == 41
    assert result[0]["project_name"] == "Factory project"
