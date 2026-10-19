from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    PROJECT_NAME: str = "Condenser Calculator API"
    API_V1_STR: str = "/api/v1"

    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "condenser"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "condenser_calc"

    # DATABASE_URL имеет приоритет, а при его отсутствии URL собирается из
    # POSTGRES_* — одинаково для API, Alembic, Docker Compose и Kubernetes.
    SQLALCHEMY_DATABASE_URI: str = Field(
        default="",
        validation_alias="DATABASE_URL",
    )

    def model_post_init(self, __context: object) -> None:
        if self.SQLALCHEMY_DATABASE_URI:
            return

        self.SQLALCHEMY_DATABASE_URI = URL.create(
            drivername="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


settings = Settings()
