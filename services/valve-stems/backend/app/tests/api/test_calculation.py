"""
Тесты для calculation check endpoints.
"""

import pytest

from app.tests.crud.test_crud import (
    create_test_calculation_result,
    create_test_turbine,
    create_test_valve,
)

@pytest.mark.asyncio
async def test_get_calculation_results(async_client, db_session):
    """Тест проверки получения списка результатов(GET)."""
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_name="VD-005")
    input_data = {
        "turbine_name": "Test Turbine",
        "valve_drawing": "VD-001",
        "valve_id": valve.id,
        "temperature_start": 100.0,
        "t_air": 300.0,
        "count_valves": 2,
        "p_ejector": [1.0, 2.0],
        "p_values": [3.0, 4.0],
    }

    output_data = {
        "Gi": [1.1, 2.2],
        "Pi_in": [3.3, 4.4],
        "Ti": [5.5, 6.6],
        "Hi": [7.7, 8.8],
        "deaerator_props": [9.9, 10.1, 11.11, 12.12],
        "ejector_props": [{"g": 13.13, "t": 14.14, "h": 15.15, "p": 16.16}],
    }

    test_results = create_test_calculation_result(db_session, valve.name, input_data, output_data)
    response = await async_client.get(f"/api/v1/valves/{valve.name}/results/")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["stock_name"] == valve.name


@pytest.mark.asyncio
async def test_delete_calculation_result(async_client, db_session):
    """Тест проверки удаления результата по id(DELETE)."""
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_name="VD-005")
    input_data = {
        "turbine_name": "Test Turbine",
        "valve_drawing": "VD-001",
        "valve_id": valve.id,
        "temperature_start": 100.0,
        "t_air": 300.0,
        "count_valves": 2,
        "p_ejector": [1.0, 2.0],
        "p_values": [3.0, 4.0],
    }

    output_data = {
        "Gi": [1.1, 2.2],
        "Pi_in": [3.3, 4.4],
        "Ti": [5.5, 6.6],
        "Hi": [7.7, 8.8],
        "deaerator_props": [9.9, 10.1, 11.11, 12.12],
        "ejector_props": [{"g": 13.13, "t": 14.14, "h": 15.15, "p": 16.16}],
    }

    result = create_test_calculation_result(db_session, valve.name, input_data, output_data)
    response = await async_client.delete(f"/api/v1/{result.id}")
    assert response.status_code == 204
    assert response.content == b""