"""
Роутер конфигурации приложения.
Отвечает за предоставление клиенту статических/настроечных словарей.
"""
# api/routes/config.py
from fastapi import APIRouter

from app.schemas.task import BUREAU_CONFIG


router = APIRouter(prefix="/config", tags=["Config"])


@router.get(
    "/bureaus",
    summary="Получение списка бюро и модулей",
    response_description="Массив объектов бюро с вложенными модулями для рендеринга UI на клиенте"
)
async def get_bureaus():
    """
    Возвращает конфигурацию бюро и доступных модулей для отрисовки фронтенда.

    Выполняет трансформацию внутреннего конфигурационного словаря `BUREAU_CONFIG` 
    в массив, адаптированный под требования UI-компонентов.

    Returns:
        list[dict]: Список объектов бюро. Каждый словарь содержит ключи:
            - id (str): Уникальный строковый код бюро (например, "teplo").
            - label (str): Читабельное название бюро для отображения пользователю.
            - color (str): Строка цвета (HEX или системное имя) для визуальной индикации.
            - modules (list[dict]): Список доступных модулей внутри бюро, где каждый 
              модуль содержит ключи `id` (str) и `label` (str).
    """
    # [ENGINEERING CONTEXT]
    # Почему выполняется итерация и маппинг, а не просто return BUREAU_CONFIG:
    # Объект BUREAU_CONFIG на бэкенде имеет структуру вложенного словаря (O(1) доступ по ключу).
    # Однако современным фронтенд-библиотекам (UI-компоненты вроде Select, List, Menu)
    # для отрисовки требуется плоский итерируемый массив объектов с унифицированными 
    # полями `id` и `label`.
    # Данный участок кода реализует паттерн BFF (Backend-For-Frontend), перекладывая 
    # вычислительную работу по адаптации структур данных на сервер.
    bureaus = []
    for bureau_code, bureau_data in BUREAU_CONFIG.items():
        modules = [
            {"id": module_code, "label": module_name}
            for module_code, module_name in bureau_data["modules"].items()
        ]
        bureaus.append({
            "id": bureau_code,
            "label": bureau_data["name"],
            "color": bureau_data["color"],
            "modules": modules
        })
    return bureaus