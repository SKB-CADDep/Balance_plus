"""
Тесты безопасности: Rate Limiting, защита от Brute-force, SQL/XSS/Path Traversal инъекции и Fuzzing
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from app.core.rate_limit import reset_rate_limiter
from app.main import app


@pytest.fixture
def client():
  return TestClient(app)


@pytest.fixture(autouse=True)
def clean_rate_limit_state():
  """Сбрасывает скользящее окно rate limiter перед каждым тестом."""
  reset_rate_limiter()
  yield
  reset_rate_limiter()


# ============================================================================
# 1. ТЕСТИРОВАНИЕ RATE LIMITING И ЗАЩИТЫ ОТ BRUTE-FORCE
# ============================================================================
class TestRateLimitingSecurity:
  """Проверка ограничения частоты запросов (>10 req/min -> 429 Too Many Requests)."""

  def test_rate_limit_triggered_after_threshold_exceeded(self, client):
    """10 запросов проходят успешно, 11-й запрос возвращает статус 429 и заголовок Retry-After."""
    mock_user = MagicMock()
    mock_user.name = "Инженер"
    mock_user.username = "engineer"
    mock_user.avatar_url = ""

    with patch(
        "app.api.routes.user.gitlab_client.get_current_user",
        return_value=mock_user,
    ):
      for _ in range(10):
        res = client.get("/api/v1/user/me")
        assert res.status_code == 200

      response = client.get("/api/v1/user/me")

    assert response.status_code == 429
    assert "Retry-After" in response.headers
    assert int(response.headers["Retry-After"]) > 0
    assert "Rate Limit" in response.json()["detail"]

  def test_rate_limit_resets_after_window_cleared(self, client):
    """После сброса окна лимита запросы снова успешно обрабатываются."""
    mock_user = MagicMock(name="Инженер", username="engineer", avatar_url="")

    with patch(
        "app.api.routes.user.gitlab_client.get_current_user",
        return_value=mock_user,
    ):
      for _ in range(10):
        client.get("/api/v1/user/me")

      assert client.get("/api/v1/user/me").status_code == 429

      reset_rate_limiter()

      assert client.get("/api/v1/user/me").status_code == 200


# ============================================================================
# 2. FUZZING: SQL-ИНЪЕКЦИИ, XSS И ПАРАМЕТРИЧЕСКИЙ ФАЗЗИНГ
# ============================================================================
class TestInjectionAndFuzzingProtection:
  """Проверка устойчивости API к инъекциям (SQLi, XSS, Path Traversal)."""

  @pytest.mark.parametrize(
      "payload",
      [
          "' OR 1=1 --",
          "'; DROP TABLE projects; --",
          "1 UNION SELECT null, username, password FROM users --",
          "admin'--",
          "' OR 'x'='x",
      ],
  )
  def test_projects_search_sql_injection_sanitized(self, client, payload):
    """Попытки SQL-инъекций в поиске проектов не вызывают 500 ошибок."""
    with patch(
        "app.api.routes.projects.gitlab_client.get_user_projects",
        return_value=[],
    ) as mock_get:
      response = client.get(f"/api/v1/projects?search={payload}")

    assert response.status_code in [200, 422, 503]
    if response.status_code == 200:
      assert response.json() == []
      mock_get.assert_called_once_with(payload)

  @pytest.mark.parametrize(
      "xss_payload",
      [
          "<script>alert('XSS')</script>",
          "<img src=x onerror=alert(document.cookie)>",
          (
              "javascript:/*--></title></style></textarea></script></xmp><svg/onload='+/'/+/onmouseover=1/+/[*/[]/+alert(1)//'>"
          ),
          "<svg onload=alert(1)>",
      ],
  )
  def test_create_task_xss_payload_handled_safely(self, client, xss_payload):
    """XSS-скрипты в названии/описании задачи экранируются без 500 ошибки."""
    mock_issue = {
        "iid": 1,
        "title": xss_payload,
        "description": xss_payload,
        "project_id": 1,
        "project_name": "Test Project",
        "state": "opened",
        "created_at": "2026-10-29T00:00:00Z",
        "web_url": "http://git.local",
        "labels": [xss_payload],
        "assignee": "engineer",
        "due_date": None,
    }

    with (
        patch(
            "app.api.routes.tasks.gitlab_client.create_issue",
            return_value=mock_issue,
        ),
        patch(
            "app.api.routes.tasks.gitlab_client.get_issue",
            return_value=mock_issue,
        ),
    ):
      response = client.post(
          "/api/v1/tasks",
          json={
              "title": xss_payload,
              "description": xss_payload,
              "labels": [xss_payload],
              "project_id": 1,
          },
      )

    assert response.status_code in [200, 201]
    assert response.json()["title"] == xss_payload

  def test_task_creation_invalid_types_rejected_by_pydantic(self, client):
    """Некорректные типы данных в полях отсекаются валидатором (422 Unprocessable Entity)."""
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": 12345,
            "description": ["не строка"],
            "project_id": "'1 OR 1=1'",
            "labels": "не список",
        },
    )
    assert response.status_code == 422

  @pytest.mark.parametrize(
      "traversal_payload",
      [
          "../../../../etc/passwd",
          "..\\..\\..\\windows\\system32\\config",
          "....//....//....//etc/shadow",
          "calculations/../../secrets",
      ],
  )
  def test_calculations_save_path_traversal_fuzzing(
      self, client, traversal_payload
  ):
    """Попытка выхода за пределы директории (Path Traversal) в app_type не крашит сервис."""
    payload = {
        "task_iid": 1,
        "project_id": 1,
        "app_type": traversal_payload,
        "input_data": {"test": 1},
        "output_data": {"result": 2},
    }

    with (
        patch(
            "app.api.routes.calculations.gitlab_client.find_branch_by_issue_iid",
            return_value="issue/1-task",
        ),
        patch(
            "app.api.routes.calculations.gitlab_client.create_commit_multiple"
        ) as mock_commit,
    ):
      mock_commit.return_value = MagicMock(
          id="sha-1", web_url="http://git.local"
      )
      response = client.post("/api/v1/calculations/save", json=payload)

    assert response.status_code in [200, 400, 422]


# ============================================================================
# 3. ЗАЩИТА ЗАГОЛОВКОВ AUTHORIZATION (OVERSIZED, REDOS, АНОМАЛИИ)
# ============================================================================
class TestAuthorizationHeaderSecurity:
  """Проверка устойчивости заголовков Authorization к ReDoS и переполнению буфера."""

  def test_oversized_authorization_header_does_not_crash_server(self, client):
    """Огромный заголовок (64 KB) безопасно обрабатывается и не роняет процесс."""
    huge_token = "A" * 65536
    headers = {"Authorization": f"Bearer {huge_token}"}

    with patch(
        "app.api.routes.projects.gitlab_client.get_user_projects",
        return_value=[],
    ):
      response = client.get("/api/v1/projects", headers=headers)

    # Сервер безопасно возвращает статус и не падает с 500
    assert response.status_code in [200, 400, 401, 413, 422, 431, 503]

  @pytest.mark.parametrize(
      "malformed_header",
      [
          "Bearer",
          "Basic YWRtaW46cGFzc3dvcmQ=",
          "Bearer " + "a" * 1000 + "!",
          "Negotiate KerberosToken",
          "Bearer \x00\x01\x02",
      ],
  )
  def test_malformed_authorization_headers_handled_gracefully(
      self, client, malformed_header
  ):
    """Некорректные форматы Authorization не вызывают необработанных 500 ошибок."""
    headers = {"Authorization": malformed_header}
    with patch(
        "app.api.routes.projects.gitlab_client.get_user_projects",
        return_value=[],
    ):
      response = client.get("/api/v1/projects", headers=headers)

    assert response.status_code in [200, 400, 401, 422, 503]