from locust import HttpUser, task, between

class OrchestratorLoadUser(HttpUser):
    # Менеджеры работают быстро, пауза 1-3 секунды
    wait_time = between(1, 3)

    @task(2)
    def list_tasks(self):
        self.client.get("/api/v1/tasks?project_id=41&state=opened")

    @task(1)
    def list_projects(self):
        self.client.get("/api/v1/projects")

    @task(2)
    def save_calculation(self):
        """Имитация сохранения результата расчета в Git-ветку"""
        url = "/api/v1/calculations/save"
        
        payload = {
            "task_iid": 1,        # IID реальной задачи
            "project_id": 41,     # ID вашего проекта
            "app_type": "valves", # или "condenser"
            "input_data": {"test_param": 100},
            "output_data": {"result": "success"},
            "commit_message": "Load test commit"
        }

        with self.client.post(url, json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 400:
                # Мы специально настроили роут возвращать 400, если ветка не найдена
                response.success() 
            else:
                response.failure(f"Status {response.status_code}: {response.text}")

    @task(1)
    def health_check(self):
        self.client.get("/health")