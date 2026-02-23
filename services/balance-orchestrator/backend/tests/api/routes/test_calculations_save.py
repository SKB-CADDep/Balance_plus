import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app 

client = TestClient(app)

# Обратите внимание на путь в patch. Он должен вести туда, где gitlab_client ИСПОЛЬЗУЕТСЯ
@patch("app.api.routes.calculations.gitlab_client") 
def test_save_calculation_with_conversion(mock_gitlab):
    """
    Интеграционный тест с проверкой конвертации и моком GitLab.
    """
    
    # 1. Настраиваем Mock (чтобы GitLab не отвечал 404 или 401)
    # Настраиваем ответ для поиска ветки
    mock_gitlab.find_branch_by_issue_iid.return_value = "feature/task-1"
    
    # Настраиваем ответ для создания коммита
    mock_commit = MagicMock()
    mock_commit.id = "hash123"
    mock_commit.web_url = "http://gitlab.local/commit/hash123"
    mock_gitlab.create_commit_multiple.return_value = mock_commit

    # 2. Входные данные (Payload)
    payload = {
        "task_iid": 1,
        "project_id": 10,
        "app_type": "valves",
        "input_data": {
            # Специально передаем МПа, чтобы проверить конвертацию в кгс/см²
            "inlet": {"value": 5, "unit": "МПа", "param_type": "pressure"}
        },
        "output_data": {},
        "commit_message": "test"
    }

    # 3. Выполняем запрос
    # ВАЖНО: Добавлен префикс /api/v1 (проверьте свой main.py, если не сработает)
    response = client.post("/api/v1/calculations/save", json=payload)

    # Если всё еще 404 — раскомментируйте строки ниже для отладки:
    # print(response.json()) 
    
    # 4. Проверки
    assert response.status_code == 200
    assert response.json()["status"] == "saved"

    # 5. Проверяем, что данные сконвертировались перед отправкой в GitLab
    # Получаем аргументы, с которыми был вызван create_commit_multiple
    call_args = mock_gitlab.create_commit_multiple.call_args
    # Ищем аргумент 'files' (он может быть позиционным или именованным)
    files_argument = call_args.kwargs.get("files")
    if not files_argument:
        files_argument = call_args[0][0] # Если позиционный аргумент

    import json
    # Достаем содержимое файла input.json, который мы якобы отправили в гит
    input_json_sent = json.loads(files_argument["calculations/valves/current/input.json"])
    
    # Логика проверки: 5 МПа ≈ 50.98 кгс/см²
    sent_value = input_json_sent["inlet"]["value"]
    sent_unit = input_json_sent["inlet"]["unit"]
    
    print(f"Отправлено в GitLab: {sent_value} {sent_unit}") # Для отладки
    
    assert sent_unit == "кгс/см²"
    assert 50 < sent_value < 52