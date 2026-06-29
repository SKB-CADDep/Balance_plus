import pytest


@pytest.mark.asyncio
async def test_negative_pressure(async_client):
    """QA-5: Отрицательное давление -> 422"""
    payload = {
        "turbine_id": 1,
        "globals": {"P_fresh": -100.0, "T_fresh": 540.0, "P_air": 1.033},
        "groups": [
            {
                "valve_id": 9,
                "type": "СК",
                "quantity": 1,
                "valve_names": ["К-1"],
                "p_values": [130, 1.033],
            }
        ],
    }
    response = await async_client.post("/api/v1/calculate", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_string_instead_of_number(async_client):
    """QA-5: Текст вместо числа -> 422"""
    payload = {"turbine_id": 1, "globals": {"P_fresh": "invalid"}, "groups": []}
    response = await async_client.post("/api/v1/calculate", json=payload)
    assert response.status_code == 422
