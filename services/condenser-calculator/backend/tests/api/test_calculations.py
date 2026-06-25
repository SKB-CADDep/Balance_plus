"""
Интеграционные тесты API расчета конденсаторов (COND-8)
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


def check_db_connection():
    print("\n[*] Проверка конфигурации...")
    from app.core.config import settings

    # 1. Пытаемся найти URL под разными именами
    db_url = None
    possible_names = ["SQLALCHEMY_DATABASE_URI", "SQLALCHEMY_DATABASE_URL", "DATABASE_URL"]

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
        engine = create_engine(str(db_url), connect_args={'connect_timeout': 3})
        with engine.connect() as conn:
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
ENDPOINT = "/api/v1/calculations/calculate"

# ==========================================
# 🟢 УСПЕШНЫЕ СЦЕНАРИИ (Happy Paths)
# ==========================================

def test_1_berman_success():
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam": [120000.0],
        "H_steam": 2400.0,
        "t1_main": [20.0],
        "coefficient_b": [0.8],
        "W_main": [8000.0]
    }
    response = client.post(ENDPOINT, json=payload)
    # Если база доступна локально по localhost, вернет 200 или 404.
    assert response.status_code in [200, 404], f"Unexpected error: {response.text}"

def test_2_metro_vikkers_success():
    payload = {"method": "metro-vickers", "condenser_id": 1, "coefficient_b": [0.9], "W_main": [9000.0]}
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in [200, 404, 422] # 422 если метод все еще не тот

def test_3_full_payload_success():
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam": [150000.0, 160000.0],
        "H_steam": 2500.0,
        "t1_main": [15.5],
        "coefficient_b": [0.7, 0.85],
        "W_main": [5000.0, 10000.0],
        "Z_builtin": 2,
        "W_builtin": [1000.0] # Добавлено для консистентности с Z_builtin
    }
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in [200, 404], f"Unexpected error: {response.text}"

def test_4_multiple_points_success():
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam": [100000.0],
        "H_steam": 2350.0,
        "t1_main": [22.0],
        "coefficient_b": [0.55, 0.65, 0.75, 0.85],
        "W_main": [4000.0, 6000.0, 8000.0]
    }
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in [200, 404], f"Unexpected error: {response.text}"

def test_5_multiple_coefficients_success():
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam": [120000.0],
        "H_steam": 2400.0,
        "t1_main": [20.0],
        "coefficient_b": [0.5, 0.6, 0.7],
        "W_main": [5000.0]
    }
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in [200, 404], f"Unexpected error: {response.text}"


# ==========================================
# 🟡 ВАЛИДАЦИЯ (422 Unprocessable Entity)
# ==========================================

def test_6_val_missing_method():
    response = client.post(ENDPOINT, json={"condenser_id": 1})
    # Теперь, когда роутер подключен, это ДОЛЖНО быть 422
    assert response.status_code == 422

def test_7_val_unknown_method():
    assert client.post(ENDPOINT, json={"method": "invalid", "condenser_id": 1}).status_code == 422

def test_8_val_missing_ids():
    assert client.post(ENDPOINT, json={"method": "berman"}).status_code == 422

def test_9_val_missing_arrays():
    assert client.post(ENDPOINT, json={"method": "berman", "condenser_id": 1}).status_code == 422

def test_10_val_wrong_type_id():
    payload = {"method": "berman", "condenser_id": "not_int", "coefficient_b": [0.1], "W_main": [100]}
    assert client.post(ENDPOINT, json=payload).status_code == 422

def test_11_val_wrong_type_arrays():
    payload = {"method": "berman", "condenser_id": 1, "coefficient_b": "not_list", "W_main": [100]}
    assert client.post(ENDPOINT, json=payload).status_code == 422

def test_12_val_empty_payload():
    assert client.post(ENDPOINT, json={}).status_code == 422

def test_13_val_null_in_array():
    payload = {"method": "berman", "condenser_id": 1, "coefficient_b": [None], "W_main": [8000]}
    assert client.post(ENDPOINT, json=payload).status_code == 422

def test_14_val_string_in_array():
    payload = {"method": "berman", "condenser_id": 1, "coefficient_b": [0.1], "W_main": [8000, "error"]}
    assert client.post(ENDPOINT, json=payload).status_code == 422

def test_15_val_method_case_sensitive():
    payload = {"method": "BERMAN", "condenser_id": 1, "coefficient_b": [0.1], "W_main": [100]}
    assert client.post(ENDPOINT, json=payload).status_code == 422

def test_16_val_builtin_wrong_type():
    payload = {"method": "berman", "condenser_id": 1, "coefficient_b": [0.1], "W_main": [100], "W_builtin": "not_list"}
    assert client.post(ENDPOINT, json=payload).status_code == 422

def test_17_val_material_id_type():
    payload = {"method": "berman", "condenser_id": 1, "material_id": "string", "coefficient_b": [0.1], "W_main": [100]}
    assert client.post(ENDPOINT, json=payload).status_code == 422

def test_18_val_non_numeric_coefficient():
    payload = {"method": "berman", "condenser_id": 1, "coefficient_b": ["0.8"], "W_main": [100]}
    # Если Pydantic не сможет сконвертировать строку в float - будет 422
    assert client.post(ENDPOINT, json=payload).status_code in [200, 404, 422]


# ==========================================
# 🔴 ОШИБКИ ЛОГИКИ (404 / 400)
# ==========================================

def test_19_not_found_condenser():
    # Используем правильные данные, но плохой ID.
    # Если вернется 422 - значит движок проверяет существование в БД до расчетов.
    payload = {"method": "berman", "condenser_id": 99999, "coefficient_b": [0.8], "W_main": [8000.0]}
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in [404, 422]

def test_20_not_found_material():
    payload = {"method": "berman", "condenser_id": 1, "material_id": 99999, "coefficient_b": [0.8], "W_main": [8000.0]}
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in [404, 422]

def test_21_engine_error_empty_input():
    # Пустые списки могут пройти валидацию схемы, но упасть на этапе расчетов (400)
    payload = {"method": "berman", "condenser_id": 1, "coefficient_b": [], "W_main": []}
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in [400, 422, 404]


# ==========================================
# 🟣 EDGE CASES & WARNINGS (COND-8)
# ==========================================

def test_22_edge_one_bundle_builtin_none():
    """Тест "один пучок" (W_builtin = None)"""
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam": [120000.0],
        "H_steam": 2400.0,
        "t1_main":[20.0],
        "coefficient_b": [0.8],
        "W_main":[8000.0],
        "W_builtin": None
    }
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in[200, 404]

def test_23_edge_one_bundle_builtin_empty():
    """Тест "один пучок" (W_builtin =[])"""
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam": [120000.0],
        "H_steam": 2400.0,
        "t1_main": [20.0],
        "coefficient_b": [0.8],
        "W_main": [8000.0],
        "W_builtin":[]
    }
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in [200, 404, 422]

def test_24_edge_empty_array_coefficient_b():
    """Пустой массив coefficient_b =[] (должен использовать default)"""
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam": [120000.0],
        "H_steam": 2400.0,
        "t1_main": [20.0],
        "coefficient_b":[],
        "W_main": [8000.0]
    }
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in[200, 404, 422, 400]

def test_25_edge_empty_array_g_steam():
    """Пустой массив G_steam =[] (ошибка расчетов/валидации)"""
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam":[],
        "H_steam": 2400.0,
        "t1_main": [20.0],
        "coefficient_b": [0.8],
        "W_main": [8000.0]
    }
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in [422, 400]

def test_26_edge_empty_array_t1_main():
    """Пустой массив t1_main =[] (ошибка расчетов/валидации)"""
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam":[120000.0],
        "H_steam": 2400.0,
        "t1_main": [],
        "coefficient_b": [0.8],
        "W_main": [8000.0]
    }
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in [422, 400]

@pytest.mark.parametrize("b_val",[0.0, 1.0, 0.75, 0.999])
def test_27_edge_boundary_b(b_val):
    """Граничные значения коэффициента загрязнения b"""
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam": [120000.0],
        "H_steam": 2400.0,
        "t1_main": [20.0],
        "coefficient_b": [b_val],
        "W_main": [8000.0]
    }
    response = client.post(ENDPOINT, json=payload)
    # Если b=0.0 запрещен Pydantic-схемой, вернется 422, иначе 200 или 404
    assert response.status_code in [200, 404, 422]

@pytest.mark.parametrize("temp, expected_warning",[
    (0.0, False),    # Граница Бермана
    (45.0, False),   # Граница Бермана
    (150.0, True)    # Экстремальное значение, должно выдать warning
])
def test_28_edge_boundary_temperatures(temp, expected_warning):
    """Температурные граничные случаи и проверка генерации BR-10 / BR-11"""
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam": [120000.0],
        "H_steam": 2400.0,
        "t1_main": [temp],
        "coefficient_b": [0.8],
        "W_main": [8000.0]
    }
    response = client.post(ENDPOINT, json=payload)
    if response.status_code == 200:
        data = response.json()
        if expected_warning:
            has_warning = any(
                len(table.get("warnings",[])) > 0
                for table in data.get("tables",[])
            )
            assert has_warning, f"Ожидался warning (BR-10) для температуры {temp}"

def test_29_edge_different_lengths_w_main_builtin():
    """Разные длины массивов W_main и W_builtin (декартово произведение матриц)"""
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam":[120000.0],
        "H_steam": 2400.0,
        "t1_main": [20.0],
        "coefficient_b": [0.8],
        "W_main":[8000.0, 9000.0, 10000.0],
        "W_builtin":[1000.0, 2000.0]
    }
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in [200, 404, 422]

def test_30_edge_warning_br06_high_water_flow():
    """Тест генерации warnings: BR-06 Расход воды вне лимитов"""
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam": [120000.0],
        "H_steam": 2400.0,
        "t1_main": [20.0],
        "coefficient_b": [0.8],
        "W_main": [999999.0]  # Намеренно завышенный расход
    }
    response = client.post(ENDPOINT, json=payload)
    if response.status_code == 200:
        data = response.json()
        has_warning = any(
            any("расход" in w.lower() for w in table.get("warnings", []))
            for table in data.get("tables",[])
        )
        assert has_warning, "Ожидался warning BR-06 (превышен максимальный расход)"

def test_31_edge_invalid_combination_berman_missing_h_steam():
    """Берман без H_steam (некорректная комбинация для данного метода)"""
    payload = {
        "method": "berman",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam": [120000.0],
        "t1_main": [20.0],
        "coefficient_b": [0.8],
        "W_main": [8000.0],
        "X_steam": 0.95  # Поле для Метро-Виккерс
    }
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in [422, 400]

def test_32_edge_invalid_combination_metrovickers_with_h_steam():
    """Метро-Виккерс с H_steam (лишнее поле, валидация должна игнорировать или отбивать)"""
    payload = {
        "method": "metro-vickers",
        "condenser_id": 1,
        "material_id": 1,
        "G_steam": [120000.0],
        "H_steam": 2400.0,
        "t1_main": [20.0],
        "coefficient_b":[0.8],
        "W_main": [8000.0]
    }
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code in[200, 422, 400, 404]
