"""
Тесты для calculation check endpoints.
"""

from app import schemas
from app.tests.crud.test_crud import (
    create_test_calculation_result,
    create_test_turbine,
    create_test_valve,
)


async def test_get_calculation_results(async_client, db_session):
    """Тест проверки получения списка результатов(GET)."""
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_name="VD-005")
    parameters = schemas.MultiCalculationParams(
        turbine_id=turbine.id,
        globals=schemas.CalculationGlobals(P_fresh=7, T_fresh=20),
        groups=[
            schemas.ValveGroupInput(
                valve_id=valve.id,
                type="СК",
                valve_names=["VD-005"],
                quantity=1,
            )
        ],
    )
    results = schemas.MultiCalculationResult(
        details=[
            schemas.GroupCalculationDetails(
                valve_id=valve.id,
                type="СК",
                valve_names=["VD-005"],
                quantity=1,
                Gi=[1.1, 2.2],
                Pi_in=[3.3, 4.4],
                Ti=[5.5, 6.6],
                Hi=[7.7, 8.8],
                deaerator_props=[9.9, 10.1, 11.11, 12.12],
                ejector_props=[{"g": 13.13, "t": 14.14, "h": 15.15, "p": 16.16}],
                group_total_g=100.0,
            )
        ],
        summary=schemas.CalculationSummary(
            sk=schemas.TypeSummary(total_g=150.5, mixed_h=720.3),
            rk=schemas.TypeSummary(total_g=80.2, mixed_h=680.1),
            srk=schemas.TypeSummary(total_g=45.0, mixed_h=700.5),
        ),
    )

    create_test_calculation_result(
        db_session, valve.name, parameters.model_dump(), results.model_dump()
    )
    response = await async_client.get(f"/api/v1/valves/{valve.name}/results/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["stock_name"] == valve.name
    assert item["input_data"]["turbine_id"] == turbine.id
    assert item["input_data"]["globals"]["P_fresh"] == parameters.globals.P_fresh
    assert item["output_data"]["summary"]["sk"]["total_g"] == results.summary.sk.total_g
    assert item["output_data"]["details"][0]["Gi"] == results.details[0].Gi


async def test_delete_calculation_result(async_client, db_session):
    """Тест проверки удаления результата по id(DELETE)."""
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_name="VD-005")
    parameters = schemas.MultiCalculationParams(
        turbine_id=turbine.id,
        globals=schemas.CalculationGlobals(P_fresh=7, T_fresh=20),
        groups=[
            schemas.ValveGroupInput(
                valve_id=valve.id,
                type="СК",
                valve_names=["VD-005"],
                quantity=1,
            )
        ],
    )
    results = schemas.MultiCalculationResult(
        details=[
            schemas.GroupCalculationDetails(
                valve_id=valve.id,
                type="СК",
                valve_names=["VD-005"],
                quantity=1,
                Gi=[1.1, 2.2],
                Pi_in=[3.3, 4.4],
                Ti=[5.5, 6.6],
                Hi=[7.7, 8.8],
                deaerator_props=[9.9, 10.1, 11.11, 12.12],
                ejector_props=[{"g": 13.13, "t": 14.14, "h": 15.15, "p": 16.16}],
                group_total_g=100.0,
            )
        ],
        summary=schemas.CalculationSummary(
            sk=schemas.TypeSummary(total_g=150.5, mixed_h=720.3),
            rk=schemas.TypeSummary(total_g=80.2, mixed_h=680.1),
            srk=schemas.TypeSummary(total_g=45.0, mixed_h=700.5),
        ),
    )

    input_data = parameters.model_dump()
    output_data = results.model_dump()
    result = create_test_calculation_result(db_session, valve.name, input_data, output_data)

    response = await async_client.delete(f"/api/v1/{result.id}")
    assert response.status_code == 204
    assert response.content == b""


async def test_calculate_with_full_valve_types(async_client, db_session):
    """Тест выполнения расчета с полными наименованиями типов клапанов ('Стопорный', 'Регулирующий')."""
    turbine = create_test_turbine(db_session)
    valve1 = create_test_valve(db_session, valve_name="VD-006")
    valve2 = create_test_valve(db_session, valve_name="VD-007")

    payload = {
        "turbine_id": turbine.id,
        "globals": {
            "P_fresh": 130.0,
            "T_fresh": 540.0,
            "P_air": 1.033,
            "T_air": 27.0,
            "P_lst_leak_off": 0.97,
        },
        "groups": [
            {
                "valve_id": valve1.id,
                "type": "Стопорный",
                "valve_names": ["VD-006"],
                "quantity": 1,
                "p_leak_offs": [30.0, 10.0, 2.0],
            },
            {
                "valve_id": valve2.id,
                "type": "Регулирующий",
                "valve_names": ["VD-007"],
                "quantity": 1,
                "p_leak_offs": [30.0, 10.0, 2.0],
            },
        ],
    }

    response = await async_client.post("/api/v1/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "details" in data
    assert len(data["details"]) == 2
    assert data["details"][0]["type"] == "Стопорный"
    assert data["details"][1]["type"] == "Регулирующий"
    assert "summary" in data
    assert data["summary"]["sk"]["total_g"] > 0
    assert data["summary"]["rk"]["total_g"] > 0

