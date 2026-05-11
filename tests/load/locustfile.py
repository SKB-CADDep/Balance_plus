import random
from locust import HttpUser, task, between

class ValveStemsLoadUser(HttpUser):
    """
    Класс описывает одного виртуального инженера.
    Если мы скажем Locust запустить 100 пользователей, он создаст 100 таких объектов,
    и они будут работать параллельно.
    """
    
    # Имитация человеческого поведения: 
    # инженер делает клик, ждет от 1 до 5 секунд (изучает результат), затем кликает снова.
    wait_time = between(1, 5) 

    # Базовый JSON, который фронтенд отправляет на бэкенд "Штоков" для расчета.
    # Мы используем структуру, которую вычистили в таске QA-1.
    base_payload = {
        "globals": {
            "P_fresh": 130.0,
            "P_fresh_unit": "кгс/см²",
            "T_fresh": 555.0,
            "T_fresh_unit": "°C",
            "P_air": 1.033,
            "T_air": 40.0,
            "P_lst_leak_off": 0.97
        },
        "groups":[
            {
                "valve_id": 9,
                "type": "СК",
                "valve_names": ["К-1", "К-2"],
                "quantity": 2,
                "p_values":[130.0, 10.0, 1.033],
                "p_values_unit": "кгс/см²"
            }
        ]
    }

    # Декоратор @task() означает "Действие пользователя".
    # Цифра 3 означает ВЕС (приоритет). То есть расчеты бот будет запускать 
    # в 3 раза чаще, чем дергать другие эндпоинты.
    @task(3)
    def calculate_stems(self):
        """Задача: отправить тяжелый математический расчет"""
        payload = self.base_payload.copy()
        
        # ВАЖНО: Мы делаем рандомизацию (немного меняем температуру каждый раз).
        # Зачем? Чтобы умный сервер или база данных не "закешировали" ответ.
        # Нам нужно заставить физический движок (ValvePhysicsEngine) потеть каждый раз!
        payload["globals"]["T_fresh"] = random.uniform(540.0, 560.0)
        
        # Делаем POST запрос. Путь относительный (URL мы укажем в браузере при запуске).
        # catch_response=True позволяет нам самим решать, успешен запрос или нет.
        with self.client.post("/api/v1/calculations/calculate", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                # Если сервер упадет под нагрузкой (500) или вернет 422, Locust запишет это в ошибки
                response.failure(f"Ошибка {response.status_code}: {response.text}")

    @task(1)
    def get_turbines(self):
        """Задача: просто подгрузить список турбин из БД (легкий запрос)"""
        self.client.get("/api/v1/turbines/")