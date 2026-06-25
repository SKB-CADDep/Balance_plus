"""
Модуль конфигурации приложения (Pydantic Settings).

Отвечает за загрузку переменных окружения из .env файлов и системного окружения,
их строгую типизацию и валидацию перед запуском сервиса 'Valve Stems'.
"""

from typing import Annotated, Any, Literal
from urllib.parse import quote_plus

from pydantic import (
    AnyUrl,
    BeforeValidator,
    computed_field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    """
    Парсер для списка разрешенных CORS-доменов.
    Преобразует строку (например, "http://localhost,http://test") в список строк.
    """
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    """
    Глобальные настройки приложения.
    Значения по умолчанию могут быть переопределены переменными окружения 
    или через файл, указанный в env_file.
    """
    
    # WARNING (Архитектурный долг):
    # Жесткая привязка к .env.local может вызвать предупреждения в CI/CD (production среде),
    # если этот файл отсутствует. Обычно используют env_file=".env" или передают динамически.
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding='utf-8',
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"

    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    # WARNING (MyPy / Статический анализатор):
    # Функция parse_cors возвращает list[str] | str, но аннотация здесь ожидает list[AnyUrl] | str.
    # Во время выполнения Pydantic V2 автоматически скастит строки в валидные AnyUrl, 
    # но строгие линтеры кода могут выдать ошибку несоответствия типов.
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    PROJECT_NAME: str = "WSAPropertiesCalculator"

    # Настройки PostgreSQL (значения по умолчанию, будут переопределены из .env)
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "postgres"

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> MultiHostUrl:
        """
        Автоматически собирает URI для подключения к БД на основе заданных параметров.
        Использует современный драйвер psycopg (psycopg3) для SQLAlchemy 2.0.
        """
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=quote_plus(self.POSTGRES_PASSWORD),
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )


settings = Settings()
