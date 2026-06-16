"""
Роутер для работы с геометрическими моделями.
Обеспечивает чтение списка доступных геометрий и их содержимого напрямую 
из файлов репозитория GitLab (ветка по умолчанию).
"""
import json

import gitlab.exceptions
from fastapi import APIRouter, HTTPException, Path

from app.core.gitlab_adapter import gitlab_client
from app.schemas.geometry import GeometriesManifest, GeometryInfo


router = APIRouter(prefix="/geometries", tags=["Geometries"])


@router.get(
    "", 
    response_model=list[GeometryInfo],
    summary="Получение списка геометрий",
    response_description="Массив объектов с метаданными всех доступных геометрий (ID, название, путь к файлу)"
)
async def list_geometries():
    """
    Получает список всех доступных геометрий.

    Читает и парсит файл манифеста `geometries/geometries_manifest.json` из 
    дефолтной ветки (main/master) репозитория проекта в GitLab.

    Returns:
        list[GeometryInfo]: Список валидированных Pydantic-объектов с информацией о геометриях.

    Raises:
        HTTPException (401): При недействительном токене GitLab.
        HTTPException (404): Если файл манифеста не найден в репозитории.
        HTTPException (502): При проблемах сети или на стороне API GitLab.
        HTTPException (500): При ошибках парсинга JSON или других системных сбоях.
    """
    try:
        project = gitlab_client.get_project()
        file = project.files.get(
            file_path="geometries/geometries_manifest.json",
            ref=gitlab_client.default_branch
        )
        # file.decode() возвращает bytes от GitLab API, второе decode("utf-8") преобразует в строку
        content = file.decode().decode("utf-8")
        manifest = GeometriesManifest.model_validate_json(content)
        return manifest.geometries
    except gitlab.exceptions.GitlabAuthenticationError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации в GitLab")
    except gitlab.exceptions.GitlabGetError:
        raise HTTPException(status_code=404, detail="Манифест геометрий не найден в GitLab")
    except gitlab.exceptions.GitlabError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка GitLab API: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения манифеста: {e}")


@router.get(
    "/{geometry_id}",
    summary="Получение файла геометрии по ID",
    response_description="Сырой JSON-объект с данными запрошенной геометрии"
)
async def get_geometry(
    geometry_id: str = Path(..., title="ID Геометрии", description="Уникальный строковый идентификатор геометрии (например, 'condenser_v1')")
):
    """
    Получает полное содержимое файла конкретной геометрии по её идентификатору.

    Args:
        geometry_id (str): Идентификатор геометрии для поиска.

    Returns:
        dict: Распарсенный JSON-объект, содержащий структуру геометрии.

    Raises:
        HTTPException (404): Если ID не найден в манифесте или отсутствует сам файл в GitLab.
        HTTPException (401, 502, 500): Стандартные ошибки доступа к GitLab API и серверные сбои.
    """
    try:
        # [ENGINEERING CONTEXT]
        # Почему реализовано двухшаговое чтение (Манифест -> Путь -> Файл):
        # Манифест выступает в роли единого реестра (Source of Truth). 
        # Мы намеренно не хардкодим алгоритм сборки пути вида `f"geometries/{geometry_id}.json"`.
        # Использование манифеста позволяет хранить файлы геометрий в подпапках, менять 
        # их расширения или переименовывать физические файлы без изменения бизнес-логики и API.
        
        # 1. Читаем манифест для поиска пути
        project = gitlab_client.get_project()
        manifest_file = project.files.get(
            file_path="geometries/geometries_manifest.json",
            ref=gitlab_client.default_branch
        )
        manifest = GeometriesManifest.model_validate_json(
            manifest_file.decode().decode("utf-8")
        )

        # 2. Ищем геометрию по ID
        geometry_info = next(
            (g for g in manifest.geometries if g.id == geometry_id),
            None
        )
        if not geometry_info:
            raise HTTPException(status_code=404, detail=f"Геометрия {geometry_id} не найдена")

        # 3. Читаем целевой файл геометрии
        geometry_file = project.files.get(
            file_path=geometry_info.file,
            ref=gitlab_client.default_branch
        )
        geometry_data = json.loads(geometry_file.decode().decode("utf-8"))

        return geometry_data

    except gitlab.exceptions.GitlabAuthenticationError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации в GitLab")
    except gitlab.exceptions.GitlabGetError:
        raise HTTPException(status_code=404, detail="Геометрия или файл не найдены в GitLab")
    except gitlab.exceptions.GitlabError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка GitLab API: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения геометрии: {e}")
        