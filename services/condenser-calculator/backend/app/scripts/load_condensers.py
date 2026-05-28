import pandas as pd
import numpy as np
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.condenser import Condenser
from app.models.material import Material

logger = logging.getLogger(__name__)

def safe_float(val):
    """Безопасное преобразование значения в float. Если пусто или '-', возвращает None."""
    if pd.isna(val) or val == '-':
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def safe_int(val):
    """Безопасное преобразование значения в int."""
    f_val = safe_float(val)
    return int(f_val) if f_val is not None else None

def load_condensers(db: Session, excel_path: str = "default.xlsx"):
    """
    Парсит Excel-файл и загружает конденсаторы в базу данных.
    """
    path = Path(excel_path)
    if not path.exists():
        logger.error(f"Файл {excel_path} не найден!")
        return

    logger.info(f"Читаем файл {excel_path}...")
    df = pd.read_excel(path)
    df.replace('-', np.nan, inplace=True)
    df.replace('', np.nan, inplace=True)

    added_count = 0
    # Кэш имен для защиты от дубликатов внутри одного файла
    processed_names = set()

    for index, row in df.iterrows():
        condenser_name = str(row.get('Тип_конденсатора', '')).strip()
        if not condenser_name or condenser_name == 'nan':
            continue  # Пропускаем пустые строки

        # 1. Проверка на дубликаты в памяти скрипта
        if condenser_name in processed_names:
            logger.info(f"Конденсатор {condenser_name} уже обработан. Пропускаем дубликат.")
            continue
            
        # 2. Проверка на дубликаты в базе данных
        existing = db.query(Condenser).filter(Condenser.name_condenser == condenser_name).first()
        if existing:
            logger.info(f"Конденсатор {condenser_name} уже существует в БД. Пропускаем.")
            continue

        processed_names.add(condenser_name)

        # --- Новая логика обработки Banyak-ко-Многим материалов ---
        raw_material_string = str(row.get('Материал_охлаждающих_труб', '')).strip()
        matched_materials = []
        
        if raw_material_string and raw_material_string != 'nan':
            # Разбиваем строку по слэшу на список
            material_names = [name.strip() for name in raw_material_string.split('/') if name.strip()]
            
            for mat_name in material_names:
                material_obj = db.query(Material).filter(Material.name.ilike(f"%{mat_name}%")).first()
                if material_obj:
                    matched_materials.append(material_obj)
                else:
                    logger.warning(f"Компонент материала '{mat_name}' не найден в БД")
        
        if not matched_materials:
            default_material = db.query(Material).first()
            if default_material:
                matched_materials.append(default_material)
                logger.warning(f"Для {condenser_name} не найдено совпадений. Привязан default материал.")

        # --- Расчет геометрии ---
        od = safe_float(row.get('Наружный_диаметр_труб_мм'))
        wt = safe_float(row.get('Толщина_стенки_труб_мм'))
        
        internal_diam = 0.0
        if od is not None and wt is not None:
            internal_diam = od - (2 * wt)

        # --- Формирование JSON с лимитами расходов воды ---
        water_limits = {
            "main_bundle": {
                "max": safe_float(row.get('Максимальный_расход_охлаждающей_воды_т/ч')),
                "min": safe_float(row.get('Минимальный_расход_охлаждающей_воды_т/ч'))
            },
            "total_max": safe_float(row.get('Максимальный_расход_охлаждающей_воды_через_основные_и_встроенные_пучки_т/ч'))
        }

        # --- Создание объекта ---
        new_condenser = Condenser(
            name_condenser=condenser_name,
            doc_num_thermo_calc=str(row.get('Теплогидравлический_расчет_конденсатора_(номер_документа)', '')),
            doc_num_assembly=str(row.get('Номера_используемых_чертежей', '')),
            
            # Геометрия
            diameter_internal=internal_diam,
            wall_thickness=wt or 0.0,
            
            # Внимание: material_id удален, используем список materials
            materials=matched_materials, 
            
            main_length=safe_float(row.get('Активная_длина_охлаждающих_труб_основного_пучка_мм')) or 0.0,
            main_count=safe_int(row.get('Количество_охлаждающих_труб_основного_пучка_шт')) or 0,
            builtin_length=safe_float(row.get('Активная_длина_охлаждающих_труб_встроенного_пучка_мм')),
            builtin_count=safe_int(row.get('Количество_охлаждающих_труб_встроенного_пучка_шт')),
            aircooler_count=safe_int(row.get('Общее_количество_труб_воздухоохладителя_шт')),
            
            # Дефолтные значения для обязательных полей
            passes_main=2, 
            passes_builtin=2,
            ejectors_count=1,
            mass_flow_steam_nom=100000.0,
            mass_flow_air=50.0,
            
            water_flow_limits=water_limits
        )

        db.add(new_condenser)
        added_count += 1

    try:
        db.commit()
        logger.info(f"Успешно добавлено конденсаторов: {added_count}")
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при сохранении в БД: {e}")