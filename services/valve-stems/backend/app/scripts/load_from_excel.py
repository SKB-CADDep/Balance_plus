import logging
import sys
import os
import pandas as pd
from pathlib import Path

sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine, Base
from app.models import Turbine, Valve

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пути для работы внутри Docker-контейнера
PROJECTS_FILE = Path("/app/Data.xlsx")
GEOMETRY_FILE = Path("/app/Data_1.xlsx")

def clean_value(val):
    if pd.isna(val): return None
    if isinstance(val, float) and val.is_integer(): return str(int(val))
    return str(val).strip()

def to_float(val, default=None):
    if pd.isna(val): return default
    if isinstance(val, str):
        val = val.replace(',', '.').strip()
        if not val: return default
    try: return float(val)
    except ValueError: return default

def extract_valves(cell_value):
    if pd.isna(cell_value) or str(cell_value).strip() == "": return []
    raw_str = str(cell_value).replace('\n', ',')
    return [v.strip() for v in raw_str.split(',') if v.strip()]

def init_db():
    if not PROJECTS_FILE.exists() or not GEOMETRY_FILE.exists():
        logger.error("Один из Excel файлов не найден!")
        return

    db = SessionLocal()
    
    try:
        logger.info("Пересоздание таблиц БД (переход на Many-to-Many)...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        # ---------------------------------------------------------
        # ФАЗА 1: Загрузка УНИКАЛЬНЫХ геометрий клапанов
        # ---------------------------------------------------------
        logger.info("Чтение геометрий из Data_1.xlsx...")
        df_geo = pd.read_excel(GEOMETRY_FILE)
        
        valve_cache = {} # Словарь { "Имя_Чертежа": Объект_Valve }
        
        for _, row in df_geo.iterrows():
            name = str(row.get('Чертеж_клапана')).strip()
            if not name or name == 'nan': continue
            
            # Если такой чертеж уже добавили, пропускаем дубль
            if name in valve_cache: continue
            
            valve = Valve(
                name=name,
                type=clean_value(row.get('Тип_клапана')),
                count_parts=to_float(row.get('Количество_участков')),
                diameter=to_float(row.get('Диаметр_штока_мм')),
                clearance=to_float(row.get('Расчетный_зазор_мм')),
                len_part1=to_float(row.get('Длина_участка_1_мм')),
                len_part2=to_float(row.get('Длина_участка_2_мм')),
                len_part3=to_float(row.get('Длина_участка_3_мм')),
                len_part4=to_float(row.get('Длина_участка_4_мм')),
                len_part5=to_float(row.get('Длина_участка_5_мм')),
                round_radius=to_float(row.get('Радиус_скругления_(размер_фаски)_мм'), default=2.0)
            )
            db.add(valve)
            valve_cache[name] = valve

        db.commit()
        logger.info(f"В справочник добавлено {len(valve_cache)} уникальных клапанов.")

        # ---------------------------------------------------------
        # ФАЗА 2: Загрузка ПРОЕКТОВ и создание связей
        # ---------------------------------------------------------
        logger.info("Чтение проектов из Data.xlsx...")
        df_proj = pd.read_excel(PROJECTS_FILE)
        count_turbines = 0

        for _, row in df_proj.iterrows():
            mark = clean_value(row.get('Марка турбины'))
            if not mark: continue

            turbine = Turbine(
                name=mark,
                station_name=clean_value(row.get('Наименование станции')),
                station_number=clean_value(row.get('Станц. №')),
                factory_number=clean_value(row.get('Зав№'))
            )
            
            # Собираем все имена клапанов для этой турбины
            all_valves_for_turbine = []
            all_valves_for_turbine.extend([(v, "Стопорный (СК)") for v in extract_valves(row.get('СК'))])
            all_valves_for_turbine.extend([(v, "Регулирующий (РК)") for v in extract_valves(row.get('РК'))])
            all_valves_for_turbine.extend([(v, "Стопорно-регулирующий (СРК)") for v in extract_valves(row.get('СРК'))])
            
            for v_name, v_type in all_valves_for_turbine:
                # Если клапан есть в базе — берем его. Если нет — создаем пустую геометрию на лету!
                if v_name in valve_cache:
                    valve_obj = valve_cache[v_name]
                else:
                    valve_obj = Valve(name=v_name, type=v_type)
                    db.add(valve_obj)
                    valve_cache[v_name] = valve_obj # Сохраняем в кэш
                
                # Магия SQLAlchemy: просто добавляем объект в список, связка Many-to-Many создастся сама!
                if valve_obj not in turbine.valves:
                    turbine.valves.append(valve_obj)

            db.add(turbine)
            count_turbines += 1

        db.commit()
        logger.info(f"Успешно загружено! Проектов: {count_turbines}. Всего уникальных клапанов в базе: {len(valve_cache)}")

    except Exception as e:
        logger.error(f"Ошибка при загрузке: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()