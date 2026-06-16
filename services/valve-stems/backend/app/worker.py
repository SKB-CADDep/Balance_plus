"""
Фоновый исполнитель задач (Celery Worker) для расчетного микросервиса.

Отвечает за асинхронное выполнение "тяжелого" математического ядра.
Позволяет разгрузить основной поток FastAPI: HTTP-запрос быстро возвращает 
пользователю `Task ID`, а сам процесс расчета идет в изолированном процессе (Worker), 
сообщая о статусе через брокер сообщений (RabbitMQ / Redis).
"""

import logging
from app.core.celery_app import celery_app
from app.core.database import SessionLocal

# Импорты схем и адаптера
from app.schemas.calculation import MultiCalculationParams
from app.schemas.valve import ValveInfo  # Убедись, что путь импорта схемы ValveInfo правильный
from app.crud.valves import get_valve_by_id
from app.adapters.calculation_adapter import CalculationAdapter

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def calculate_valve_stems_async(self, payload: dict):
    """
    Фоновая задача для расчета параметров работы (утечек) штоков клапанов.

    [ENGINEERING CONTEXT]
    Почему здесь открывается новая независимая сессия к БД (`SessionLocal`):
    Воркеры Celery работают в отдельных процессах (ОС), которые не имеют доступа 
    к HTTP-контексту FastAPI и зависимости `get_db()`. Поэтому воркер обязан 
    самостоятельно открыть соединение с БД и, что еще важнее, самостоятельно 
    закрыть его в блоке `finally: db.close()`, чтобы не исчерпать пул соединений (Connection Pool).

    Args:
        payload (dict): Сериализованный словарь с входными параметрами от пользователя 
            (соответствующий Pydantic-модели MultiCalculationParams).

    Returns:
        dict: Статус выполнения ("success" / "error") и сериализованный результат 
            математического расчета (или текст ошибки).
    """
    task_id = self.request.id
    logger.info(f"Начат асинхронный расчет штоков клапанов. Task ID: {task_id}")
    
    # Открываем независимую сессию к БД для воркера
    db = SessionLocal()
    try:
        # 1. Парсим входящий JSON в главную Pydantic модель
        calc_input = MultiCalculationParams(**payload)
        
        # 2. Подготавливаем данные по группам
        groups_data = []
        for group in calc_input.groups:
            # Вытягиваем SQLAlchemy-модель из базы
            db_valve = get_valve_by_id(db, group.valve_id)
            
            # [ENGINEERING CONTEXT]
            # Конвертируем SQLAlchemy-модель в Pydantic-схему ValveInfo, 
            # так как адаптер (CalculationAdapter) ждет именно её.
            # (Используем model_validate для Pydantic v2 или from_orm для v1)
            valve_info = ValveInfo.model_validate(db_valve)
            
            # Собираем кортеж (ValveGroupInput, ValveInfo) как просит адаптер
            groups_data.append((group, valve_info))

        # 3. Запускаем тяжелое математическое ядро
        adapter = CalculationAdapter()
        result = adapter.run_multi_calculation(
            globals_data=calc_input.globals,
            groups_data=groups_data
        )
        
        logger.info(f"Расчет штоков успешно завершен. Task ID: {task_id}")
        
        # 4. Возвращаем результат (сериализуем Pydantic модель в словарь)
        return {
            "status": "success",
            "result": result.model_dump()
        }
        
    except Exception as e:
        # [ENGINEERING CONTEXT]
        # Тот самый золотой стандарт: exc_info=True покажет нам идеальный Traceback!
        # В фоновых воркерах нет терминала разработчика, поэтому если математическое 
        # ядро упадет, мы увидим всю цепочку вызовов (Stack Trace) прямо в логах Kibana/ELK.
        logger.error(f"Ошибка при расчете Task ID {task_id}: {str(e)}", exc_info=True)
        return {
            "status": "error", 
            "error_type": type(e).__name__, 
            "message": str(e)
        }
    finally:
        db.close()
        