import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
class TestNegativeValidation:
    def setup_method(self, method):
        self.transport = ASGITransport(app=app)
        # ВНИМАНИЕ: Сверяем со Swagger!
        self.url = "/api/v1/calculate" 

    async def test_negative_pressure(self):
        """QA-5: Отрицательное давление -> 422"""
        payload = {
            "turbine_id": 1, # Добавили обязательное поле
            "globals": {"P_fresh": -100.0, "T_fresh": 540.0, "P_air": 1.033},
            "groups": [
                {
                    "valve_id": 9, "type": "СК", "quantity": 1, 
                    "valve_names": ["К-1"], "p_values": [130, 1.033]
                }
            ]
        }
        async with AsyncClient(transport=self.transport, base_url="http://test") as ac:
            response = await ac.post(self.url, json=payload)
        
        # Теперь путь верный, и Pydantic должен вернуть 422 на отрицательное число
        assert response.status_code == 422

    async def test_string_instead_of_number(self):
        """QA-5: Текст вместо числа -> 422"""
        payload = {
            "turbine_id": 1,
            "globals": {"P_fresh": "invalid"},
            "groups": []
        }
        async with AsyncClient(transport=self.transport, base_url="http://test") as ac:
            response = await ac.post(self.url, json=payload)
        assert response.status_code == 422