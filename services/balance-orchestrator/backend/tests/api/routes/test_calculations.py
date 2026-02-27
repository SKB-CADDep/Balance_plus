# Описание файла для отображения в главном меню CLI
description = "Сохранение и получение результатов расчетов (GitLab)"

# Базовые настройки для всех тестов в этом файле
defaults = {
    # Укажи тут порт, на котором крутится твой локальный FastAPI
    "base_url": "http://localhost:8005", 
    "headers": {
        "Content-Type": "application/json"
    }
}

# Список тестов
tests =[
    # --- БЛОК 1: Сохранение расчетов ---
    {
        "id": "save_success",
        "description": "Успешное сохранение результата",
        "request": {
            "method": "POST",
            "endpoint": "/api/v1/calculations/save", # Уточни свой реальный роут
            "json": {
                "task_iid": 42,
                "project_id": 123,
                "app_type": "valves",
                "input_data": {"param1": "value1"},
                "output_data": {"result": "success"},
                "commit_message": "Test commit"
            }
        },
        "expected": {
            "status_code": 200,
            "response_contains": {
                "status": "saved"
            }
        }
    },
    {
        "id": "save_fail_400",
        "description": "Ошибка 400 - Ветка не найдена (несуществующий task_iid)",
        "request": {
            "method": "POST",
            "endpoint": "/api/v1/calculations/save",
            "json": {
                "task_iid": 99999,  # Специально даем плохой ID задачи
                "project_id": 123,
                "app_type": "valves",
                "input_data": {"param1": "value1"},
                "output_data": {"result": "success"}
            }
        },
        "expected": {
            "status_code": 400
        }
    },

    # --- БЛОК 2: Получение расчетов ---
    {
        "id": "get_success",
        "description": "Получение данных последнего расчета",
        "request": {
            "method": "GET",
            "endpoint": "/api/v1/calculations/latest",
            "params": {
                "task_iid": 42,
                "project_id": 123,
                "app_type": "valves"
            }
        },
        "expected": {
            "status_code": 200,
            "response_contains": {
                "found": True
            }
        }
    }
]