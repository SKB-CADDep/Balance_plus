from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Condenser Calculator API"
    API_V1_STR: str = "/api/v1"

    # Настройки подключения к PostgreSQL
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "condenser"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "condenser_calc"
    POSTGRES_PORT: int = 5432

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
