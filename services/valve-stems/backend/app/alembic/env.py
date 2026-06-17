"""
Конфигурационное окружение Alembic для применения миграций базы данных.

[ENGINEERING CONTEXT]
Внимание: В данном проекте (экосистема Balance+ IDE) используется гибридный подход к БД.
Из-за наличия сложной предметной области и огромных эталонных справочников (материалы, геометрии),
ПЕРВИЧНАЯ инициализация пустой базы данных через `alembic upgrade head` СТРОГО ЗАПРЕЩЕНА.

База данных должна разворачиваться исключительно из SQL-дампа (например, `init.dump`).
Alembic используется здесь ТОЛЬКО для инкрементальных (последующих) изменений схемы БД
поверх уже восстановленного дампа.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base


# Доступ к конфигурации alembic.ini
config = context.config

# Настройка логирования на основе файла alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные моделей SQLAlchemy для автогенерации миграций (autogenerate)
target_metadata = Base.metadata


def get_url() -> str:
    """
    Получает строку подключения к БД из глобальных настроек приложения (Pydantic Settings).

    Returns:
        str: DSN строка подключения к PostgreSQL.
    """
    return str(settings.SQLALCHEMY_DATABASE_URI)


def run_migrations_offline() -> None:
    """
    Запускает миграции в 'offline' режиме.

    В этом режиме контекст конфигурируется только с использованием URL,
    без создания полноценного объекта Engine. Это позволяет не устанавливать 
    физическое соединение с базой данных (DBAPI не требуется).

    Вместо реального изменения таблиц, вызовы `context.execute()` генерируют 
    чистый SQL-скрипт, который выводится в стандартный поток вывода (stdout).
    Используется для генерации SQL-файлов миграций.
    """
    url = get_url()
    context.configure(
        url=url, 
        target_metadata=target_metadata, 
        literal_binds=True, 
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Запускает миграции в 'online' режиме.

    В этом сценарии создается полноценный объект SQLAlchemy Engine, 
    который устанавливает физическое соединение с базой данных.
    
    [ENGINEERING CONTEXT]
    Используется `poolclass=pool.NullPool`. Это сделано специально для скрипта миграций, 
    чтобы не держать соединения открытыми (connection pooling не нужен для одноразовой CLI-команды).
    Миграции применяются внутри единой транзакции (begin_transaction), что гарантирует 
    откат (rollback) в случае ошибки на любом из шагов.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata, 
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


# Определение режима запуска на основе аргументов командной строки Alembic
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
    