import logging

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.condenser import Condenser
from app.models.material import Material

logger = logging.getLogger(__name__)


def seed_data(db: Session) -> None:
    # 1. Добавляем материалы
    materials = [
        {
            "id": 1,
            "material_uuid": "858dc196-6712-4dbb-bfdd-201c8ca5c65c",
            "name": "МНЖ5-1 (Медно-никелевый сплав)",
            "thermal_conductivity_points": [[20, 45.0], [100, 50.0]],
        },
        {
            "id": 2,
            "material_uuid": "fb772921-6fdf-4122-b25b-5fc40e74f836",
            "name": "Л-68 (Латунь)",
            "thermal_conductivity_points": [[20, 105.0], [100, 110.0]],
        },
        {
            "id": 3,
            "material_uuid": "d4a89993-4903-4558-8671-50e50882e99d",
            "name": "Нержавеющая сталь 12Х18Н10Т",
            "thermal_conductivity_points": [[20, 15.0], [100, 16.0]],
        },
    ]

    for mat_data in materials:
        db.merge(Material(**mat_data))
    db.commit()

    # 2. Добавляем 3 типа конденсаторов (DoR п.2)
    condensers = [
        {
            # Конденсатор 1: Большой двухходовой (Берман)
            "name_condenser": "КГ2-6200",
            "project_id": "proj-6200-a",
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
            "project_id": "proj-800k",
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
            "project_id": "proj-k100",
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
        db.merge(Condenser(**cond_data))

    db.commit()
    print("✅ Тестовые данные (Материалы и 3 Конденсатора) успешно загружены (merge) в БД.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
