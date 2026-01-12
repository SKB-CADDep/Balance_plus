# api/routes/geometries.py
import json
from fastapi import APIRouter, HTTPException

from app.schemas.geometry import GeometriesManifest, GeometryInfo, CondenserGeometry
from app.core.gitlab_adapter import gitlab_client

router = APIRouter(prefix="/geometries", tags=["Geometries"])


@router.get("", response_model=list[GeometryInfo])
async def list_geometries():
    """Получить список всех доступных геометрий"""
    try:
        project = gitlab_client.get_project()
        file = project.files.get(
            file_path="geometries/geometries_manifest.json",
            ref=gitlab_client.default_branch
        )
        content = file.decode().decode("utf-8")
        manifest = GeometriesManifest.model_validate_json(content)
        return manifest.geometries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения манифеста: {e}")


@router.get("/{geometry_id}")
async def get_geometry(geometry_id: str):
    """Получить полную геометрию по ID"""
    try:
        # Сначала находим файл в манифесте
        project = gitlab_client.get_project()
        manifest_file = project.files.get(
            file_path="geometries/geometries_manifest.json",
            ref=gitlab_client.default_branch
        )
        manifest = GeometriesManifest.model_validate_json(
            manifest_file.decode().decode("utf-8")
        )

        # Ищем геометрию по ID
        geometry_info = next(
            (g for g in manifest.geometries if g.id == geometry_id),
            None
        )
        if not geometry_info:
            raise HTTPException(status_code=404, detail=f"Геометрия {geometry_id} не найдена")

        # Читаем файл геометрии
        geometry_file = project.files.get(
            file_path=geometry_info.file,
            ref=gitlab_client.default_branch
        )
        geometry_data = json.loads(geometry_file.decode().decode("utf-8"))

        return geometry_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения геометрии: {e}")