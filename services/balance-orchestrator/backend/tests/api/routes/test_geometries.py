"""
Тесты эндпоинтов geometries (манifest и файлы из GitLab).
"""

from unittest.mock import MagicMock, patch

import gitlab.exceptions
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.routes.geometries import get_geometry, list_geometries
from app.schemas.geometry import GeometriesManifest

MANIFEST_PATH = "geometries/geometries_manifest.json"
GEOMETRY_FILE_PATH = "geometries/condenser_01.json"
DEFAULT_BRANCH = "main"
GEOMETRY_ID = "condenser-01"

VALID_MANIFEST_JSON = """
{
  "schema_version": "1.0",
  "geometries": [
    {
      "id": "condenser-01",
      "name": "Test Condenser",
      "type": "condenser",
      "description": "Demo geometry",
      "file": "geometries/condenser_01.json"
    }
  ]
}
"""

VALID_GEOMETRY_JSON = """
{
  "id": "condenser-01",
  "type": "condenser",
  "version": "1.0",
  "dimensions": {
    "length": {"value": 10.0, "unit": "m"},
    "diameter": {"value": 2.0, "unit": "m"},
    "tube_count": 1000,
    "tube_diameter": {"value": 0.02, "unit": "m"}
  },
  "materials": {
    "shell": "steel",
    "tubes": "brass"
  }
}
"""

INVALID_MANIFEST_JSON = """
{
  "schema_version": "1.0",
  "geometries": [{}]
}
"""

BROKEN_JSON = "{ not valid json }"


def make_gitlab_file(content: str) -> MagicMock:
    mock_file = MagicMock()
    mock_file.decode.return_value = content.encode("utf-8")
    return mock_file


def setup_gitlab_success(
    mock_gitlab: MagicMock,
    manifest_json: str = VALID_MANIFEST_JSON,
    geometry_files: dict[str, str] | None = None,
) -> MagicMock:
    geometry_files = geometry_files or {}
    mock_project = MagicMock()
    mock_gitlab.get_project.return_value = mock_project
    mock_gitlab.default_branch = DEFAULT_BRANCH

    def files_get(file_path: str, ref: str):
        if file_path == MANIFEST_PATH:
            return make_gitlab_file(manifest_json)
        if file_path in geometry_files:
            return make_gitlab_file(geometry_files[file_path])
        raise gitlab.exceptions.GitlabGetError("404 File Not Found")

    mock_project.files.get.side_effect = files_get
    return mock_project


class TestGeometriesManifest:
    """Валидация GeometriesManifest.model_validate_json."""

    def test_valid_manifest_parses(self):
        manifest = GeometriesManifest.model_validate_json(VALID_MANIFEST_JSON)

        assert manifest.schema_version == "1.0"
        assert len(manifest.geometries) == 1
        assert manifest.geometries[0].id == GEOMETRY_ID
        assert manifest.geometries[0].file == GEOMETRY_FILE_PATH

    def test_invalid_manifest_raises_validation_error(self):
        with pytest.raises(ValidationError):
            GeometriesManifest.model_validate_json(INVALID_MANIFEST_JSON)

    def test_non_json_raises_validation_error(self):
        with pytest.raises(ValidationError):
            GeometriesManifest.model_validate_json(BROKEN_JSON)


class TestListGeometries:
    """Тесты эндпоинта list_geometries."""

    @pytest.mark.asyncio
    @patch("app.api.routes.geometries.gitlab_client")
    async def test_list_geometries_parses_manifest(self, mock_gitlab: MagicMock):
        """Должен вернуть список геометрий из валидного манифеста."""
        mock_project = setup_gitlab_success(mock_gitlab)

        result = await list_geometries()

        assert len(result) == 1
        assert result[0].id == GEOMETRY_ID
        assert result[0].name == "Test Condenser"
        assert result[0].file == GEOMETRY_FILE_PATH

        mock_gitlab.get_project.assert_called_once()
        mock_project.files.get.assert_called_once_with(
            file_path=MANIFEST_PATH,
            ref=DEFAULT_BRANCH,
        )

    @pytest.mark.asyncio
    @patch("app.api.routes.geometries.gitlab_client")
    async def test_list_raises_404_when_manifest_not_found(self, mock_gitlab: MagicMock):
        """Должен вернуть 404, если файл манифеста отсутствует в GitLab."""
        mock_project = MagicMock()
        mock_gitlab.get_project.return_value = mock_project
        mock_gitlab.default_branch = DEFAULT_BRANCH
        mock_project.files.get.side_effect = gitlab.exceptions.GitlabGetError("404")

        with pytest.raises(HTTPException) as exc_info:
            await list_geometries()

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Манифест геометрий не найден в GitLab"

    @pytest.mark.asyncio
    @patch("app.api.routes.geometries.gitlab_client")
    async def test_list_raises_401_on_authentication_error(self, mock_gitlab: MagicMock):
        """Должен вернуть 401 при ошибке авторизации в GitLab."""
        mock_gitlab.get_project.side_effect = gitlab.exceptions.GitlabAuthenticationError(
            "Auth failed"
        )

        with pytest.raises(HTTPException) as exc_info:
            await list_geometries()

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Ошибка авторизации в GitLab"

    @pytest.mark.asyncio
    @patch("app.api.routes.geometries.gitlab_client")
    async def test_list_raises_502_on_gitlab_error(self, mock_gitlab: MagicMock):
        """Должен вернуть 502 при ошибке GitLab API."""
        mock_gitlab.get_project.side_effect = gitlab.exceptions.GitlabError("API error")

        with pytest.raises(HTTPException) as exc_info:
            await list_geometries()

        assert exc_info.value.status_code == 502
        assert exc_info.value.detail == "Ошибка GitLab API: API error"

    @pytest.mark.asyncio
    @patch("app.api.routes.geometries.gitlab_client")
    async def test_list_raises_500_on_invalid_manifest(self, mock_gitlab: MagicMock):
        """Должен вернуть 500, если JSON манифеста не проходит валидацию Pydantic."""
        setup_gitlab_success(mock_gitlab, manifest_json=INVALID_MANIFEST_JSON)

        with pytest.raises(HTTPException) as exc_info:
            await list_geometries()

        assert exc_info.value.status_code == 500
        assert "Ошибка чтения манифеста" in exc_info.value.detail


