from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Condenser Calculator API"
    API_V1_STR: str = "/api/v1"

    # Теперь Pydantic будет искать DATABASE_URL в окружении.
    # Если не найдет - соберет дефолтную строку.
    SQLALCHEMY_DATABASE_URI: str = Field(
        default="postgresql+psycopg://condenser:password@db:5432/condenser_calc",
        validation_alias="DATABASE_URL",
    )

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


settings = Settings()
