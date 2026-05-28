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
    Фоновая задача для расчета параметров работы штоков клапанов.
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
            
            # Конвертируем её в Pydantic схему ValveInfo, так как адаптер ждет именно её
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
        # Тот самый золотой стандарт: exc_info=True покажет нам идеальный Traceback!
        logger.error(f"Ошибка при расчете Task ID {task_id}: {str(e)}", exc_info=True)
        return {
            "status": "error", 
            "error_type": type(e).__name__, 
            "message": str(e)
        }
    finally:
        db.close()