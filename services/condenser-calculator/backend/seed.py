"""
Главный скрипт для инициализации базы данных.
Запускать так: py seed.py
"""
import sys
import os
from pathlib import Path

# --- БРОНЕБОЙНЫЙ ФИКС (Хост + Порт) ---
if "POSTGRES_SERVER" not in os.environ:
    os.environ["POSTGRES_SERVER"] = "localhost"
if "DB_HOST" not in os.environ:
    os.environ["DB_HOST"] = "localhost"
if "POSTGRES_PORT" not in os.environ:
    os.environ["POSTGRES_PORT"] = "5255"
if "DB_PORT" not in os.environ:
    os.environ["DB_PORT"] = "5255"

# Принудительно добавляем текущую папку (backend) в пути Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, SessionLocal
from app.models.base import Base
# Обязательно импортируем модели, чтобы SQLAlchemy узнала о них до создания таблиц
from app.models.condenser import Condenser
from app.models.material import Material

# Импортируем ваши функции
from app.scripts.load_materials import load_materials
from app.scripts.load_condensers import load_condensers

def main():
    print(f"[*] Подключение к БД на {os.environ.get('POSTGRES_SERVER')}:{os.environ.get('POSTGRES_PORT')}...")
    print("[1/3] Создание таблиц в базе данных...")
    Base.metadata.create_all(bind=engine)
    print("[+] Таблицы готовы.")

    # Открываем сессию базы данных
    db = SessionLocal()
    try:
        print("\n[2/3] Загрузка материалов...")
        materials_dir = Path(__file__).parent.parent / "db" / "materials"
        if materials_dir.exists():
            load_materials(db, materials_dir)
            print("[+] Материалы загружены.")
        else:
            print(f"[-] Папка с материалами не найдена: {materials_dir}")

        print("\n[3/3] Загрузка конденсаторов...")
        load_condensers(db)
        print("[+] Конденсаторы загружены.")
        
    except Exception as e:
        print(f"[!] Произошла ошибка: {e}")
    finally:
        db.close()
        print("\n[*] Готово! Теперь можно запускать тесты.")

if __name__ == "__main__":
    main()