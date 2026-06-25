import random
from locust import HttpUser, task, between

class CondenserLoadUser(HttpUser):
    wait_time = between(2, 5)

    @task(3)
    def calculate_berman(self):
        url = "/api/v1/calculate" 
        
        payload = {
            "condenser_id": 1,
            "material_id": 1,
            "method": "berman",
            "coefficient_b": [1.0],
            "G_steam": [150.0],     # 150 тонн пара
            "W_main": [12000.0],    # 12000 тонн воды (кратность 80 - идеал)
            "t1_main": [15.0],      # 15 градусов (центр диапазона)
            "H_steam": 550.0,
            "G_steam_unit": "т/ч",
            "W_main_unit": "т/ч",
            "t1_main_unit": "°C",
            "H_steam_unit": "ккал/кг"
        }
        
        payload["G_steam"][0] = random.uniform(140.0, 160.0)

        with self.client.post(url, json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}: {response.text}")

    @task(1)
    def get_materials(self):
        # ТОЧНЫЙ ПУТЬ ИЗ JSON (без слэша)
        self.client.get("/api/v1/materials")

    @task(1)
    def health_check(self):
        # ТОЧНЫЙ ПУТЬ ИЗ JSON (со слэшем!)
        self.client.get("/api/v1/health/")