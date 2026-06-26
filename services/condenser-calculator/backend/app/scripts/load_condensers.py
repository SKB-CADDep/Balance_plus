"""Загружает базовые данные конденсаторов в PostgreSQL."""

from sqlalchemy.orm import Session

from app.models.condenser import Condenser


def load_condensers(db: Session) -> None:
    # Создаем базовый конденсатор для тестов (ID = 1)
    default_condenser = Condenser(
        id=1,
        name_condenser="80-КЦС-3",
        project_id="П-123",
        doc_num_thermo_calc="ТК-1",
        doc_num_assembly="СБ-1",
        doc_num_passport="ПС-1",
        diameter_internal=24.0,
        wall_thickness=1.0,
        material_id=1,  # Привязка к материалу, который загружается первым
        main_length=8950.0,
        main_count=8400,
        builtin_length=8950.0,
        builtin_count=1200,
        aircooler_count=450,
        passes_main=2,
        passes_builtin=2,
        ejectors_count=1,
        mass_flow_steam_nom=155000.0,
        mass_flow_air=40.0,
        water_flow_limits=[4000.0, 20000.0],
    )

    existing = db.query(Condenser).filter(Condenser.id == 1).first()
    if not existing:
        db.add(default_condenser)
        db.commit()
        print("[+] Конденсатор '80-КЦС-3' (ID=1) успешно добавлен в БД.")
    else:
        print("[*] Конденсатор с ID=1 уже существует.")
