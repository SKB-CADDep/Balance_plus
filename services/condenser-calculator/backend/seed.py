"""
Главный скрипт для инициализации базы данных.
Запускать так: py seed.py
"""
import sys
import os
from pathlib import Path

# --- БРОНЕБОЙНЫЙ ФИКС (Хост + Порт) ---
os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["DB_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5255"  # <-- Указываем правильный порт!
os.environ["DB_PORT"] = "5255"        # На всякий случай

# Принудительно добавляем текущую папку (backend) в пути Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, SessionLocal
from app.models.base import Base
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
        BASE_DIR = Path(__file__).resolve().parent
        
        print("\n[2/3] Загрузка материалов...")
        # Теперь путь будет backend/data/materials
        materials_dir = BASE_DIR / "data" / "materials" 
        
        if materials_dir.exists() and any(materials_dir.iterdir()):
            load_materials(db, materials_dir)
            print("[+] Материалы загружены.")
        else:
            print(f"[-] Папка с материалами не найдена или пуста: {materials_dir}")

        print("\n[3/3] Загрузка конденсаторов...")
        # Теперь путь будет backend/data/default.xlsx
        excel_path = BASE_DIR / "data" / "default.xlsx"
        
        if excel_path.exists():
            load_condensers(db, str(excel_path))
            print("[+] Конденсаторы загружены.")
        else:
            print(f"[-] Файл Excel не найден по пути: {excel_path}")
        
    except Exception as e:
        print(f"[!] Произошла ошибка: {e}")
    finally:
        db.close()
        print("\n[*] Готово! Теперь можно запускать тесты.")

if __name__ == "__main__":
    main()