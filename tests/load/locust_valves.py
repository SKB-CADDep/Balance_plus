import random
from locust import HttpUser, task, between

class ValveStemsUser(HttpUser):
    wait_time = between(1, 4)

    @task(3)
    def calculate_multi(self):
        # URL теперь точно верный (подтверждено pytest)
        url = "/api/v1/calculate" 
        
        payload = {
            "turbine_id": 1,
            "globals": {
                "P_fresh": 130.0,
                "P_fresh_unit": "кгс/см²",
                "T_fresh": 555.0,
                "T_fresh_unit": "°C",
                "P_air": 1.033,
                "T_air": 40.0,
                "P_lst_leak_off": 0.97
            },
            "groups": [
                {
                    "valve_id": 9,
                    "type": "СК",
                    "valve_names": ["СК-1", "СК-2"], 
                    "quantity": 2,
                    # ИСПРАВЛЕНО: поле теперь называется p_leak_offs
                    # Для 3 участков (клапан 9) передаем ровно 1 значение
                    "p_leak_offs": [10.0], 
                    "p_leak_offs_unit": "кгс/см²"
                }
            ]
        }
        
        # Рандомизация давления, чтобы нагрузить движок разными итерациями
        payload["globals"]["P_fresh"] = random.uniform(125.0, 135.0)

        with self.client.post(url, json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                # Если здесь вылезет 422, Locust покажет в чем именно ошибка валидации
                response.failure(f"Error {response.status_code}: {response.text}")

    @task(1)
    def get_turbines(self):
        self.client.get("/api/v1/turbines/")