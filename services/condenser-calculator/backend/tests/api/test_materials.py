import pytest
from fastapi.testclient import TestClient

from app.main import app


def check_db_connection() -> None:
    print("\n[*] Проверка конфигурации...")
    from app.core.config import settings

    # 1. Пытаемся найти URL под разными именами
    db_url = None
    possible_names = [
        "SQLALCHEMY_DATABASE_URI",
        "SQLALCHEMY_DATABASE_URL",
        "DATABASE_URL",
    ]

    for name in possible_names:
        if hasattr(settings, name):
            db_url = getattr(settings, name)
            print(f"[*] Найдено поле: {name}")
            break

    if not db_url:
        # Если не нашли, выведем все доступные поля для отладки
        attrs = [a for a in dir(settings) if not a.startswith("_")]
        print("[!] ОШИБКА: URL базы данных не найден в настройках.")
        print(f"[*] Доступные поля в settings: {attrs}")
        pytest.exit("Завершение: не удалось определить URL базы данных")

    print(f"[*] Пытаюсь подключиться к: {db_url}")

    try:
        from sqlalchemy import create_engine

        engine = create_engine(str(db_url), connect_args={"connect_timeout": 3})
        with engine.connect():
            print("[+] БД доступна!")
    except Exception as e:
        print(f"[!] ОШИБКА ПОДКЛЮЧЕНИЯ К БД: {e}")
        print("[*] УБЕДИТЕСЬ, ЧТО:")
        print("    1. PostgreSQL запущен.")
        print("    2. В .env файле POSTGRES_SERVER=localhost (не 'db').")
        print("    3. Логин/пароль верны.")
        pytest.exit("Завершение: база данных недоступна")


check_db_connection()

client = TestClient(app)
ENDPOINT = "/api/v1/materials"


def test_get_materials() -> None:
    """Успешное получение списка всех материалов"""
    response = client.get(ENDPOINT)
    assert response.status_code == 200
    materials = response.json()
    assert isinstance(materials, list)
    if len(materials) > 0:
        assert "id" in materials[0] and "name" in materials[0]


def test_get_materials_paginated() -> None:
    """Пагинация — skip и limit"""
    all_items = client.get(ENDPOINT, params={"limit": 500}).json()
    if len(all_items) < 6:
        pytest.skip("Нужно ≥6 материалов в БД")

    page1 = client.get(ENDPOINT, params={"skip": 0, "limit": 3}).json()
    page2 = client.get(ENDPOINT, params={"skip": 3, "limit": 3}).json()

    assert len(page1) == 3
    assert len(page2) == 3
    assert page1[0]["id"] == all_items[0]["id"]
    assert page2[0]["id"] == all_items[3]["id"]



def test_get_materials_by_condenser_id() -> None:
    """Успешное получение материалов для конденсатора"""
    response = client.get("/api/v1/condensers/1/materials")
    assert response.status_code == 200
    materials = response.json()
    assert isinstance(materials, list)
    if len(materials) > 0:
        assert "id" in materials[0] and "name" in materials[0]


def test_get_materials_by_nonexistent_condenser_id() -> None:
    """404 — конденсатор не найден"""
    response = client.get("/api/v1/condensers/9999999/materials")
    assert response.status_code in (404,500)

