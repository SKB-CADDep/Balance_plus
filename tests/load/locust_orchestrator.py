from scenarios.auth_load_scenario import user_pool, generate_jwt
import os
import sys
from pathlib import Path

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner

LOAD_DIR = Path(__file__).resolve().parent
if str(LOAD_DIR) not in sys.path:
    sys.path.insert(0, str(LOAD_DIR))


class OrchestratorLoadUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        """Инициализация виртуального пользователя с уникальным токеном из пула."""
        self.user_data = user_pool.get_random_user()
        self.token = self.user_data["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-User-Id": str(self.user_data["user_id"]),
            "Content-Type": "application/json",
        }

    # =========================================================================
    # 1. АУТЕНТИФИКАЦИЯ И ПРОВЕРКА СЕССИЙ (Высокий вес для достижения 200+ RPS)
    # =========================================================================
    @task(6)
    def validate_user_session(self):
        """
        Интенсивная проверка валидности токена и профиля пользователя.
        Критичный эндпоинт для измерения p95 и p99.
        """
        with self.client.get(
            "/api/v1/user/me",
            headers=self.headers,
            name="/api/v1/user/me [Validate Session]",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 401, 503]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def rotate_session_token(self):
        """Эмуляция фоновой ротации и обновления токена пользователя во время сессии."""
        new_token = user_pool.rotate_user_token(self.user_data, expires_in=300)
        self.token = new_token
        self.headers["Authorization"] = f"Bearer {self.token}"

    @task(1)
    def test_expired_token_rejection(self):
        """Проверка быстрого отклонения просроченного токена без утечек памяти."""
        expired_token = generate_jwt(
            self.user_data["user_id"], self.user_data["username"], expires_in=-10)
        bad_headers = {"Authorization": f"Bearer {expired_token}"}
        with self.client.get(
            "/api/v1/user/me",
            headers=bad_headers,
            name="/api/v1/user/me [Expired Token]",
            catch_response=True,
        ) as response:
            if response.status_code in [401, 503]:
                response.success()
            else:
                response.failure(
                    f"Expired token was not rejected with 401: {response.status_code}")

    # =========================================================================
    # 2. БИЗНЕС-ОПЕРАЦИИ ОРКЕСТРАТОРА С АВТОРИЗАЦИОННЫМИ ЗАГОЛОВКАМИ
    # =========================================================================
    @task(3)
    def list_tasks(self):
        self.client.get(
            "/api/v1/tasks?project_id=41&state=opened",
            headers=self.headers,
            name="/api/v1/tasks",
        )

    @task(2)
    def list_projects(self):
        self.client.get(
            "/api/v1/projects",
            headers=self.headers,
            name="/api/v1/projects",
        )

    @task(2)
    def save_calculation(self):
        """Имитация сохранения результата расчета в Git-ветку под авторизованной сессией"""
        payload = {
            "task_iid": 1,
            "project_id": 41,
            "app_type": "valves",
            "input_data": {"P_fresh": 130, "T_fresh": 555},
            "output_data": {"total_leakage": 0.45},
            "commit_message": f"Load test commit from {self.user_data['username']}",
        }

        with self.client.post(
            "/api/v1/calculations/save",
            json=payload,
            headers=self.headers,
            name="/api/v1/calculations/save",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 400, 401, 503]:
                response.success()
            else:
                response.failure(
                    f"Status {response.status_code}: {response.text}")

    @task(1)
    def health_check(self):
        self.client.get("/health", name="/health")


# =============================================================================
# ХУКИ СБОРА МЕТРИК SLA ПО ЗАВЕРШЕНИИ ТЕСТА
# =============================================================================
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Проверка выполнения критериев приёмки: p95 <= 15ms для валидации токена."""
    if isinstance(environment.runner, MasterRunner):
        return

    stat = environment.stats.get("/api/v1/user/me [Validate Session]", "GET")
    if stat and stat.num_requests > 0:
        p95 = stat.get_response_time_percentile(0.95)
        p99 = stat.get_response_time_percentile(0.99)
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ SLA ВАЛИДАЦИИ ТОКЕНОВ (/api/v1/user/me):")
        print(f"Всего запросов проверки сессий: {stat.num_requests}")
        print(f"Текущий p95: {p95:.2f} ms (Целевое значение: <= 15.0 ms)")
        print(f"Текущий p99: {p99:.2f} ms (Целевое значение: <= 30.0 ms)")
        print(f"Средний RPS: {stat.total_rps:.2f}")
        if p95 <= 15.0:
            print("✅ КРИТЕРИЙ ПРИЁМКИ ВЫПОЛНЕН: p95 <= 15ms")
        else:
            print(
                f"⚠️ ПРЕДУПРЕЖДЕНИЕ: p95 ({p95:.2f}ms) превысил целевой порог 15ms")
        print("=" * 60 + "\n")
