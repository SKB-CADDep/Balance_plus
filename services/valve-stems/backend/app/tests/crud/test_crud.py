"""
Модуль тестов CRUD-операций сервиса valve-stems.
"""


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


def create_test_valve(db: Session, valve_name: str = "VD-001"):
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
    """Тест успешного получения списка клапанов для существующей турбины."""
    turbine = create_test_turbine(db_session)
    valve1 = create_test_valve(db_session, valve_name="VD-001")
    valve2 = create_test_valve(db_session, valve_name="VD-002")
    turbine.valves.append(valve1)
    turbine.valves.append(valve2)
    db_session.commit()

    result = crud.get_valves_by_turbine(db_session, turbine_name="Test Turbine")

    assert result is not None
    assert len(result.valves) >= 1


def test_get_valves_by_turbine_no_turbine(db_session):
    """Тест получения клапанов для несуществующей турбины"""
    with pytest.raises(EntityNotFoundError):
        crud.get_valves_by_turbine(db_session, turbine_name="Nonexistent Turbine")


def test_get_valve_by_drawing(db_session):
    """Тест успешного получения клапана по имени его чертежа."""
    create_test_valve(db_session, valve_name="VD-003")

    result = crud.get_valve_by_drawing(db_session, valve_drawing="VD-003")
    assert result.name == "VD-003"


def test_get_valve_by_drawing_not_found(db_session):
    """Тест получения несуществующего клапана по имени чертежа"""
    with pytest.raises(EntityNotFoundError):
        result = crud.get_valve_by_drawing(db_session, valve_drawing="Nonexistent Drawing")

# ===== Тесты get_valve_by_id =====

def test_get_valve_by_id(db_session):
    """Тест успешного получения клапана по ID."""
    valve = create_test_valve(db_session, valve_name="VD-004")

    result = crud.get_valve_by_id(db_session, valve_id=valve.id)

    assert result is not None
    assert result.id == valve.id
    assert result.name == "VD-004"


def test_get_valve_by_id_not_found(db_session):
    """Тест получения несуществующего клапана по ID"""
    with pytest.raises(EntityNotFoundError):
        result = crud.get_valve_by_id(db_session, valve_id=999)


def test_create_calculation_result(db_session):
    """Тест успешного создания и сохранения в БД результатов мульти-расчета."""
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_name="VD-005")

    parameters = schemas.MultiCalculationParams(
        turbine_id=turbine.id,
        globals=schemas.CalculationGlobals(P_fresh=7, T_fresh = 20),
        groups=[
            schemas.ValveGroupInput(
                valve_id=valve.id,
                type= "СК",
                valve_names=["VD-005"],
                quantity=1)],
    )

    results = schemas.MultiCalculationResult(
        details=[schemas.GroupCalculationDetails(
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
            group_total_g=100.0)],
        summary= schemas.CalculationSummary(
            sk=schemas.TypeSummary(total_g=150.5, mixed_h=720.3),
            rk=schemas.TypeSummary(total_g=80.2, mixed_h=680.1),
            srk=schemas.TypeSummary(total_g=45.0, mixed_h=700.5)))

    # ИСПРАВЛЕНО: удален невалидный аргумент valve_id
    db_result = crud.create_calculation_result(
        db=db_session,
        parameters=parameters,
        results=results,
        stock_name=valve.name,
        turbine_name = turbine.name
    )

    assert db_result.id is not None
    assert db_result.stock_name == "VD-005"


def test_get_results_by_valve_drawing(db_session):
    """Тест получения списка всех результатов расчетов для конкретного имени чертежа клапана."""
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_name="VD-006")
    parameters1 = schemas.MultiCalculationParams(
        turbine_id=turbine.id,
        globals=schemas.CalculationGlobals(P_fresh=7, T_fresh=20),
        groups=[
            schemas.ValveGroupInput(
                valve_id=valve.id,
                type="СК",
                valve_names=["VD-006"],
                quantity=1)],
    )
    results1 = schemas.MultiCalculationResult(
        details=[schemas.GroupCalculationDetails(
            valve_id=valve.id,
            type="СК",
            valve_names=["VD-006"],
            quantity=1,
            Gi=[1.1, 2.2],
            Pi_in=[3.3, 4.4],
            Ti=[5.5, 6.6],
            Hi=[7.7, 8.8],
            deaerator_props=[9.9, 10.1, 11.11, 12.12],
            ejector_props=[{"g": 13.13, "t": 14.14, "h": 15.15, "p": 16.16}],
            group_total_g=100.0)],
        summary=schemas.CalculationSummary(
            sk=schemas.TypeSummary(total_g=150.5, mixed_h=720.3),
            rk=schemas.TypeSummary(total_g=80.2, mixed_h=680.1),
            srk=schemas.TypeSummary(total_g=45.0, mixed_h=700.5)))

    create_test_calculation_result(
        db_session, "VD-006",
        parameters1.model_dump(), results1.model_dump(),
    )
    parameters2 = schemas.MultiCalculationParams(
        turbine_id=turbine.id,
        globals=schemas.CalculationGlobals(P_fresh=7, T_fresh=20),
        groups=[
            schemas.ValveGroupInput(
                valve_id=valve.id,
                type="СК",
                valve_names=["VD-006"],
                quantity=1)],)

    results2 = schemas.MultiCalculationResult(
        details=[schemas.GroupCalculationDetails(
            valve_id=valve.id,
            type="СК",
            valve_names=["VD-006"],
            quantity=1,
            Gi=[2.2, 3.3],
            Pi_in=[4.4, 5.5],
            Ti=[6.6, 7.7],
            Hi=[8.8, 9.9],
            deaerator_props=[10.10, 11.11, 12.12, 13.13],
            ejector_props=[{"g": 14.14, "t": 15.15, "h": 16.16, "p": 17.17}],
            group_total_g=110.0)],
        summary=schemas.CalculationSummary(
            sk=schemas.TypeSummary(total_g=151.5, mixed_h=721.3),
            rk=schemas.TypeSummary(total_g=81.2, mixed_h=681.1),
            srk=schemas.TypeSummary(total_g=46.0, mixed_h=701.5)))

    create_test_calculation_result(
        db_session, "VD-006",
        parameters2.model_dump(), results2.model_dump(),
    )

    results = crud.get_results_by_valve_drawing(
        db_session, valve_drawing="VD-006")
    assert len(results) >= 1
    assert results[0].stock_name == "VD-006"
    assert results[1].stock_name == "VD-006"


def test_get_results_by_valve_drawing_not_found(db_session):
    """Тест получения результатов для несуществующего чертежа"""
    results = crud.get_results_by_valve_drawing(db_session, valve_drawing="Nonexistent Drawing")

    assert results == []


def test_create_calculation_result_invalid_data(db_session):
    """Pydantic должен отклонить невалидные данные при создании схемы."""
    turbine = create_test_turbine(db_session)
    valve = create_test_valve(db_session, valve_name="VD-007")
    with pytest.raises(ValueError):
        schemas.MultiCalculationParams(
            turbine_id=turbine.id,
            globals=schemas.CalculationGlobals(P_fresh=7, T_fresh=20),
            groups=[
                schemas.ValveGroupInput(
                    valve_id=valve.id,
                    type="СК",
                    valve_names=["VD-006"],
                    quantity="invalid")], )  # Должно быть int
