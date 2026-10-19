"""
Комплексные unit-тесты адаптера GitLabAdapter (ветки, коммиты, MR, файлы, задачи и обработка ошибок)
"""

from unittest.mock import MagicMock, patch

import gitlab.exceptions
import pytest

from app.core.gitlab_adapter import GitLabAdapter, GitLabConfigurationError


# ============================================================================
# 1. КОНФИГУРАЦИЯ И АВТОРИЗАЦИЯ (БАЗОВЫЕ ТЕСТЫ)
# ============================================================================
class TestGitLabAdapterConfiguration:
    def test_missing_configuration_is_reported_lazily(self) -> None:
        """Адаптер сообщает о неполной конфигурации только при обращении."""
        adapter = GitLabAdapter(url="", token="")
        assert adapter.configured is False
        assert adapter.connection_summary()["configured"] is False

        with pytest.raises(GitLabConfigurationError, match="GITLAB_URL"):
            adapter.check_connection()

    @patch("app.core.gitlab_adapter.gitlab.Gitlab")
    def test_client_uses_internal_gitlab_options(self, mock_gitlab: MagicMock) -> None:
        """Клиент gitlab.Gitlab создается с заданными параметрами таймаута и ssl."""
        adapter = GitLabAdapter(
            url="http://git.utz.local/",
            token="test-token",
            project_id=41,
            ssl_verify=False,
            timeout=7,
        )

        client = adapter.gl

        assert client is mock_gitlab.return_value
        mock_gitlab.assert_called_once_with(
            "http://git.utz.local",
            private_token="test-token",
            ssl_verify=False,
            timeout=7,
            retry_transient_errors=True,
        )

    def test_connection_check_returns_sanitized_diagnostics(self) -> None:
        """check_connection возвращает статус без раскрытия токена."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token")
        client = MagicMock()
        client.user.username = "engineer"
        adapter._gl = client

        result = adapter.check_connection()

        client.auth.assert_called_once_with()
        assert result["status"] == "ok"
        assert result["username"] == "engineer"
        assert "token" not in result


# ============================================================================
# 2. РАБОТА С ВЕТКАМИ (СОЗДАНИЕ, ПРОВЕРКА, УМНЫЙ ПОИСК ПО ISSUE IID)
# ============================================================================
class TestGitLabAdapterBranches:
    def test_create_branch_success(self) -> None:
        """Успешное создание новой ветки возвращает True."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token", project_id=1)
        project = MagicMock()
        project.default_branch = "main"
        project.branches.create.return_value = MagicMock()
        adapter.get_project_by_id = MagicMock(return_value=project)

        created = adapter.create_branch("issue/4-task", source_branch="main", project_id=1)

        assert created is True
        project.branches.create.assert_called_once_with({"branch": "issue/4-task", "ref": "main"})

    def test_create_branch_already_exists_returns_false(self) -> None:
        """Если ветка уже существует, метод возвращает False без падения."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token", project_id=1)
        project = MagicMock()
        project.default_branch = "main"
        project.branches.create.side_effect = gitlab.exceptions.GitlabCreateError("Branch already exists")
        adapter.get_project_by_id = MagicMock(return_value=project)

        created = adapter.create_branch("issue/4-existing", source_branch="main", project_id=1)

        assert created is False

    def test_create_branch_unexpected_error_raises(self) -> None:
        """При непредвиденной ошибке GitLabCreateError метод пробрасывает исключение."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token", project_id=1)
        project = MagicMock()
        project.default_branch = "main"
        project.branches.create.side_effect = gitlab.exceptions.GitlabCreateError("500 Internal Error")
        adapter.get_project_by_id = MagicMock(return_value=project)

        with pytest.raises(gitlab.exceptions.GitlabCreateError):
            adapter.create_branch("issue/4-fail", project_id=1)

    def test_branch_exists_true_and_false(self) -> None:
        """Проверка существования ветки (True при наличии, False при GitlabGetError)."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token", project_id=1)
        project = MagicMock()
        adapter.get_project_by_id = MagicMock(return_value=project)

        # 1. Ветка существует
        project.branches.get.return_value = MagicMock()
        assert adapter.branch_exists("main", project_id=1) is True

        # 2. Ветка не найдена (404)
        project.branches.get.side_effect = gitlab.exceptions.GitlabGetError("404 Not Found")
        assert adapter.branch_exists("non-existent-branch", project_id=1) is False

    def test_find_branch_by_issue_iid_matches_naming_conventions(self) -> None:
        """Умный поиск ветки находит форматы: '4-name', 'issue/4-name', '4'."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token", project_id=1)
        project = MagicMock()
        adapter.get_project_by_id = MagicMock(return_value=project)

        b1 = MagicMock()
        b1.name = "issue/42-calculate-flow"
        b2 = MagicMock()
        b2.name = "other-branch"
        project.branches.list.return_value = [b2, b1]

        found = adapter.find_branch_by_issue_iid(issue_iid=42, project_id=1)
        assert found == "issue/42-calculate-flow"

    def test_find_branch_by_issue_iid_returns_none_when_no_match(self) -> None:
        """Если ни одна ветка не совпала по номеру задачи, возвращается None."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token", project_id=1)
        project = MagicMock()
        adapter.get_project_by_id = MagicMock(return_value=project)

        project.branches.list.return_value = []
        assert adapter.find_branch_by_issue_iid(issue_iid=99, project_id=1) is None


# ============================================================================
# 3. РАБОТА С КОММИТАМИ И ФАЙЛАМИ
# ============================================================================
class TestGitLabAdapterFilesAndCommits:
    def test_create_commit_determines_create_vs_update_action(self) -> None:
        """Метод create_commit ставит action='create', если файл новый, и 'update', если существует."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token", project_id=1)
        project = MagicMock()
        project.default_branch = "main"
        project.commits.create.return_value = MagicMock(id="sha-12345")
        adapter.get_project_by_id = MagicMock(return_value=project)

        # 1. Файл не существует -> action 'create'
        adapter.file_exists = MagicMock(return_value=False)
        adapter.create_commit("new.json", "{}", "Initial commit", branch="main", project_id=1)

        call_data = project.commits.create.call_args[0][0]
        assert call_data["actions"][0]["action"] == "create"

        # 2. Файл существует -> action 'update'
        adapter.file_exists = MagicMock(return_value=True)
        adapter.create_commit("new.json", "{}", "Update commit", branch="main", project_id=1)

        call_data_update = project.commits.create.call_args[0][0]
        assert call_data_update["actions"][0]["action"] == "update"

    def test_create_commit_multiple_packages_all_files(self) -> None:
        """create_commit_multiple упаковывает несколько файлов в единый атомарный коммит."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token", project_id=1)
        project = MagicMock()
        project.default_branch = "main"
        adapter.get_project_by_id = MagicMock(return_value=project)
        adapter.file_exists = MagicMock(return_value=False)

        files = {"file1.txt": "content1", "file2.txt": "content2"}
        adapter.create_commit_multiple(files, "Batch commit", branch="main", project_id=1)

        call_data = project.commits.create.call_args[0][0]
        assert len(call_data["actions"]) == 2
        assert call_data["actions"][0]["file_path"] == "file1.txt"
        assert call_data["actions"][1]["file_path"] == "file2.txt"

    def test_get_file_content_decoded_returns_string_or_none(self) -> None:
        """Чтение и декодирование файла из репозитория."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token", project_id=1)
        project = MagicMock()
        project.default_branch = "main"
        adapter.get_project_by_id = MagicMock(return_value=project)

        # 1. Успешное чтение
        mock_file = MagicMock()
        mock_file.decode.return_value = b'{"status": "ok"}'
        project.files.get.return_value = mock_file

        content = adapter.get_file_content_decoded("config.json", ref="main", project_id=1)
        assert content == '{"status": "ok"}'

        # 2. Ошибка чтения (файл не найден) -> None
        project.files.get.side_effect = gitlab.exceptions.GitlabGetError("404 Not Found")
        assert adapter.get_file_content_decoded("missing.json", ref="main", project_id=1) is None


