"""
Тесты для turbines check endpoints.
"""

import pytest


@pytest.mark.asyncio
async def test_create_turbine(async_client, db_session):
    """Тест проверки создания сущностей(POST)."""
    payload = {"name": "Test_Turbine"}
    response = await async_client.post("/turbines", json=payload)
    data = response.json()
    assert response.status_code == 201
    assert data["name"] == "Test Turbine"


@pytest.mark.asyncio
async def test_get_valves_by_turbine(async_client, db_session):
    """Тест проверки получения клапанов турбины(GET)."""
    new_turbine = create_test_turbine(db_session, "Test Turbine")
    valve1 = create_test_valve(db_session, "Test Valve1", new_turbine.id)
    valve2 = create_test_valve(db_session, "Test Valve2", new_turbine.id)
    response = await async_client.get(f"turbines/{new_turbine.id}/valves/")
    data = response.json()
    assert data[0] is not None
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_all_turbines_with_valves(async_client, db_session):
    """Тест проверки получения турбин с клапанами(GET)."""
    turbine1 = create_test_turbine(db_session, "Turbine1")
    turbine2 = create_test_turbine(db_session, "Turbine2")
    turbine3 = create_test_turbine(db_session, "Turbine3")
    valve1 = create_test_valve(db_session, "Test Valve1", turbine1.id)
    valve2 = create_test_valve(db_session, "Test Valve2", turbine2.id)
    response = await async_client.get("/turbines/")
    data = response.json()
    assert len(data) == 3
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_read_turbine_by_id(async_client, db_session):
    """Тест проверки получения турбины по id(GET)."""
    turbine = create_test_turbine(db_session, "Test Turbine")
    response = await async_client.get(f"/turbines/{turbine.id}")
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == "Test Turbine"
    assert data["id"] == turbine.id


@pytest.mark.asyncio
async def test_get_turbine_not_found(async_client, db_session):
    """Тест проверки получения несуществующей турбины по id(GET)."""
    turbine_id = 999
    response = await async_client.get(f"/turbines/{turbine_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}