class TestGetGeometry:
    """Тесты эндпоинта get_geometry."""

    @pytest.mark.asyncio
    @patch("app.api.routes.geometries.gitlab_client")
    async def test_get_geometry_returns_geometry_data(self, mock_gitlab: MagicMock):
        """Должен вернуть полный JSON геометрии, если id и файл существуют."""
        mock_project = setup_gitlab_success(
            mock_gitlab,
            geometry_files={GEOMETRY_FILE_PATH: VALID_GEOMETRY_JSON},
        )

        result = await get_geometry(GEOMETRY_ID)

        assert result["id"] == GEOMETRY_ID
        assert result["dimensions"]["tube_count"] == 1000
        assert mock_project.files.get.call_count == 2

    @pytest.mark.asyncio
    @patch("app.api.routes.geometries.gitlab_client")
    async def test_get_geometry_raises_404_when_id_not_in_manifest(self, mock_gitlab: MagicMock):
        """Должен вернуть 404, если id геометрии отсутствует в манифесте."""
        mock_project = setup_gitlab_success(mock_gitlab)

        with pytest.raises(HTTPException) as exc_info:
            await get_geometry("unknown-id")

        assert exc_info.value.status_code == 404
        assert "unknown-id" in exc_info.value.detail
        assert mock_project.files.get.call_count == 1

    @pytest.mark.asyncio
    @patch("app.api.routes.geometries.gitlab_client")
    async def test_get_geometry_raises_404_when_geometry_file_missing(self, mock_gitlab: MagicMock):
        """Должен вернуть 404, если файл геометрии отсутствует в GitLab."""
        setup_gitlab_success(mock_gitlab)

        with pytest.raises(HTTPException) as exc_info:
            await get_geometry(GEOMETRY_ID)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Геометрия или файл не найдены в GitLab"

    @pytest.mark.asyncio
    @patch("app.api.routes.geometries.gitlab_client")
    async def test_get_raises_401_on_authentication_error(self, mock_gitlab: MagicMock):
        """Должен вернуть 401 при ошибке авторизации в GitLab."""
        mock_gitlab.get_project.side_effect = gitlab.exceptions.GitlabAuthenticationError(
            "Auth failed"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_geometry(GEOMETRY_ID)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Ошибка авторизации в GitLab"

    @pytest.mark.asyncio
    @patch("app.api.routes.geometries.gitlab_client")
    async def test_get_raises_502_on_gitlab_error(self, mock_gitlab: MagicMock):
        """Должен вернуть 502 при ошибке GitLab API."""
        mock_project = MagicMock()
        mock_gitlab.get_project.return_value = mock_project
        mock_gitlab.default_branch = DEFAULT_BRANCH
        mock_project.files.get.side_effect = gitlab.exceptions.GitlabError("API error")

        with pytest.raises(HTTPException) as exc_info:
            await get_geometry(GEOMETRY_ID)

        assert exc_info.value.status_code == 502
        assert "Ошибка GitLab API" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("app.api.routes.geometries.gitlab_client")
    async def test_get_raises_500_on_invalid_geometry_json(self, mock_gitlab: MagicMock):
        """Должен вернуть 500, если файл геометрии содержит невалидный JSON."""
        setup_gitlab_success(
            mock_gitlab,
            geometry_files={GEOMETRY_FILE_PATH: BROKEN_JSON},
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_geometry(GEOMETRY_ID)

        assert exc_info.value.status_code == 500
        assert "Ошибка чтения геометрии" in exc_info.value.detail
