from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.api.routes.health import gitlab_health_check, health_check
from app.core.gitlab_adapter import GitLabConfigurationError


@pytest.mark.asyncio
@patch("app.api.routes.health.gitlab_client")
async def test_health_does_not_call_gitlab(mock_gitlab) -> None:
    mock_gitlab.connection_summary.return_value = {"configured": False}

    result = await health_check()

    assert result["status"] == "ok"
    assert result["gitlab"] == {"configured": False}
    mock_gitlab.check_connection.assert_not_called()


@pytest.mark.asyncio
@patch("app.api.routes.health.gitlab_client")
async def test_gitlab_health_reports_configuration_error(mock_gitlab) -> None:
    mock_gitlab.check_connection.side_effect = GitLabConfigurationError("missing token")
    mock_gitlab.connection_summary.return_value = {
        "configured": False,
        "url": "http://git.utz.local",
    }

    with pytest.raises(HTTPException) as exc_info:
        await gitlab_health_check()

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["error_type"] == "configuration"
    assert "token" not in exc_info.value.detail["gitlab"]
