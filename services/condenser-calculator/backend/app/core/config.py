"""
Конфигурация параметров окружения (Environment Settings) микросервиса.

Модуль использует библиотеку `pydantic-settings` для декларативного описания 
и строгой типизации переменных окружения. Настройки автоматически загружаются 
из системного окружения среды или из локального файла `.env`.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Глобальные настройки микросервиса condenser-calculator.

    Свойства класса автоматически маппятся (связываются) с переменными 
    окружения при запуске приложения. Если переменная отсутствует, 
    используется значение по умолчанию (`default`).
    """
    
    # Базовые настройки API
    PROJECT_NAME: str = "Condenser Calculator API"
    API_V1_STR: str = "/api/v1"

    # Строка подключения к базе данных PostgreSQL.
    # Если переменная окружения DATABASE_URL задана (например, в docker-compose.yml 
    # или Kubernetes ConfigMap), Pydantic использует её благодаря `validation_alias`. 
    # Если она не найдена, будет использована дефолтная строка для локальной разработки.
    SQLALCHEMY_DATABASE_URI: str = Field(
        default="postgresql+psycopg://condenser:password@db:5432/condenser_calc",
        validation_alias="DATABASE_URL" 
    )

    # Настройки поведения Pydantic:
    # env_file=".env" — попытаться прочитать переменные из файла (удобно при локальной разработке)
    # case_sensitive=True — строгая чувствительность к регистру переменных окружения
    # extra="ignore" — игнорировать лишние переменные в .env файле (не выбрасывать ошибку)
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

# Создание глобального синглтона настроек.
# Этот объект импортируется во все остальные модули проекта (например, в main.py и database.py).
settings = Settings()
