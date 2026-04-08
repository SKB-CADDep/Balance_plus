import logging
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.material import Material
from app.models.condenser import Condenser

logger = logging.getLogger(__name__)


def seed_data(db: Session):
    # 1. Добавляем материалы
    materials = [
        {
            "id": 1,
            "name": "МНЖ5-1 (Медно-никелевый сплав)",
            "thermal_properties": [[20, 45.0], [100, 50.0]],
        },
        {
            "id": 2,
            "name": "Л-68 (Латунь)",
            "thermal_properties": [[20, 105.0], [100, 110.0]],
        },
        {
            "id": 3,
            "name": "Нержавеющая сталь 12Х18Н10Т",
            "thermal_properties": [[20, 15.0], [100, 16.0]],
        },
    ]

    for mat_data in materials:
        mat = db.query(Material).filter(Material.id == mat_data["id"]).first()
        if not mat:
            db.add(Material(**mat_data))
    db.commit()

    # 2. Добавляем 3 типа конденсаторов (DoR п.2)
    condensers = [
        {
            # Конденсатор 1: Большой двухходовой (Берман)
            "name_condenser": "КГ2-6200",
            "diameter_internal": 26.0,
            "wall_thickness": 1.0,
            "material_id": 1,
            "main_length": 9000.0,
            "main_count": 14500,
            "builtin_length": 9000.0,
            "builtin_count": 1200,
            "aircooler_count": 400,
            "passes_main": 2,
            "passes_builtin": 2,
            "ejectors_count": 3,
            "mass_flow_steam_nom": 500000.0,
            "mass_flow_air": 60.0,
            "water_flow_limits": {
                "main_bundle": {"min": 6000.0, "max": 12000.0},
                "builtin_bundle": {"min": 500.0, "max": 1500.0},
            },
        },
        {
            # Конденсатор 2: Метро-Виккерс (без встроенного пучка)
            "name_condenser": "800-КЦС-3",
            "diameter_internal": 24.0,
            "wall_thickness": 1.0,
            "material_id": 2,
            "main_length": 12000.0,
            "main_count": 18000,
            "builtin_length": None,
            "builtin_count": None,
            "aircooler_count": 600,
            "passes_main": 1,
            "passes_builtin": None,
            "ejectors_count": 2,
            "mass_flow_steam_nom": 800000.0,
            "mass_flow_air": 80.0,
            "water_flow_limits": {"main_bundle": {"min": 15000.0, "max": 25000.0}},
        },
        {
            # Конденсатор 3: Малый промышленный
            "name_condenser": "К-100-36",
            "diameter_internal": 22.0,
            "wall_thickness": 1.0,
            "material_id": 3,
            "main_length": 6000.0,
            "main_count": 5000,
            "builtin_length": 6000.0,
            "builtin_count": 400,
            "aircooler_count": 150,
            "passes_main": 2,
            "passes_builtin": 2,
            "ejectors_count": 1,
            "mass_flow_steam_nom": 100000.0,
            "mass_flow_air": 20.0,
            "water_flow_limits": {
                "main_bundle": {"min": 1000.0, "max": 3000.0},
                "builtin_bundle": {"min": 100.0, "max": 400.0},
            },
        },
    ]

    for cond_data in condensers:
        cond = (
            db.query(Condenser)
            .filter(Condenser.name_condenser == cond_data["name_condenser"])
            .first()
        )
        if not cond:
            db.add(Condenser(**cond_data))

    db.commit()
    print("✅ Тестовые данные (Материалы и 3 Конденсатора) успешно загружены в БД.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
