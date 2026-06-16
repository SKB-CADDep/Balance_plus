"""
Скрипт начальной загрузки справочника материалов (Seed Data).

Читает директорию с JSON-файлами физико-химических свойств материалов 
трубных пучков (теплопроводность, плотность и т.д.) и загружает их 
в базу данных. Обеспечивает идемпотентность: скрипт можно запускать 
многократно, дубликаты будут проигнорированы.
"""

import json
import logging
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.material import Material

logger = logging.getLogger(__name__)


def load_materials(db: Session, materials_dir: Path) -> None:
    """
    Читает JSON-файлы материалов из указанной директории и загружает их в БД.
    Пропускает материалы, если они уже существуют (по имени).
    
    Args:
        db (Session): Активная сессия базы данных.
        materials_dir (Path): Путь к папке, содержащей эталонные .json файлы.
    """
    if not materials_dir.exists():
        logger.error(f"Папка с материалами не найдена: {materials_dir}")
        return

    logger.info(f"Сканируем папку {materials_dir} на наличие JSON-файлов...")
    added_count = 0

    for json_file in materials_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Достаем имя по реальной структуре JSON
            material_name = data.get("metadata", {}).get("name_material_standard")
            if not material_name:
                logger.warning(f"Файл {json_file.name} не содержит 'name_material_standard'. Пропускаем.")
                continue

            # 1. Защита от дубликатов (SQLAlchemy 2.0 style)
            stmt = select(Material).where(Material.name == material_name)
            existing = db.scalar(stmt)
            
            if existing:
                logger.info(f"Материал '{material_name}' уже есть в БД. Пропускаем.")
                continue

            # 2. Достаем UUID
            mat_uuid = data.get("material_id", f"generated-{material_name}")
            
            # 3. Достаем массив точек [[t1, λ1], [t2, λ2]]
            thermal_points = (
                data.get("physical_properties", {})
                .get("coefficient_thermal_conductivity", {})
                .get("temperature_value_pairs", [])
            )
            
            # 4. Создаем объект материала
            new_material = Material(
                material_uuid=mat_uuid,
                name=material_name,
                thermal_conductivity_points=thermal_points,
                full_properties=data  # Закидываем весь JSON целиком для будущих расчетов
            )
            
            db.add(new_material)
            added_count += 1

        except json.JSONDecodeError:
            logger.error(f"Ошибка синтаксиса JSON в файле {json_file.name}")
        except Exception as e:
            logger.error(f"Ошибка при обработке {json_file.name}: {e}")

    # Фиксируем изменения в базе данных
    try:
        if added_count > 0:
            db.commit()
            logger.info(f"[+] Успешно загружено новых материалов: {added_count}")
        else:
            db.rollback()
            logger.info("[*] Новых материалов для загрузки не найдено (все уже в базе).")
    except Exception as e:
        db.rollback()
        logger.error(f"[!] Ошибка при сохранении материалов в БД: {e}")
        