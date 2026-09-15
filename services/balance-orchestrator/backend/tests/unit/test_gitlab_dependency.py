from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.core import gitlab_dependency
from app.core.security import CurrentUser


class _AsyncClientContext:
    def __init__(self, response):
        self.client = MagicMock()
        self.client.post = AsyncMock(return_value=response)

    async def __aenter__(self):
        return self.client

    async def __aexit__(self, *_args):
        return None


@pytest.mark.asyncio
async def test_get_gitlab_client_uses_current_users_oauth_token(monkeypatch) -> None:
    monkeypatch.setenv("GITLAB_AUTH_MODE", "oauth")
    monkeypatch.setenv("AUTH_SERVICE_CLIENT_SECRET", "service-secret")
    response = MagicMock(status_code=200)
    response.json.return_value = {
        "access_token": "user-oauth-token",
        "token_type": "Bearer",
        "expires_at": 1_800_000_000,
        "gitlab_user_id": 17,
        "gitlab_username": "engineer",
    }
    context = _AsyncClientContext(response)
    monkeypatch.setattr(
        gitlab_dependency.httpx,
        "AsyncClient",
        lambda **_kwargs: context,
    )

    client = await gitlab_dependency.get_gitlab_client(
        SimpleNamespace(credentials="balance-token"),
        CurrentUser(username="engineer", gitlab_user_id=17, gitlab_username="engineer"),
    )

    assert client.token == "user-oauth-token"
    assert client.auth_type == "oauth"
    context.client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_gitlab_client_rejects_mismatched_identity(monkeypatch) -> None:
    monkeypatch.setenv("GITLAB_AUTH_MODE", "oauth")
    monkeypatch.setenv("AUTH_SERVICE_CLIENT_SECRET", "service-secret")
    response = MagicMock(status_code=200)
    response.json.return_value = {
        "access_token": "user-oauth-token",
        "token_type": "Bearer",
        "expires_at": 1_800_000_000,
        "gitlab_user_id": 18,
        "gitlab_username": "another-user",
    }
    monkeypatch.setattr(
        gitlab_dependency.httpx,
        "AsyncClient",
        lambda **_kwargs: _AsyncClientContext(response),
    )

    with pytest.raises(HTTPException) as exc_info:
        await gitlab_dependency.get_gitlab_client(
            SimpleNamespace(credentials="balance-token"),
            CurrentUser(username="engineer", gitlab_user_id=17, gitlab_username="engineer"),
        )

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_get_gitlab_client_rejects_mismatched_gitlab_user_id(monkeypatch) -> None:
    monkeypatch.setenv("GITLAB_AUTH_MODE", "oauth")
    monkeypatch.setenv("AUTH_SERVICE_CLIENT_SECRET", "service-secret")
    response = MagicMock(status_code=200)
    response.json.return_value = {
        "access_token": "user-oauth-token",
        "token_type": "Bearer",
        "expires_at": 1_800_000_000,
        "gitlab_user_id": 18,
        "gitlab_username": "engineer",
    }
    monkeypatch.setattr(
        gitlab_dependency.httpx,
        "AsyncClient",
        lambda **_kwargs: _AsyncClientContext(response),
    )

    with pytest.raises(HTTPException) as exc_info:
        await gitlab_dependency.get_gitlab_client(
            SimpleNamespace(credentials="balance-token"),
            CurrentUser(username="engineer", gitlab_user_id=17, gitlab_username="engineer"),
        )

    assert exc_info.value.status_code == 503
