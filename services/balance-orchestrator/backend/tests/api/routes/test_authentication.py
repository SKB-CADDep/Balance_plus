import httpx
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from httpx import ASGITransport, AsyncClient

from app.core import security
from app.main import app


class FakeAsyncClient:
    def __init__(self, response=None, error=None, **_kwargs):
        self.response = response
        self.error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def post(self, *_args, **_kwargs):
        if self.error:
            raise self.error
        return self.response


@pytest.mark.asyncio
async def test_api_v1_rejects_anonymous_request() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/config/bureaus")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_current_user_is_loaded_from_auth_service(monkeypatch) -> None:
    response = httpx.Response(
        200,
        json={
            "valid": True,
            "username": "engineer",
            "email": "engineer@utz.local",
            "full_name": "Test Engineer",
            "groups": ["BalanceUsers"],
        },
        request=httpx.Request("POST", "http://authentication-service:8000/auth/validate"),
    )
    monkeypatch.setattr(
        security.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient(response=response, **kwargs),
    )

    user = await security.get_current_user(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    )

    assert user.username == "engineer"
    assert user.full_name == "Test Engineer"


@pytest.mark.asyncio
async def test_invalid_token_returns_401(monkeypatch) -> None:
    response = httpx.Response(
        200,
        json={"valid": False, "message": "Invalid or expired token"},
        request=httpx.Request("POST", "http://authentication-service:8000/auth/validate"),
    )
    monkeypatch.setattr(
        security.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient(response=response, **kwargs),
    )

    with pytest.raises(HTTPException) as exc_info:
        await security.get_current_user(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid")
        )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_service_outage_returns_503(monkeypatch) -> None:
    request = httpx.Request("POST", "http://authentication-service:8000/auth/validate")
    monkeypatch.setattr(
        security.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient(
            error=httpx.ConnectError("unavailable", request=request),
            **kwargs,
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await security.get_current_user(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
        )

    assert exc_info.value.status_code == 503