# ============================================================================
# 4. РАБОТА С MERGE REQUESTS
# ============================================================================
class TestGitLabAdapterMergeRequests:
    def test_create_merge_request_success(self) -> None:
        """Успешное создание Merge Request с возвратом iid и web_url."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token", project_id=1)
        project = MagicMock()
        project.default_branch = "main"
        adapter.get_project_by_id = MagicMock(return_value=project)
        adapter.branch_exists = MagicMock(return_value=True)

        mock_mr = MagicMock()
        mock_mr.iid = 7
        mock_mr.title = "Draft MR"
        mock_mr.web_url = "http://git.utz.local/project/-/merge_requests/7"
        mock_mr.state = "opened"
        project.mergerequests.create.return_value = mock_mr

        result = adapter.create_merge_request(
            source_branch="issue/4-task",
            title="Draft MR",
            assignee_id=42,
            project_id=1,
        )

        assert result["iid"] == 7
        assert result["web_url"] == "http://git.utz.local/project/-/merge_requests/7"
        project.mergerequests.create.assert_called_once()
        call_kwargs = project.mergerequests.create.call_args[0][0]
        assert call_kwargs["source_branch"] == "issue/4-task"
        assert call_kwargs["target_branch"] == "main"
        assert call_kwargs["assignee_id"] == 42
        assert call_kwargs["remove_source_branch"] is True

    def test_create_merge_request_raises_value_error_if_source_branch_missing(self) -> None:
        """Если исходная ветка не существует, создание MR прерывается ошибкой ValueError."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token", project_id=1)
        project = MagicMock()
        project.default_branch = "main"
        adapter.get_project_by_id = MagicMock(return_value=project)
        adapter.branch_exists = MagicMock(return_value=False)

        with pytest.raises(ValueError, match="не найдена"):
            adapter.create_merge_request("missing-branch", "Title", project_id=1)

    def test_create_merge_request_raises_value_error_if_already_exists(self) -> None:
        """Если MR для этой ветки уже открыт, возвращается понятная ошибка ValueError."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token", project_id=1)
        project = MagicMock()
        project.default_branch = "main"
        adapter.get_project_by_id = MagicMock(return_value=project)
        adapter.branch_exists = MagicMock(return_value=True)

        project.mergerequests.create.side_effect = gitlab.exceptions.GitlabCreateError("MR already exists")

        with pytest.raises(ValueError, match="уже существует"):
            adapter.create_merge_request("existing-branch", "Title", project_id=1)


# ============================================================================
# 5. РАБОТА С ЗАДАЧАМИ (ISSUES)
# ============================================================================
class TestGitLabAdapterIssues:
    def test_project_filter_is_used_for_assigned_issues(self) -> None:
        """Фильтрация назначенных задач в проекте."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token")
        client = MagicMock()
        client.user.id = 17
        adapter._gl = client

        project = MagicMock()
        project.id = 41
        project.name = "Factory project"
        issue = MagicMock()
        issue.iid = 5
        issue.project_id = 41
        issue.title = "Calculation"
        issue.description = None
        issue.state = "opened"
        issue.labels = []
        issue.assignee = {"username": "engineer"}
        issue.created_at = "2026-08-19T00:00:00Z"
        issue.due_date = None
        issue.web_url = "http://git.utz.local/project/-/issues/5"
        project.issues.list.return_value = [issue]
        adapter.get_project_by_id = MagicMock(return_value=project)

        result = adapter.get_all_assigned_issues(state="opened", project_id=41)

        project.issues.list.assert_called_once_with(
            assignee_id=17,
            state="opened",
            get_all=True,
        )
        assert result[0]["project_id"] == 41
        assert result[0]["project_name"] == "Factory project"

    def test_create_issue_success(self) -> None:
        """Создание задачи возвращает словарь с iid, title и web_url."""
        adapter = GitLabAdapter(url="http://git.utz.local", token="test-token", project_id=1)
        client = MagicMock()
        client.user.id = 17
        adapter._gl = client

        project = MagicMock()
        project.id = 1
        adapter.get_project_by_id = MagicMock(return_value=project)

        mock_issue = MagicMock()
        mock_issue.iid = 12
        mock_issue.title = "Новая расчетная задача"
        mock_issue.web_url = "http://git.utz.local/project/-/issues/12"
        project.issues.create.return_value = mock_issue

        result = adapter.create_issue("Новая расчетная задача", "Описание", labels=["calc"], project_id=1)

        assert result["iid"] == 12
        assert result["title"] == "Новая расчетная задача"
        assert result["web_url"] == "http://git.utz.local/project/-/issues/12"