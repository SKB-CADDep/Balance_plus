import pytest

from app.core.config import Settings


POSTGRES_ENV_KEYS = (
    "DATABASE_URL",
    "POSTGRES_SERVER",
    "POSTGRES_PORT",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
)


def clear_database_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in POSTGRES_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_database_uri_is_built_from_postgres_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_database_env(monkeypatch)
    monkeypatch.setenv(
        "POSTGRES_SERVER", "postgres-postgresql.postgres.svc.cluster.local"
    )
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_USER", "condenser")
    monkeypatch.setenv("POSTGRES_PASSWORD", "super-secret-password")
    monkeypatch.setenv("POSTGRES_DB", "condenser_calculator")

    settings = Settings(_env_file=None)

    assert settings.SQLALCHEMY_DATABASE_URI == (
        "postgresql+psycopg://condenser:super-secret-password@"
        "postgres-postgresql.postgres.svc.cluster.local:5432/condenser_calculator"
    )


def test_database_url_takes_priority_over_postgres_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_database_env(monkeypatch)
    monkeypatch.setenv("POSTGRES_SERVER", "ignored-host")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://explicit:secret@database.example:5433/explicit_db",
    )

    settings = Settings(_env_file=None)

    assert settings.SQLALCHEMY_DATABASE_URI == (
        "postgresql+psycopg://explicit:secret@database.example:5433/explicit_db"
    )


def test_database_uri_escapes_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_database_env(monkeypatch)
    monkeypatch.setenv("POSTGRES_USER", "service-user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss/word")

    settings = Settings(_env_file=None)

    assert "service-user:p%40ss%2Fword@db:5432/condenser_calc" in (
        settings.SQLALCHEMY_DATABASE_URI
    )
