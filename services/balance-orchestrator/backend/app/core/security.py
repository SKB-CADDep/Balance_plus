from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import httpx
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, ValidationError


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    groups: list[str] = Field(default_factory=list)


class TokenValidationResponse(BaseModel):
    valid: bool
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    groups: list[str] = Field(default_factory=list)
    message: str | None = None


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _auth_service_url() -> str:
    return os.getenv("AUTH_SERVICE_URL", "http://authentication-service:8000").rstrip("/")


def _auth_service_timeout() -> float:
    try:
        return float(os.getenv("AUTH_SERVICE_TIMEOUT", "5"))
    except ValueError:
        return 5.0


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    try:
        async with httpx.AsyncClient(timeout=_auth_service_timeout()) as client:
            response = await client.post(
                f"{_auth_service_url()}/auth/validate",
                json={"token": credentials.credentials},
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable",
        ) from exc

    if response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable",
        )
    if response.status_code != status.HTTP_200_OK:
        raise _unauthorized("Invalid access token")

    try:
        validation = TokenValidationResponse.model_validate(response.json())
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service returned an invalid response",
        ) from exc

    if not validation.valid or not validation.username:
        raise _unauthorized("Invalid or expired access token")

    return CurrentUser(
        username=validation.username,
        email=validation.email,
        full_name=validation.full_name,
        groups=validation.groups,
    )
