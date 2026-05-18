from locust import HttpUser, task, between

class CondenserUser(HttpUser):
    wait_time = between(2, 5)

    @task
    def calculate_condenser(self):
        # Эндпоинт из Swagger сервиса конденсаторов
        url = "/api/v1/calculations/calculate/berman"
        
        payload = {
            "condenser_id": 1,
            "material_id": 1,
            "calculation_method": "berman",
            "g_steam": [150.0, 200.0],
            "t1_main": [20.0, 25.0],
            "w_main": [1.5, 2.0],
            "coefficient_b": [0.9, 0.95]
        }
        
        self.client.post(url, json=payload)