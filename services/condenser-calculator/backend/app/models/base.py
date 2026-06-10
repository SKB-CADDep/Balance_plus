"""
Базовый класс SQLAlchemy 2.0 для ORM-моделей.
"""
import re
from typing import Any
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """
    Базовый класс для всех ORM-моделей.
    Используется Alembic для metadata.
    """
    
    # Отключаем предупреждения MyPy о динамических атрибутах
    __name__: str
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Автоматическая генерация имени таблицы на основе названия класса.
        Преобразует CamelCase в snake_case.
        
        Пример: 
        class CondenserModel(Base) -> имя таблицы 'condenser_model'
        class User(Base) -> имя таблицы 'user'
        """
        # Логика преобразования CamelCase -> snake_case
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    def __repr__(self) -> str:
        """
        Универсальный магический метод для удобного логирования и дебага.
        Вместо <CondenserModel object at 0x...> в консоль выведется:
        <CondenserModel(id=1, name='Конденсатор 1')>
        """
        # Собираем все колонки и их значения
        columns = [
            f"{col.name}={getattr(self, col.name)!r}" 
            for col in self.__table__.columns
        ]
        return f"<{self.__class__.__name__}({', '.join(columns)})>"

    def to_dict(self) -> dict[str, Any]:
        """
        Полезный утилитный метод для быстрой конвертации ORM-модели в словарь.
        Удобно при передаче данных в Pydantic или JSON-ответ.
        """
        return {
            col.name: getattr(self, col.name)
            for col in self.__table__.columns
        }
        