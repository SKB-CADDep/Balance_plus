from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from fastapi import FastAPI, Form, Header, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

app = FastAPI(title="Local GitLab OAuth simulator")

CLIENT_ID = os.getenv("MOCK_GITLAB_CLIENT_ID", "balance-local-client")
CLIENT_SECRET = os.getenv("MOCK_GITLAB_CLIENT_SECRET", "balance-local-secret")
LDAP_USERNAME = os.getenv("MOCK_LDAP_USERNAME", "engineer")
LDAP_PASSWORD = os.getenv("MOCK_LDAP_PASSWORD", "factory-password")
PROJECT_ID = int(os.getenv("MOCK_GITLAB_PROJECT_ID", "41"))
INITIAL_TOKEN_EXPIRES_IN = int(os.getenv("MOCK_GITLAB_INITIAL_TOKEN_EXPIRES_IN", "7200"))

USER = {
    "id": 17,
    "username": LDAP_USERNAME,
    "name": "Local LDAP Engineer",
    "email": f"{LDAP_USERNAME}@utz.local",
    "public_email": f"{LDAP_USERNAME}@utz.local",
    "state": "active",
    "web_url": f"http://gitlab.localhost:8088/{LDAP_USERNAME}",
}
PROJECT = {
    "id": PROJECT_ID,
    "name": "Balance local project",
    "name_with_namespace": "UTZ / Balance local project",
    "path": "balance-local",
    "path_with_namespace": "utz/balance-local",
    "default_branch": "develop",
    "web_url": "http://gitlab.localhost:8088/utz/balance-local",
}

authorization_codes: dict[str, dict[str, str]] = {}
access_tokens: dict[str, str] = {}
refresh_tokens: dict[str, str] = {}
issues: dict[int, dict[str, Any]] = {}
branches: set[str] = {"develop"}
merge_requests: list[dict[str, Any]] = []
audit_log: list[dict[str, str]] = []
oauth_audit_log: list[dict[str, str]] = []


def _list_response(items: list[dict[str, Any]]) -> JSONResponse:
    return JSONResponse(
        items,
        headers={
            "X-Page": "1",
            "X-Per-Page": "100",
            "X-Next-Page": "",
            "X-Prev-Page": "",
            "X-Total": str(len(items)),
            "X-Total-Pages": "1",
        },
    )


def _authenticated_username(authorization: str | None) -> str:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.casefold() != "bearer" or token not in access_tokens:
        raise HTTPException(status_code=401, detail="invalid OAuth token")
    return access_tokens[token]


def _audit(request: Request, authorization: str | None) -> str:
    username = _authenticated_username(authorization)
    audit_log.append(
        {"method": request.method, "path": request.url.path, "username": username}
    )
    return username


async def _request_data(request: Request) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return await request.json()
    form = await request.form()
    data: dict[str, Any] = {}
    for key in form:
        values = form.getlist(key)
        data[key] = values if len(values) > 1 else values[0]
    return data


def _issue(iid: int, title: str, description: str = "", labels: list[str] | None = None):
    return {
        "id": 1000 + iid,
        "iid": iid,
        "project_id": PROJECT_ID,
        "title": title,
        "description": description,
        "state": "opened",
        "labels": labels or [],
        "assignee": {"id": USER["id"], "username": USER["username"]},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "due_date": None,
        "web_url": f"{PROJECT['web_url']}/-/issues/{iid}",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/oauth/authorize", response_class=HTMLResponse)
async def authorize_page(
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    response_type: str = Query(...),
    state: str = Query(...),
    scope: str = Query("api"),
    code_challenge: str = Query(...),
    code_challenge_method: str = Query(...),
):
    if client_id != CLIENT_ID or response_type != "code" or code_challenge_method != "S256":
        raise HTTPException(status_code=400, detail="invalid OAuth authorization request")
    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
            "state": state,
            "scope": scope,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
        }
    )
    return f"""
    <!doctype html>
    <html lang="ru"><head><meta charset="utf-8"><title>Mock GitLab LDAP</title></head>
    <body style="font-family:sans-serif;max-width:440px;margin:60px auto">
      <h1>GitLab — локальная LDAP-симуляция</h1>
      <p>Тестовая учётная запись: <b>{html.escape(LDAP_USERNAME)}</b></p>
      <form method="post" action="/oauth/authorize?{html.escape(query)}">
        <label>LDAP login <input name="username" required autofocus></label><br><br>
        <label>LDAP password <input name="password" type="password" required></label><br><br>
        <button type="submit">Войти и разрешить доступ</button>
      </form>
    </body></html>
    """


