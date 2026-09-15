from app.core.config import Settings


def test_development_environment_is_supported() -> None:
    settings = Settings(ENVIRONMENT="development")

    assert settings.ENVIRONMENT == "development"


def test_celery_redis_url_is_built_from_separate_settings() -> None:
    settings = Settings(
        REDIS_HOST="redis.internal",
        REDIS_PORT=6380,
        REDIS_PASSWORD="pa:ss@word",
        REDIS_DB=2,
    )

    assert (
        settings.CELERY_REDIS_URL
        == "redis://:pa%3Ass%40word@redis.internal:6380/2"
    )


def test_explicit_redis_url_has_priority() -> None:
    settings = Settings(
        REDIS_URL="redis://:legacy@old-redis:6379/4",
        REDIS_HOST="ignored",
        REDIS_PORT=6380,
        REDIS_PASSWORD="ignored",
        REDIS_DB=2,
    )

    assert settings.CELERY_REDIS_URL == "redis://:legacy@old-redis:6379/4"
