"""
Конфигурационное окружение Alembic для микросервиса condenser-calculator.

[ENGINEERING CONTEXT]
Внимание: В данном проекте используется гибридный подход к БД.
ПЕРВИЧНАЯ инициализация пустой базы данных через `alembic upgrade head` СТРОГО ЗАПРЕЩЕНА,
так как эталонные справочники оборудования и теплофизических свойств 
(модели Condenser, Material) разворачиваются исключительно из подготовленных SQL-дампов.

Alembic используется в этом микросервисе ТОЛЬКО для инкрементальных (последующих) 
изменений схемы поверх уже восстановленной базы данных.
"""

import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from os.path import dirname, abspath


from app.core.config import settings


from app.models.base import Base
# Явный импорт моделей необходим, чтобы Alembic добавил их в target_metadata
# и смог генерировать миграции (autogenerate) на основе изменений в коде.
from app.models.material import Material
from app.models.condenser import Condenser

config = context.config

# Динамическая подстановка URL базы данных из Pydantic настроек
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Запускает миграции в 'offline' режиме.

    Конфигурирует контекст только с использованием URL, без создания пула соединений (Engine).
    Позволяет генерировать SQL-скрипты миграций без физического подключения к БД (DBAPI не требуется).
    Все SQL-выражения перехватываются и выводятся в стандартный поток вывода (stdout).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Запускает миграции в 'online' режиме (с подключением к БД).

    Создает объект Engine и связывает реальное соединение с контекстом Alembic
    для физического изменения таблиц в PostgreSQL.

    [ENGINEERING CONTEXT]
    Оптимизация пула соединений: используется `poolclass=pool.NullPool`. 
    Это предотвращает создание висящего пула соединений для короткоживущего 
    CLI-скрипта миграций. Без этой настройки скрипт может "зависнуть" 
    при выполнении автоматических пайплайнов в CI/CD (GitHub Actions/GitLab CI).
    Флаг `compare_type=True` заставляет Alembic отслеживать изменения 
    типов данных в колонках (например, Float -> Integer).
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
    