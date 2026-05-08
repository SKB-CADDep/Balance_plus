from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.core.exceptions import EntityNotFoundError

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
        type="СК",
        diameter=10.0,
        clearance=1.0,
        count_parts=5,
        len_part1=1.0,
        len_part2=1.0,
        len_part3=1.0,
        len_part4=1.0,
        len_part5=1.0,
        round_radius=0.5,
    )
    if turbine_id:
        turbine = db.get(models.Turbine, turbine_id)
        if turbine:
            valve.turbines.append(turbine)
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
    # Восстанавливаем хелпер: в модели CalculationResultDB нет поля valve_id
    calculation_result = models.CalculationResultDB(
        stock_name=valve_name,
        turbine_name="Test Turbine",
        calc_timestamp=datetime.now(timezone.utc),
        input_data=input_data,
        output_data=output_data,
    )
    db.add(calculation_result)
    db.commit()
    db.refresh(calculation_result)
    return calculation_result

# ===== Тесты CRUD =====


def test_get_valves_by_turbine(db_session):
    turbine = create_test_turbine(db_session)
    create_test_valve(db_session, valve_name="VD-001", turbine_id=turbine.id)
    result = crud.get_valves_by_turbine(
        db_session, turbine_name="Test Turbine")
    assert result is not None
    assert len(result.valves) >= 1


def test_get_valves_by_turbine_no_turbine(db_session):
    with pytest.raises(EntityNotFoundError):
        crud.get_valves_by_turbine(db_session, turbine_name="Nonexistent")


def test_get_valve_by_drawing(db_session):
    create_test_valve(db_session, valve_name="VD-003")
    result = crud.get_valve_by_drawing(db_session, valve_drawing="VD-003")
    assert result.name == "VD-003"


def test_get_valve_by_id_not_found(db_session):
    with pytest.raises(EntityNotFoundError):
        crud.get_valve_by_id(db_session, valve_id=999)


def test_create_calculation_result(db_session):
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(
        db_session, valve_name="VD-005", turbine_id=turbine.id)

    parameters = schemas.CalculationGlobals(
        P_fresh=240.0,
        T_fresh=540.0,
        P_air=1.033
    )

    results = schemas.GroupCalculationDetails(
        valve_id=valve.id,
        type="СК",
        valve_names=[valve.name],
        quantity=1,
        Gi=[1.1, 2.2],
        Pi_in=[3.3, 4.4],
        Ti=[5.5, 6.6],
        Hi=[7.7, 8.8],
        deaerator_props=[9.9, 10.1],
        ejector_props=[{"g": 13.13, "p": 16.16}],
        group_total_g=3.3
    )

    # ИСПРАВЛЕНО: удален невалидный аргумент valve_id
    db_result = crud.create_calculation_result(
        db=db_session,
        parameters=parameters,
        results=results,
        stock_name=valve.name,    # Добавили этот аргумент
        turbine_name=turbine.name  # И этот аргумент
    )

    assert db_result.id is not None
    assert db_result.stock_name == "VD-005"


def test_get_results_by_valve_drawing(db_session):
    # Теперь этот тест пройдет, так как хелпер create_test_calculation_result исправлен
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(
        db_session, valve_name="VD-006", turbine_id=turbine.id)

    create_test_calculation_result(
        db_session, "VD-006",
        {"input": "data"}, {"output": "data"},
        valve_id=valve.id,
    )

    results = crud.get_results_by_valve_drawing(
        db_session, valve_drawing="VD-006")
    assert len(results) >= 1
    assert results[0].stock_name == "VD-006"


def test_create_calculation_result_invalid_data(db_session):
    """Проверка валидации Pydantic на новых схемах."""
    with pytest.raises(ValueError):
        # В CalculationGlobals P_fresh должно быть > 0
        schemas.CalculationGlobals(
            P_fresh=-10.0,
            T_fresh=540.0
        )
