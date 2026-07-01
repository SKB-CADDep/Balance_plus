import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
class TestCondenserNegativeValidation:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Используем современный транспорт для httpx
        self.transport = ASGITransport(app=app)
        self.url = "/api/v1/calculate"

    async def test_berman_missing_h_steam(self):
        """QA-5: Метод 'berman' без H_steam должен возвращать 422 (бизнес-валидатор)"""
        payload = {
            "condenser_id": 1,
            "material_id": 1,
            "method": "berman",
            "coefficient_b": [0.95],
            "G_steam": [150.0],
            "W_main": [12000.0],
            "t1_main": [15.0],
            "H_steam": None,  # Ошибка здесь!
        }
        async with AsyncClient(transport=self.transport, base_url="http://test") as ac:
            response = await ac.post(self.url, json=payload)

        assert response.status_code == 422
        assert "H_steam" in response.text

    async def test_invalid_method_name(self):
        """QA-5: Несуществующий метод расчета -> 422"""
        payload = {
            "condenser_id": 1,
            "material_id": 1,
            "method": "unknown_strategy",  # Ошибка здесь (Enum/Literal)
            "G_steam": [100.0],
            "W_main": [10000.0],
            "t1_main": [15.0],
        }
        async with AsyncClient(transport=self.transport, base_url="http://test") as ac:
            response = await ac.post(self.url, json=payload)
        assert response.status_code == 422

    async def test_coefficient_b_out_of_range(self):
        """QA-5: Коэффициент чистоты > 1.0 -> 422"""
        payload = {
            "condenser_id": 1,
            "material_id": 1,
            "method": "metro-vickers",
            "coefficient_b": [1.5],  # Ошибка здесь (max 1.0)
            "G_steam": [100.0],
            "W_main": [10000.0],
            "t1_main": [15.0],
        }
        async with AsyncClient(transport=self.transport, base_url="http://test") as ac:
            response = await ac.post(self.url, json=payload)
        assert response.status_code == 422

    async def test_empty_arrays(self):
        """QA-5: Пустые массивы входных данных -> 422"""
        payload = {
            "condenser_id": 1,
            "material_id": 1,
            "method": "berman",
            "G_steam": [],  # Ошибка здесь (min_length=1)
            "W_main": [10000.0],
            "t1_main": [15.0],
            "H_steam": 550.0,
        }
        async with AsyncClient(transport=self.transport, base_url="http://test") as ac:
            response = await ac.post(self.url, json=payload)
        assert response.status_code == 422

    async def test_string_in_numeric_array(self):
        """QA-5: Текст внутри массива чисел -> 422"""
        payload = {
            "condenser_id": 1,
            "material_id": 1,
            "method": "metro-vickers",
            "G_steam": [100.0, "МНОГО"],  # Ошибка здесь
            "W_main": [10000.0],
            "t1_main": [15.0],
        }
        async with AsyncClient(transport=self.transport, base_url="http://test") as ac:
            response = await ac.post(self.url, json=payload)
        assert response.status_code == 422
