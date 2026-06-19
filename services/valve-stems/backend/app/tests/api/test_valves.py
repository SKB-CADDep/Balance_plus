"""
Тесты для valves check endpoints.
"""

import pytest

"""
Позитивные сценарии.
"""
@pytest.mark.asyncio
async def test_create_valve(async_client, db_session):
    """Тест проверки создания сущностей(POST)."""
    payload = {"name": "Test Valve"}
    response = await async_client.post("/valves/", json=payload)
    data = response.json()
    assert response.status_code == 201
    assert data["name"] == payload["name"]


@pytest.mark.asyncio
async def test_get_valves(async_client, db_session):
    """Тест проверки получения списка клапанов(GET)."""
    valve1 = create_test_valve(db_session)
    valve2 = create_test_valve(db_session)
    valve3 = create_test_valve(db_session)
    valve4 = create_test_valve(db_session)
    response = await async_client.get("/valves")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 4


@pytest.mark.asyncio
async def test_read_valve_by_id(async_client, db_session):
    """Тест проверки получения клапана по id(GET)."""
    valve = create_test_valve(db_session)
    response = await async_client.get(f"/valves/{valve.id}")
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == valve.id
    assert data["name"] == valve.name


@pytest.mark.asyncio
async def test_get_turbine_by_valve_name(async_client, db_session):
    """Тест проверки получения турбины по имени клапана(GET)."""
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, "Test Valve", turbine.id)
    response = await async_client.get(f"/{valve.name}/turbine")
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == turbine.id
    assert data["name"] == turbine.name

@pytest.mark.asyncio
async def test_create_valve_duplicate_name(async_client, db_session):
    """Тест проверки создания клапана с дублирующимся именем (POST)."""
    valve = create_test_valve(db_session, "Test Valve")
    payload = {"name": "Test Valve"}
    response = await async_client.post("/valves", json=payload)
    data = response.json()
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_get_turbine_by_nonexistent_valve_name(async_client, db_session):
    """Тест проверки получения турбины по несуществующему имени клапана(GET)."""
    turbine = create_test_turbine(db_session)
    valve_name = "Fake Valve"
    response = await async_client.get(f"valves/{valve_name}/turbine")
    data = response.json()
    assert response.status_code == 404