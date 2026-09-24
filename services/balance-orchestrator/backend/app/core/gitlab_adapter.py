import logging
import os
import time
from pathlib import Path
from typing import Any

import gitlab
from dotenv import load_dotenv
from gitlab.exceptions import GitlabGetError


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger(__name__)


class GitLabConfigurationError(RuntimeError):
    """GitLab integration is not configured or contains invalid values."""


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        logger.warning("Invalid numeric environment value", extra={"name": name})
        return default


class GitLabAdapter:
    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        project_id: int | str | None = None,
        ssl_verify: bool | None = None,
        timeout: float | None = None,
    ) -> None:
        self.url = (url if url is not None else os.getenv("GITLAB_URL", "")).strip().rstrip("/")
        self.token = (
            token
            if token is not None
            else os.getenv("GITLAB_PRIVATE_TOKEN") or os.getenv("GITLAB_TOKEN", "")
        ).strip()
        self.project_id = (
            project_id if project_id is not None else os.getenv("GITLAB_PROJECT_ID")
        )
        self.ssl_verify = (
            ssl_verify if ssl_verify is not None else _env_bool("GITLAB_SSL_VERIFY", False)
        )
        self.timeout = timeout if timeout is not None else _env_float("GITLAB_TIMEOUT", 10.0)

        # Клиент создаётся лениво. Благодаря этому API и /health запускаются даже
        # без .env, а причина ошибки видна через /health/gitlab.
        self._gl: gitlab.Gitlab | None = None
        self._project = None
        self._default_branch = None
        self._projects_cache: dict[int, tuple[Any, float]] = {}
        self.CACHE_TTL = 300  # Время жизни кеша: 5 минут (300 сек)

    @property
    def configured(self) -> bool:
        return bool(self.url and self.token)

    @property
    def gl(self) -> gitlab.Gitlab:
        if not self.configured:
            missing = []
            if not self.url:
                missing.append("GITLAB_URL")
            if not self.token:
                missing.append("GITLAB_PRIVATE_TOKEN")
            raise GitLabConfigurationError(
                f"Не заданы обязательные настройки GitLab: {', '.join(missing)}"
            )

        if self._gl is None:
            self._gl = gitlab.Gitlab(
                self.url,
                private_token=self.token,
                ssl_verify=self.ssl_verify,
                timeout=self.timeout,
                retry_transient_errors=True,
            )
        return self._gl

    def connection_summary(self) -> dict[str, Any]:
        """Безопасная диагностика конфигурации без токена."""
        return {
            "configured": self.configured,
            "url": self.url or None,
            "project_id": self.project_id,
            "ssl_verify": self.ssl_verify,
            "timeout_seconds": self.timeout,
        }

    def check_connection(self, check_project: bool = False) -> dict[str, Any]:
        """Проверяет токен и, при необходимости, доступ к проекту по умолчанию."""
        self.gl.auth()
        result = {
            **self.connection_summary(),
            "status": "ok",
            "username": self.gl.user.username,
        }
        if check_project:
            if not self.project_id:
                raise GitLabConfigurationError("GITLAB_PROJECT_ID не задан в .env")
            project = self.get_project()
            result["project"] = {
                "id": project.id,
                "path": project.path_with_namespace,
                "default_branch": project.default_branch,
            }
        return result

    def get_current_user(self):
        if self.gl.user is None:
            self.gl.auth()
        return self.gl.user

    def get_project(self):
        """Получает объект текущего рабочего проекта (с кешированием)"""
        if self._project is None:
            if not self.project_id:
                raise GitLabConfigurationError("GITLAB_PROJECT_ID не задан в .env")
            self._project = self.gl.projects.get(self.project_id)
            self._default_branch = self._project.default_branch
            logger.info(
                "Connected to default GitLab project",
                extra={
                    "project": self._project.path_with_namespace,
                    "default_branch": self._default_branch,
                },
            )
        return self._project

    def get_project_by_id(self, project_id: int):
        """Получает проект по ID с кешированием и безопасной обработкой ошибок"""
        now = time.time()

        project_id = int(project_id)
        if project_id in self._projects_cache:
            project, timestamp = self._projects_cache[project_id]
            if now - timestamp < self.CACHE_TTL:
                return project

        logger.debug("Fetching GitLab project", extra={"project_id": project_id})
        project = self.gl.projects.get(project_id)
        self._projects_cache[project_id] = (project, now)
        return project

    @property
    def default_branch(self) -> str:
        """Возвращает дефолтную ветку проекта"""
        if self._default_branch is None:
            self.get_project()
        return self._default_branch

    # ==================== РАБОТА С ФАЙЛАМИ ====================

    def get_file_content(
        self, file_path: str, ref: str | None = None, project_id: int | None = None
    ) -> str:
        """Читает содержимое файла из репозитория"""
        project = self.get_project_by_id(project_id) if project_id else self.get_project()
        ref = ref or (project.default_branch if project_id else self.default_branch)
        file = project.files.get(file_path=file_path, ref=ref)
        return file.decode().decode("utf-8")

    def file_exists(
        self, file_path: str, ref: str | None = None, project_id: int | None = None
    ) -> bool:
        """Проверяет, существует ли файл"""
        project = self.get_project_by_id(project_id) if project_id else self.get_project()
        ref = ref or (project.default_branch if project_id else self.default_branch)
        try:
            project.files.get(file_path=file_path, ref=ref)
            return True
        except GitlabGetError:
            return False

    def create_commit(
        self,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str | None = None,
        project_id: int | None = None,
    ):
        """Создает или обновляет файл в репозитории"""
        project = self.get_project_by_id(project_id) if project_id else self.get_project()
        branch = branch or (project.default_branch if project_id else self.default_branch)

        action = (
            "update" if self.file_exists(file_path, branch, project_id=project_id) else "create"
        )

        data = {
            "branch": branch,
            "commit_message": commit_message,
            "actions": [{"action": action, "file_path": file_path, "content": content}],
        }

        commit = project.commits.create(data)
        return commit

    def create_commit_multiple(
        self,
        files: dict[str, str],
        commit_message: str,
        branch: str | None = None,
        project_id: int | None = None,
    ):
        """Создает коммит с несколькими файлами одновременно"""
        project = self.get_project_by_id(project_id) if project_id else self.get_project()
        branch = branch or (project.default_branch if project_id else self.default_branch)

        actions = []
        for file_path, content in files.items():
            action = (
                "update" if self.file_exists(file_path, branch, project_id=project_id) else "create"
            )
            actions.append({"action": action, "file_path": file_path, "content": content})

        data = {
            "branch": branch,
            "commit_message": commit_message,
            "actions": actions,
        }

        commit = project.commits.create(data)
        return commit

    def list_files_in_path(self, path: str, ref: str, project_id: int | None = None) -> list[dict]:
        """Возвращает список файлов в папке"""
        project = self.get_project_by_id(project_id) if project_id else self.get_project()
        try:
            return project.repository_tree(path=path, ref=ref, recursive=False)
        except GitlabGetError:
            return []

    def get_file_content_decoded(
        self, file_path: str, ref: str, project_id: int | None = None
    ) -> str | None:
        """Читает файл и декодирует контент"""
        try:
            project = self.get_project_by_id(project_id) if project_id else self.get_project()
            f = project.files.get(file_path=file_path, ref=ref)
            return f.decode().decode("utf-8")
        except GitlabGetError:
            return None

    # ==================== РАБОТА С ВЕТКАМИ ====================

    def create_branch(
        self, branch_name: str, source_branch: str | None = None, project_id: int | None = None
    ) -> bool:
        """Создаёт новую ветку. Возвращает True если создана, False если уже существует"""
        project = self.get_project_by_id(project_id) if project_id else self.get_project()
        source = source_branch or (project.default_branch if project_id else self.default_branch)

        try:
            project.branches.create({"branch": branch_name, "ref": source})
            print(f"✅ Создана ветка: {branch_name}")
            return True
        except gitlab.exceptions.GitlabCreateError as e:
            if "already exists" in str(e):
                print(f"ℹ️ Ветка {branch_name} уже существует")
                return False
            raise

    def branch_exists(self, branch_name: str, project_id: int | None = None) -> bool:
        """Проверяет существование ветки"""
        project = self.get_project_by_id(project_id) if project_id else self.get_project()
        try:
            project.branches.get(branch_name)
            return True
        except GitlabGetError:
            return False

    def find_branch_by_issue_iid(self, issue_iid: int, project_id: int) -> str | None:
        """
        Умный поиск ветки задачи.
        Ищет ветку, которая начинается с '4-' или 'issue/4-' или 'feature/4-'.
        """
        project = self.get_project_by_id(project_id)
        str_iid = str(issue_iid)

        # Ищем все ветки, содержащие ID задачи (API search)
        branches = project.branches.list(search=str_iid, get_all=True)

        if not branches:
            logger.info("No GitLab branches found for issue", extra={"issue_iid": issue_iid})
            return None

        logger.debug(
            "GitLab branch candidates found",
            extra={"issue_iid": issue_iid, "branches": [b.name for b in branches]},
        )

        # 2. Фильтруем кандидатов
        for b in branches:
            name = b.name

            # Проверка 1: Начинается с ID (4-fix...)
            if name.startswith(f"{str_iid}-"):
                return name

            # Проверка 2: Содержит ID после слэша (.../4-fix...)
            # Это покрывает 'issue/4-', 'feature/4-', 'bugfix/4-'
            if f"/{str_iid}-" in name:
                return name

            # Проверка 3: Точное совпадение (просто '4')
            if name == str_iid:
                return name

        logger.info("No GitLab branch matched issue naming convention", extra={"issue_iid": issue_iid})
        return None

    # ==================== РАБОТА С ЗАДАЧАМИ (ISSUES) ====================

    def get_all_assigned_issues(
        self, state: str = "opened", project_id: int | None = None
    ) -> list[dict]:
        """Получает назначенные пользователю задачи глобально или в одном проекте."""
        user = self.get_current_user()

        if project_id is not None:
            project = self.get_project_by_id(project_id)
            issues = project.issues.list(
                assignee_id=user.id,
                state=state,
                get_all=True,
            )
            projects = {int(project.id): project}
        else:
            issues = self.gl.issues.list(
                assignee_id=user.id,
                state=state,
                scope="all",
                get_all=True,
            )
            projects = {}

        result = []
        for issue in issues:
            issue_project_id = int(getattr(issue, "project_id", project_id))
            proj = projects.get(issue_project_id)
            if proj is None:
                proj = self.get_project_by_id(issue.project_id)

            result.append(
                {
                    "iid": issue.iid,
                    "project_id": issue_project_id,
                    "project_name": proj.name,
                    "title": issue.title,
                    "description": issue.description,
                    "state": issue.state,
                    "labels": issue.labels,
                    "assignee": issue.assignee["username"] if issue.assignee else None,
                    "created_at": issue.created_at,
                    "due_date": issue.due_date,
                    "web_url": issue.web_url,
                }
            )
        return result

    def get_issue(self, issue_iid: int, project_id: int) -> dict:
        project = self.get_project_by_id(project_id)
        issue = project.issues.get(issue_iid)
        return {
            "iid": issue.iid,
            "project_id": project_id,
            "project_name": project.name,  # без namespace
            "title": issue.title,
            "description": issue.description,
            "state": issue.state,
            "labels": issue.labels,
            "assignee": issue.assignee["username"] if issue.assignee else None,
            "created_at": issue.created_at,
            "due_date": issue.due_date,
            "web_url": issue.web_url,
        }

    def get_user_projects(self, search: str = "") -> list[dict]:
        """Возвращает проекты пользователя (для выпадающего списка)"""
        # membership=True: только те, где я участник
        # order_by='last_activity_at': сначала те, с которыми недавно работали (удобно)
        projects = self.gl.projects.list(
            membership=True,
            search=search,
            order_by="last_activity_at",
            min_access_level=30,  # Developer и выше (чтобы мог создавать задачи)
            simple=True,
            get_all=False,  # Не тянем все 100500, хватит первых 20-50 для саджеста
            per_page=50,
        )
        return [{"id": p.id, "name": p.name_with_namespace, "web_url": p.web_url} for p in projects]

    def create_issue(
        self,
        title: str,
        description: str = "",
        labels: list[str] | None = None,
        project_id: int | None = None,
    ) -> dict:
        """Создаёт новую задачу"""
        # Если ID передан - берем конкретный проект. Иначе - дефолтный из ENV (для совместимости)
        project = self.get_project_by_id(project_id) if project_id else self.get_project()
        user = self.get_current_user()
        issue = project.issues.create(
            {
                "title": title,
                "description": description,
                "labels": labels or [],
                "assignee_ids": [user.id],  # Сразу назначаем на себя
            }
        )

        return {
            "iid": issue.iid,
            "title": issue.title,
            "project_id": project.id,
            "web_url": issue.web_url,
        }

    # ==================== РАБОТА С MERGE REQUESTS ====================

    def create_merge_request(
        self,
        source_branch: str,
        title: str,
        description: str = "",
        target_branch: str | None = None,
        assignee_id: int | None = None,
        project_id: int | None = None,
    ) -> dict:
        """Создаёт Merge Request"""
        project = self.get_project_by_id(project_id) if project_id else self.get_project()
        target = target_branch or (project.default_branch if project_id else self.default_branch)

        # Проверяем, существует ли исходная ветка
        if not self.branch_exists(source_branch, project_id=project_id):
            raise ValueError(f"Ветка {source_branch} не найдена")

        # Создаем MR
        mr_data = {
            "source_branch": source_branch,
            "target_branch": target,
            "title": title,
            "description": description,
            "remove_source_branch": True,  # Удалять ветку после слияния
        }

        if assignee_id:
            mr_data["assignee_id"] = assignee_id

        try:
            mr = project.mergerequests.create(mr_data)
            return {
                "iid": mr.iid,
                "title": mr.title,
                "web_url": mr.web_url,
                "state": mr.state,
            }
        except gitlab.exceptions.GitlabCreateError as e:
            # Если MR уже существует, вернем ошибку или найдем существующий
            if "already exists" in str(e):
                raise ValueError("Merge Request для этой ветки уже существует")
            raise e


# Глобальный экземпляр
gitlab_client = GitLabAdapter()
