from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app import crud, models, schemas


# ===== Хелперы для создания тестовых данных =====

def create_test_turbine(db: Session, turbine_name: str = "Test Turbine"):
    turbine = models.Turbine(name=turbine_name)
    db.add(turbine)
    db.commit()
    db.refresh(turbine)
    return turbine


def create_test_valve(db: Session, valve_name: str = "VD-001", turbine_id: int | None = None):
    valve = models.Valve(
        name=valve_name,
        type="Type A",
        diameter=10.0,
        clearance=1.0,
        count_parts=5,
        len_part1=1.0,
        len_part2=1.0,
        len_part3=1.0,
        len_part4=1.0,
        len_part5=1.0,
        round_radius=0.5,
        turbine_id=turbine_id,
    )
    db.add(valve)
    db.commit()
    db.refresh(valve)
    return valve


def create_test_calculation_result(
    db: Session,
    valve_name: str,
    input_data: dict,
    output_data: dict,
    valve_id: int,
):
    calculation_result = models.CalculationResultDB(
        stock_name=valve_name,
        turbine_name="Test Turbine",
        calc_timestamp=datetime.now(timezone.utc),
        input_data=input_data,
        output_data=output_data,
        valve_id=valve_id,
    )
    db.add(calculation_result)
    db.commit()
    db.refresh(calculation_result)
    return calculation_result


# ===== Тесты get_valves_by_turbine =====

def test_get_valves_by_turbine(db_session):
    turbine = create_test_turbine(db_session)
    create_test_valve(db_session, valve_name="VD-001", turbine_id=turbine.id)
    create_test_valve(db_session, valve_name="VD-002", turbine_id=turbine.id)

    result = crud.get_valves_by_turbine(db_session, turbine_name="Test Turbine")

    assert result is not None
    assert result.count == 2
    assert len(result.valves) == 2
    assert result.valves[0].name in ["VD-001", "VD-002"]
    assert result.valves[1].name in ["VD-001", "VD-002"]


def test_get_valves_by_turbine_no_turbine(db_session):
    result = crud.get_valves_by_turbine(db_session, turbine_name="Nonexistent Turbine")

    assert result is None


# ===== Тесты get_valve_by_drawing =====

def test_get_valve_by_drawing(db_session):
    turbine = create_test_turbine(db_session)
    create_test_valve(db_session, valve_name="VD-003", turbine_id=turbine.id)

    result = crud.get_valve_by_drawing(db_session, valve_drawing="VD-003")

    assert result is not None
    assert result.name == "VD-003"


def test_get_valve_by_drawing_not_found(db_session):
    result = crud.get_valve_by_drawing(db_session, valve_drawing="Nonexistent Drawing")

    assert result is None


# ===== Тесты get_valve_by_id =====

def test_get_valve_by_id(db_session):
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_name="VD-004", turbine_id=turbine.id)

    result = crud.get_valve_by_id(db_session, valve_id=valve.id)

    assert result is not None
    assert result.id == valve.id
    assert result.name == "VD-004"


def test_get_valve_by_id_not_found(db_session):
    result = crud.get_valve_by_id(db_session, valve_id=999)

    assert result is None


# ===== Тесты create_calculation_result =====

def test_create_calculation_result(db_session):
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_name="VD-005", turbine_id=turbine.id)

    parameters = schemas.CalculationParams(
        turbine_name="Test Turbine",
        valve_drawing=valve.name,
        valve_id=valve.id,
        temperature_start=100.0,
        t_air=300.0,
        count_valves=2,
        p_ejector=[1.0, 2.0],
        p_values=[3.0, 4.0],
    )

    results = schemas.CalculationResult(
        Gi=[1.1, 2.2],
        Pi_in=[3.3, 4.4],
        Ti=[5.5, 6.6],
        Hi=[7.7, 8.8],
        deaerator_props=[9.9, 10.1, 11.11, 12.12],
        ejector_props=[{"g": 13.13, "t": 14.14, "h": 15.15, "p": 16.16}],
    )

    db_result = crud.create_calculation_result(
        db=db_session,
        parameters=parameters,
        results=results,
        valve_id=valve.id,
    )

    assert db_result.id is not None
    assert db_result.stock_name == "VD-005"
    assert isinstance(db_result.calc_timestamp, datetime)


# ===== Тесты get_results_by_valve_drawing =====

def test_get_results_by_valve_drawing(db_session):
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_name="VD-006", turbine_id=turbine.id)

    parameters1 = schemas.CalculationParams(
        turbine_name="Test Turbine",
        valve_drawing=valve.name,
        valve_id=valve.id,
        temperature_start=100.0,
        t_air=300.0,
        count_valves=2,
        p_ejector=[1.0, 2.0],
        p_values=[3.0, 4.0],
    )

    results1 = schemas.CalculationResult(
        Gi=[1.1, 2.2],
        Pi_in=[3.3, 4.4],
        Ti=[5.5, 6.6],
        Hi=[7.7, 8.8],
        deaerator_props=[9.9, 10.1, 11.11, 12.12],
        ejector_props=[{"g": 13.13, "t": 14.14, "h": 15.15, "p": 16.16}],
    )

    create_test_calculation_result(
        db_session, "VD-006",
        parameters1.model_dump(), results1.model_dump(),
        valve_id=valve.id,
    )

    parameters2 = schemas.CalculationParams(
        turbine_name="Test Turbine",
        valve_drawing=valve.name,
        valve_id=valve.id,
        temperature_start=200.0,
        t_air=400.0,
        count_valves=3,
        p_ejector=[2.0, 3.0],
        p_values=[4.0, 5.0],
    )

    results2 = schemas.CalculationResult(
        Gi=[2.2, 3.3],
        Pi_in=[4.4, 5.5],
        Ti=[6.6, 7.7],
        Hi=[8.8, 9.9],
        deaerator_props=[10.10, 11.11, 12.12, 13.13],
        ejector_props=[{"g": 14.14, "t": 15.15, "h": 16.16, "p": 17.17}],
    )

    create_test_calculation_result(
        db_session, "VD-006",
        parameters2.model_dump(), results2.model_dump(),
        valve_id=valve.id,
    )

    results = crud.get_results_by_valve_drawing(db_session, valve_drawing="VD-006")

    assert len(results) == 2
    assert results[0].stock_name == "VD-006"
    assert results[1].stock_name == "VD-006"


def test_get_results_by_valve_drawing_not_found(db_session):
    results = crud.get_results_by_valve_drawing(db_session, valve_drawing="Nonexistent Drawing")

    assert results == []


def test_create_calculation_result_invalid_data(db_session):
    """Pydantic должен отклонить невалидные данные при создании схемы."""
    turbine = create_test_turbine(db_session)
    create_test_valve(db_session, valve_name="VD-007", turbine_id=turbine.id)

    with pytest.raises(ValueError):
        schemas.CalculationParams(
            turbine_name="Test Turbine",
            valve_drawing="VD-007",
            valve_id=1,
            temperature_start="invalid",  # Должно быть float
            t_air=300.0,
            count_valves=2,
            p_ejector=[1.0, 2.0],
            p_values=[3.0, 4.0],
        )
