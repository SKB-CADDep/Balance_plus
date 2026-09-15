import base64
import hashlib

from fastapi.testclient import TestClient

import app as simulator

client = TestClient(simulator.app)


def _authorize_params(challenge: str) -> dict[str, str]:
    return {
        "client_id": simulator.CLIENT_ID,
        "redirect_uri": "http://localhost:3030/auth/gitlab/callback",
        "response_type": "code",
        "state": "test-state",
        "scope": "api",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }


def test_oauth_pkce_and_user_api_are_delegated_to_ldap_user() -> None:
    simulator.authorization_codes.clear()
    simulator.access_tokens.clear()
    simulator.refresh_tokens.clear()
    simulator.audit_log.clear()
    verifier = "local-verifier-with-more-than-forty-three-characters-123456789"
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    params = _authorize_params(challenge)

    denied = client.post(
        "/oauth/authorize",
        params=params,
        data={"username": "missing", "password": "wrong"},
        follow_redirects=False,
    )
    assert denied.status_code == 401

    authorized = client.post(
        "/oauth/authorize",
        params=params,
        data={
            "username": simulator.LDAP_USERNAME,
            "password": simulator.LDAP_PASSWORD,
        },
        follow_redirects=False,
    )
    assert authorized.status_code == 302
    code = next(iter(simulator.authorization_codes))

    token_response = client.post(
        "/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": simulator.CLIENT_ID,
            "client_secret": simulator.CLIENT_SECRET,
            "code": code,
            "redirect_uri": params["redirect_uri"],
            "code_verifier": verifier,
        },
    )
    assert token_response.status_code == 200
    access_token = token_response.json()["access_token"]

    user_response = client.get(
        "/api/v4/user",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert user_response.status_code == 200
    assert user_response.json()["username"] == simulator.LDAP_USERNAME
    assert simulator.audit_log[-1]["username"] == simulator.LDAP_USERNAME
