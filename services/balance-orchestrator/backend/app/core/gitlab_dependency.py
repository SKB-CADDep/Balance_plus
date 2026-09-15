from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, ValidationError

from app.core.gitlab_adapter import (
    GitLabAdapter,
    get_legacy_gitlab_client,
    reset_request_gitlab_client,
    set_request_gitlab_client,
)
from app.core.security import CurrentUser, bearer_scheme, get_current_user


class GitLabTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: int
    gitlab_user_id: int
    gitlab_username: str


def _auth_service_url() -> str:
    return os.getenv("AUTH_SERVICE_URL", "http://authentication-service:8000").rstrip("/")


def _auth_service_timeout() -> float:
    try:
        return float(os.getenv("AUTH_SERVICE_TIMEOUT", "5"))
    except ValueError:
        return 5.0


async def get_gitlab_client(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    current_user: CurrentUser = Depends(get_current_user),
) -> GitLabAdapter:
    if os.getenv("GITLAB_AUTH_MODE", "oauth").lower() == "legacy":
        return get_legacy_gitlab_client()
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    service_secret = os.getenv("AUTH_SERVICE_CLIENT_SECRET", "")
    if not service_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitLab user-token integration is not configured",
        )

    try:
        async with httpx.AsyncClient(timeout=_auth_service_timeout()) as client:
            response = await client.post(
                f"{_auth_service_url()}/internal/gitlab/token",
                headers={
                    "Authorization": f"Bearer {credentials.credentials}",
                    "X-Service-Secret": service_secret,
                },
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable",
        ) from exc

    if response.status_code in {401, 403}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="GitLab account is not linked or access has expired",
        )
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not obtain the current user's GitLab credentials",
        )

    try:
        token = GitLabTokenResponse.model_validate(response.json())
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service returned invalid GitLab credentials",
        ) from exc

    expected_username = current_user.gitlab_username or current_user.username
    identity_mismatch = token.gitlab_username.casefold() != expected_username.casefold()
    if current_user.gitlab_user_id is not None:
        identity_mismatch = identity_mismatch or token.gitlab_user_id != current_user.gitlab_user_id
    if identity_mismatch:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitLab identity does not match the authenticated user",
        )

    return GitLabAdapter(token=token.access_token, auth_type="oauth")


async def bind_gitlab_client(
    client: GitLabAdapter = Depends(get_gitlab_client),
) -> AsyncIterator[None]:
    context_token = set_request_gitlab_client(client)
    try:
        yield
    finally:
        reset_request_gitlab_client(context_token)
