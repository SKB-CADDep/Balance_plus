from __future__ import annotations

import json
import sys
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

FRONTEND_URL = "http://localhost:3030"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


opener = build_opener(NoRedirect)


def request(url: str, *, method: str = "GET", data=None, headers=None):
    payload = data
    if isinstance(data, dict):
        payload = json.dumps(data).encode("utf-8")
        headers = {**(headers or {}), "Content-Type": "application/json"}
    req = Request(url, data=payload, headers=headers or {}, method=method)
    try:
        response = opener.open(req, timeout=10)
    except HTTPError as exc:
        if 300 <= exc.code < 400:
            return exc.code, dict(exc.headers), exc.read()
        raise RuntimeError(f"{method} {url} returned {exc.code}: {exc.read().decode()}") from exc
    with response:
        return response.status, dict(response.headers), response.read()


def location(headers: dict[str, str]) -> str:
    value = headers.get("Location") or headers.get("location")
    if not value:
        raise AssertionError("redirect response has no Location header")
    return value


def host_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname != "gitlab.localhost":
        return url
    return urlunparse(parsed._replace(netloc=f"localhost:{parsed.port or 8088}"))


def json_request(url: str, *, method: str = "GET", data=None, token: str | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else None
    status_code, _, body = request(url, method=method, data=data, headers=headers)
    if not 200 <= status_code < 300:
        raise AssertionError(f"unexpected status {status_code} for {url}")
    return json.loads(body)


def main() -> int:
    status_code, headers, _ = request(f"{FRONTEND_URL}/auth/gitlab/login")
    assert status_code == 302
    authorization_url = host_url(location(headers))

    invalid_credentials = urlencode(
        {"username": "missing-user", "password": "wrong-password"}
    ).encode("ascii")
    try:
        request(
            authorization_url,
            method="POST",
            data=invalid_credentials,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    except RuntimeError as exc:
        assert "returned 401" in str(exc)
    else:
        raise AssertionError("unknown LDAP/GitLab account was allowed")

    credentials = urlencode(
        {"username": "engineer", "password": "factory-password"}
    ).encode("ascii")
    status_code, headers, _ = request(
        authorization_url,
        method="POST",
        data=credentials,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert status_code == 302

    status_code, headers, _ = request(location(headers))
    assert status_code == 302
    callback_to_frontend = location(headers)
    auth_code = parse_qs(urlparse(callback_to_frontend).query)["auth_code"][0]

    tokens = json_request(
        f"{FRONTEND_URL}/auth/gitlab/exchange",
        method="POST",
        data={"code": auth_code},
    )
    balance_token = tokens["access_token"]
    try:
        json_request(
            f"{FRONTEND_URL}/auth/gitlab/exchange",
            method="POST",
            data={"code": auth_code},
        )
    except RuntimeError as exc:
        assert "returned 401" in str(exc)
    else:
        raise AssertionError("one-time frontend login code was accepted twice")

    profile = json_request(f"{FRONTEND_URL}/api/v1/user/me", token=balance_token)
    assert profile["username"] == "engineer"
    assert profile["gitlab_user_id"] == 17

    projects = json_request(f"{FRONTEND_URL}/api/v1/projects", token=balance_token)
    assert projects[0]["id"] == 41

    task = json_request(
        f"{FRONTEND_URL}/api/v1/tasks",
        method="POST",
        token=balance_token,
        data={
            "title": "OAuth smoke calculation",
            "description": "Created by the local GitLab/LDAP simulator",
            "labels": ["bureau::btr", "module::btr-condensers"],
            "project_id": 41,
        },
    )
    issue_iid = task["iid"]

    branch = json_request(
        f"{FRONTEND_URL}/api/v1/tasks/{issue_iid}/branch",
        method="POST",
        token=balance_token,
        data={"project_id": 41},
    )
    assert branch["created"] is True

    merge_request = json_request(
        f"{FRONTEND_URL}/api/v1/tasks/{issue_iid}/submit?project_id=41",
        method="POST",
        token=balance_token,
    )
    assert merge_request["status"] == "success"

    audit = json_request("http://localhost:8088/__mock__/audit")
    assert audit["events"]
    assert {event["username"] for event in audit["events"]} == {"engineer"}
    assert any(
        event["grant_type"] == "refresh_token" and event["username"] == "engineer"
        for event in audit["oauth_events"]
    )
    required_writes = {
        "/api/v4/projects/41/issues",
        "/api/v4/projects/41/repository/branches",
        "/api/v4/projects/41/merge_requests",
    }
    actual_writes = {
        event["path"] for event in audit["events"] if event["method"] == "POST"
    }
    assert required_writes <= actual_writes

    print("OK: OAuth + PKCE + simulated LDAP + per-user GitLab writes passed")
    print(f"User: {profile['gitlab_username']}; issue: #{issue_iid}; MR: {merge_request['mr_url']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise
