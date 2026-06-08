"""
Модуль для работы с базой данных (CRUD) в контексте истории расчетов.

Отвечает за сохранение логов вычислений: входных параметров (запросов) 
и полученных результатов (сгенерированных матриц) в БД. Это необходимо 
для последующего аудита, аналитики или загрузки истории на фронтенде.
"""

import logging
from sqlalchemy.orm import Session

from app.models.calculation_result import CalculationResult

logger = logging.getLogger(__name__)


def save_calculation_result(
    db: Session,
    condenser_id: int,
    input_data: dict,
    output_data: dict,
    method: str,
) -> CalculationResult:
    """
    Сохраняет результаты расчета и исходные параметры в базу данных.

    Создает новую запись в таблице истории расчетов. Сериализованные входные данные 
    и сгенерированные матрицы сохраняются в JSON/JSONB колонки. Это позволяет 
    в будущем просмотреть историю или воспроизвести расчет без повторного 
    вызова математического ядра.

    Args:
        db (Session): Активная сессия подключения к базе данных SQLAlchemy.
        condenser_id (int): Идентификатор конденсатора, для которого выполнялся расчет.
        input_data (dict): Исходные параметры запроса (Pydantic-модель, приведенная к словарю).
        output_data (dict): Результаты расчета (матрицы, эжекторы, время выполнения).
        method (str): Использованная методика расчета (например, 'berman' или 'metro-vickers').

    Returns:
        CalculationResult: Созданный ORM-объект записи с присвоенным базой данных первичным ключом (id).
    """
    logger.info(
        "DB: saving calculation result", 
        extra={"condenser_id": condenser_id, "method": method}
    )
    
    # Формируем ORM-объект перед записью в БД
    result = CalculationResult(
        condenser_id=condenser_id,
        input_data=input_data,
        output_data=output_data,
        method=method
    )
    
    db.add(result)
    
    # Фиксируем транзакцию (сохраняем физически)
    db.commit()
    # Обновляем объект, чтобы подтянуть сгенерированный базой данных ID и другие дефолтные поля (например, timestamp)
    db.refresh(result)
    
    logger.info(
        "DB: calculation result saved successfully", 
        extra={"calculation_id": result.id, "condenser_id": condenser_id}
    )
    
    return result