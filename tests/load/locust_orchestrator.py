from locust import HttpUser, task, between

class OrchestratorUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def list_tasks(self):
        """Проверка работы с GitLab через Оркестратор"""
        self.client.get("/api/v1/tasks/?project_id=41&state=opened")

    @task
    def health_db(self):
        self.client.get("/api/v1/health/db")