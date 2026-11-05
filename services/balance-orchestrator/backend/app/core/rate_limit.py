"""
Модуль ограничения частоты запросов (Rate Limiting) для защиты аутентификационных эндпоинтов
"""

from collections import defaultdict
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_requests_store: dict[str, list[float]] = defaultdict(list)


def reset_rate_limiter() -> None:
  """Сброс счётчиков запросов (для изоляции тестов)."""
  _requests_store.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
  """
  In-memory Rate Limiter для ограничения частоты запросов с одного IP.
  По умолчанию: не более 10 запросов в 60 секунд на эндпоинты авторизации и профиля.
  """

  def __init__(self, app, max_requests: int = 10, window_seconds: int = 60):
    super().__init__(app)
    self.max_requests = max_requests
    self.window_seconds = window_seconds

  async def dispatch(self, request: Request, call_next):
    path = request.url.path

    if path.startswith("/api/v1/user") or path.startswith("/api/v1/auth"):
      client_ip = request.client.host if request.client else "127.0.0.1"
      key = f"{client_ip}:{path}"
      now = time.time()

      _requests_store[key] = [
          req_time
          for req_time in _requests_store[key]
          if now - req_time < self.window_seconds
      ]

      if len(_requests_store[key]) >= self.max_requests:
        earliest_request = _requests_store[key][0]
        retry_after = max(
            1, int(self.window_seconds - (now - earliest_request))
        )
        return JSONResponse(
            status_code=429,
            content={
                "detail": (
                    "Слишком много запросов. Превышен лимит Rate Limit."
                )
            },
            headers={"Retry-After": str(retry_after)},
        )

      _requests_store[key].append(now)

    return await call_next(request)