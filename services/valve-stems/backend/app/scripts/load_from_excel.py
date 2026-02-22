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

# Путь для работы внутри Docker-контейнера
EXCEL_PATH = Path("/app/Data.xlsx")

def clean_value(val):
    if pd.isna(val):
        return None
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    return str(val).strip()

def extract_valves(cell_value):
    if pd.isna(cell_value) or str(cell_value).strip() == "":
        return []
    raw_str = str(cell_value).replace('\n', ',')
    valves = [v.strip() for v in raw_str.split(',') if v.strip()]
    return valves

def init_db_from_excel():
    if not EXCEL_PATH.exists():
        logger.error(f"Файл {EXCEL_PATH} не найден!")
        return

    logger.info("Чтение Excel файла...")
    df = pd.read_excel(EXCEL_PATH)

    db = SessionLocal()
    
    try:
        logger.info("Пересоздание таблиц БД...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        count_turbines = 0
        count_valves = 0

        for index, row in df.iterrows():
            factory_num = clean_value(row.get('Зав№'))
            mark = clean_value(row.get('Марка турбины'))
            station = clean_value(row.get('Наименование станции'))
            st_num = clean_value(row.get('Станц. №'))

            if not mark:
                continue

            turbine = Turbine(
                name=mark,
                station_name=station,
                station_number=st_num,
                factory_number=factory_num
            )
            db.add(turbine)
            db.flush()
            count_turbines += 1

            sk_list = extract_valves(row.get('СК'))
            rk_list = extract_valves(row.get('РК'))
            srk_list = extract_valves(row.get('СРК'))

            def add_valves(v_list, v_type):
                nonlocal count_valves
                for v_name in v_list:
                    valve = Valve(
                        name=v_name,
                        type=v_type,
                        turbine_id=turbine.id,
                        count_parts=3
                    )
                    db.add(valve)
                    count_valves += 1

            add_valves(sk_list, "Стопорный (СК)")
            add_valves(rk_list, "Регулирующий (РК)")
            add_valves(srk_list, "Стопорно-регулирующий (СРК)")

        db.commit()
        logger.info(f"Успешно загружено! Проектов: {count_turbines}, Клапанов: {count_valves}")

    except Exception as e:
        logger.error(f"Ошибка при загрузке: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db_from_excel()