@app.post("/oauth/authorize")
async def authorize_submit(
    username: str = Form(...),
    password: str = Form(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    state: str = Query(...),
    scope: str = Query("api"),
    code_challenge: str = Query(...),
    code_challenge_method: str = Query(...),
):
    if client_id != CLIENT_ID or code_challenge_method != "S256":
        raise HTTPException(status_code=400, detail="invalid OAuth client")
    if username != LDAP_USERNAME or password != LDAP_PASSWORD:
        raise HTTPException(status_code=401, detail="LDAP account does not exist or is disabled")
    code = secrets.token_urlsafe(32)
    authorization_codes[code] = {
        "username": username,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "code_challenge": code_challenge,
    }
    separator = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(
        f"{redirect_uri}{separator}{urlencode({'code': code, 'state': state})}",
        status_code=status.HTTP_302_FOUND,
    )


@app.post("/oauth/token")
async def oauth_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    code: str | None = Form(default=None),
    redirect_uri: str | None = Form(default=None),
    code_verifier: str | None = Form(default=None),
    refresh_token: str | None = Form(default=None),
):
    if client_id != CLIENT_ID or client_secret != CLIENT_SECRET:
        raise HTTPException(status_code=401, detail="invalid OAuth client")

    if grant_type == "authorization_code":
        record = authorization_codes.pop(code or "", None)
        if not record or record["redirect_uri"] != redirect_uri or not code_verifier:
            raise HTTPException(status_code=400, detail="invalid authorization code")
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        if not secrets.compare_digest(challenge, record["code_challenge"]):
            raise HTTPException(status_code=400, detail="PKCE verification failed")
        username = record["username"]
        scope = record["scope"]
        expires_in = INITIAL_TOKEN_EXPIRES_IN
    elif grant_type == "refresh_token":
        username = refresh_tokens.pop(refresh_token or "", "")
        if not username:
            raise HTTPException(status_code=400, detail="invalid refresh token")
        scope = "api"
        expires_in = 7200
    else:
        raise HTTPException(status_code=400, detail="unsupported grant type")

    new_access_token = f"oauth-{secrets.token_urlsafe(24)}"
    new_refresh_token = f"refresh-{secrets.token_urlsafe(24)}"
    access_tokens[new_access_token] = username
    refresh_tokens[new_refresh_token] = username
    oauth_audit_log.append({"grant_type": grant_type, "username": username})
    return {
        "access_token": new_access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "refresh_token": new_refresh_token,
        "scope": scope,
        "created_at": int(datetime.now(timezone.utc).timestamp()),
    }


@app.get("/api/v4/user")
async def current_user(request: Request, authorization: str | None = Header(default=None)):
    _audit(request, authorization)
    return USER


@app.get("/api/v4/groups/{group_id}")
async def get_group(group_id: int, request: Request, authorization: str | None = Header(default=None)):
    _audit(request, authorization)
    return {"id": group_id, "name": "Local Balance users", "path": "balance-users"}


@app.get("/api/v4/projects")
async def list_projects(request: Request, authorization: str | None = Header(default=None)):
    _audit(request, authorization)
    return _list_response([PROJECT])


@app.get("/api/v4/projects/{project_id}")
async def get_project(project_id: int, request: Request, authorization: str | None = Header(default=None)):
    _audit(request, authorization)
    if project_id != PROJECT_ID:
        raise HTTPException(status_code=404, detail="project not found")
    return PROJECT


@app.get("/api/v4/issues")
async def list_global_issues(request: Request, authorization: str | None = Header(default=None)):
    _audit(request, authorization)
    return _list_response(list(issues.values()))


