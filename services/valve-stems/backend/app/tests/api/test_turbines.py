"""
Тесты для turbines check endpoints.
"""

import pytest

from app.tests.crud.test_crud import create_test_turbine, create_test_valve

async def test_create_turbine(async_client, db_session):
    """Тест проверки создания сущностей(POST)."""
    payload = {"name": "Test Turbine", "id": 1}
    response = await async_client.post("/api/v1/turbines", json=payload)
    data = response.json()
    assert response.status_code == 201
    assert data["name"] == "Test Turbine"


async def test_get_valves_by_turbine(async_client, db_session):
    """Тест проверки получения клапанов турбины(GET)."""
    new_turbine = create_test_turbine(db_session, "Test Turbine")
    valve1 = create_test_valve(db_session, "Test Valve1")
    valve2 = create_test_valve(db_session, "Test Valve2")
    new_turbine.valves.append(valve1)
    new_turbine.valves.append(valve2)
    db_session.commit()
    response = await async_client.get(f"/api/v1/turbines/{new_turbine.id}/valves/")
    data = response.json()
    assert data["count"] == 2
    assert response.status_code == 200


async def test_get_all_turbines_with_valves(async_client, db_session):
    """Тест проверки получения турбин с клапанами(GET)."""
    turbine1 = create_test_turbine(db_session, "Turbine1")
    turbine2 = create_test_turbine(db_session, "Turbine2")
    turbine3 = create_test_turbine(db_session, "Turbine3")
    valve1 = create_test_valve(db_session, "Test Valve1")
    valve2 = create_test_valve(db_session, "Test Valve2")
    turbine1.valves.append(valve1)
    turbine2.valves.append(valve2)
    db_session.commit()
    response = await async_client.get("/api/v1/turbines/")
    data = response.json()
    assert data[0]["name"] == "Turbine1"
    assert data[1]["name"] == "Turbine2"
    assert response.status_code == 200


async def test_read_turbine_by_id(async_client, db_session):
    """Тест проверки получения турбины по id(GET)."""
    turbine = create_test_turbine(db_session, "Test Turbine")
    response = await async_client.get(f"/api/v1/turbines/{turbine.id}")
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == "Test Turbine"
    assert data["id"] == turbine.id


async def test_get_turbine_not_found(async_client, db_session):
    """Тест проверки получения несуществующей турбины по id(GET)."""
    turbine_id = 999
    response = await async_client.get(f"/api/v1/turbines/{turbine_id}")
    assert response.status_code == 404








