"""
Модуль фоновых задач (Celery Workers) микросервиса Condenser Calculator.

Содержит "тяжелые" вычислительные задачи, которые выполняются асинхронно
вне цикла событий (Event Loop) FastAPI. Это позволяет не блокировать API
и возвращать пользователю task_id для последующего поллинга (polling) статуса.
"""
import logging
from typing import Dict, Any

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.condenser import Condenser
from app.models.material import Material
from app.schemas.calculation import CalculationInput
from app.adapters.calculation_adapter import CondenserCalculationAdapter

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def calculate_async_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Выполняет полный цикл физического расчета конденсатора в фоне.

    Аргументы передаются в виде словаря (dict), а не Pydantic-модели, 
    так как брокер сообщений Celery (Redis/RabbitMQ) сериализует задачи 
    в JSON, который не поддерживает сложные Python-объекты.

    Args:
        self: Экземпляр задачи Celery (доступен благодаря bind=True).
        payload (Dict[str, Any]): Сериализованный объект CalculationInput.

    Returns:
        Dict[str, Any]: Стандартный контракт ответа. Содержит ключ 'status' 
        ('success' или 'error') и либо результаты расчета ('result'), либо 
        информацию об ошибке ('error_type', 'message').
    """
    task_id = self.request.id
    logger.info("Начат асинхронный расчет конденсатора", extra={"task_id": task_id})
    
    # Воркеры Celery работают в отдельных процессах (или потоках),
    # у них нет доступа к Dependency Injection FastAPI (Depends(get_db)).
    # Поэтому каждый воркер обязан самостоятельно управлять жизненным циклом сессии.
    db = SessionLocal()
    try:
        # Восстанавливаем строгую типизацию и валидацию данных из "сырого" словаря
        calc_input = CalculationInput(**payload)
        
        condenser = db.query(Condenser).filter(Condenser.id == calc_input.condenser_id).first()
        if not condenser:
            return {
                "status": "error", 
                "error_type": "EntityNotFound", 
                "message": f"Конденсатор (ID {calc_input.condenser_id}) не найден в БД"
            }

        # Резолвинг материала (связь Many-to-Many).
        # Алгоритм: если клиент явно передал material_id — используем его.
        # Иначе используем механизм Fallback и берем первый привязанный материал по умолчанию.
        material = None
        requested_material_id = getattr(calc_input, 'material_id', None)
        
        if requested_material_id:
            material = db.query(Material).filter(Material.id == requested_material_id).first()
        elif condenser.materials:
            material = condenser.materials[0]

        if not material:
            return {
                "status": "error", 
                "error_type": "EntityNotFound", 
                "message": f"Не удалось определить материал для конденсатора (ID {condenser.id})"
            }
            
        # Запуск расчетного ядра через паттерн Адаптер
        adapter = CondenserCalculationAdapter()
        result = adapter.calculate(calc_input, condenser, material)
        
        logger.info("Расчет успешно завершен", extra={"task_id": task_id})
        
        return {
            "status": "success",
            "result": result.model_dump()
        }
        
    except Exception as e:
        # Ловим все исключения (вкл. CalculationEngineError), чтобы воркер
        # не упал тихо (Silent Failure), а вернул статус ошибки в брокер.
        logger.exception("Ошибка при выполнении фонового расчета", extra={"task_id": task_id})
        return {
            "status": "error", 
            "error_type": type(e).__name__, 
            "message": str(e)
        }
    finally:
        # Гарантируем возврат соединения в пул, чтобы воркер не "повесил" базу
        db.close()