@app.get("/api/v4/projects/{project_id}/issues")
async def list_project_issues(project_id: int, request: Request, authorization: str | None = Header(default=None)):
    _audit(request, authorization)
    if project_id != PROJECT_ID:
        raise HTTPException(status_code=404, detail="project not found")
    return _list_response(list(issues.values()))


@app.post("/api/v4/projects/{project_id}/issues")
async def create_issue(project_id: int, request: Request, authorization: str | None = Header(default=None)):
    _audit(request, authorization)
    if project_id != PROJECT_ID:
        raise HTTPException(status_code=404, detail="project not found")
    data = await _request_data(request)
    raw_labels = data.get("labels", [])
    if isinstance(raw_labels, str):
        try:
            parsed_labels = json.loads(raw_labels)
            labels = parsed_labels if isinstance(parsed_labels, list) else raw_labels.split(",")
        except json.JSONDecodeError:
            labels = [label for label in raw_labels.split(",") if label]
    else:
        labels = list(raw_labels)
    iid = max(issues, default=0) + 1
    issue = _issue(iid, str(data.get("title", "Local task")), str(data.get("description", "")), labels)
    issues[iid] = issue
    return issue


@app.get("/api/v4/projects/{project_id}/issues/{issue_iid}")
async def get_issue(project_id: int, issue_iid: int, request: Request, authorization: str | None = Header(default=None)):
    _audit(request, authorization)
    if project_id != PROJECT_ID or issue_iid not in issues:
        raise HTTPException(status_code=404, detail="issue not found")
    return issues[issue_iid]


@app.get("/api/v4/projects/{project_id}/repository/branches")
async def list_branches(project_id: int, request: Request, authorization: str | None = Header(default=None), search: str = ""):
    _audit(request, authorization)
    if project_id != PROJECT_ID:
        raise HTTPException(status_code=404, detail="project not found")
    items = [{"name": name, "default": name == PROJECT["default_branch"]} for name in sorted(branches) if search in name]
    return _list_response(items)


@app.post("/api/v4/projects/{project_id}/repository/branches")
async def create_branch(project_id: int, request: Request, authorization: str | None = Header(default=None)):
    _audit(request, authorization)
    if project_id != PROJECT_ID:
        raise HTTPException(status_code=404, detail="project not found")
    data = await _request_data(request)
    branch = str(data.get("branch", ""))
    if not branch:
        raise HTTPException(status_code=400, detail="branch is required")
    if branch in branches:
        raise HTTPException(status_code=400, detail="Branch already exists")
    branches.add(branch)
    return {"name": branch, "default": False}


@app.get("/api/v4/projects/{project_id}/repository/branches/{branch:path}")
async def get_branch(project_id: int, branch: str, request: Request, authorization: str | None = Header(default=None)):
    _audit(request, authorization)
    if project_id != PROJECT_ID or branch not in branches:
        raise HTTPException(status_code=404, detail="branch not found")
    return {"name": branch, "default": branch == PROJECT["default_branch"]}


@app.post("/api/v4/projects/{project_id}/merge_requests")
async def create_merge_request(project_id: int, request: Request, authorization: str | None = Header(default=None)):
    _audit(request, authorization)
    if project_id != PROJECT_ID:
        raise HTTPException(status_code=404, detail="project not found")
    data = await _request_data(request)
    source_branch = str(data.get("source_branch", ""))
    if source_branch not in branches:
        raise HTTPException(status_code=400, detail="source branch not found")
    iid = len(merge_requests) + 1
    merge_request = {
        "id": 2000 + iid,
        "iid": iid,
        "title": str(data.get("title", "Local merge request")),
        "state": "opened",
        "source_branch": source_branch,
        "target_branch": str(data.get("target_branch", PROJECT["default_branch"])),
        "web_url": f"{PROJECT['web_url']}/-/merge_requests/{iid}",
    }
    merge_requests.append(merge_request)
    return merge_request


@app.get("/__mock__/audit")
async def audit():
    return {
        "events": audit_log,
        "oauth_events": oauth_audit_log,
        "issues": list(issues.values()),
        "merge_requests": merge_requests,
    }
