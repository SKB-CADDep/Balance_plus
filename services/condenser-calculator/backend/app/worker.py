"""
Модуль фоновых задач (Workers) для выполнения ресурсоемких вычислений.

Использует Celery для запуска математического ядра вне основного HTTP-цикла (FastAPI).
Позволяет обрабатывать массивные расчеты асинхронно, предотвращая тайм-ауты 
сетевых соединений и зависание клиентского приложения (фронтенда).
"""

import logging
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.condenser import Condenser
from app.models.material import Material
from app.schemas.calculation import CalculationInput
from app.adapters.calculation_adapter import CondenserCalculationAdapter

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def calculate_async_task(self, payload: dict):
    """
    Выполняет полный цикл расчета конденсатора в фоновом процессе.

    Поскольку задача выполняется вне контекста FastAPI, она самостоятельно 
    управляет жизненным циклом подключения к базе данных.

    Args:
        self (celery.app.task.Task): Экземпляр задачи Celery (доступен благодаря bind=True).
            Позволяет получать метаданные, такие как ID текущей задачи.
        payload (dict): Сериализованные входные данные для расчета 
            (соответствуют схеме CalculationInput).

    Returns:
        dict: Унифицированный словарь с результатами. 
            При успехе содержит {"status": "success", "result": <данные>}.
            При ошибке содержит {"status": "error", "error_type": <тип>, "message": <текст>}.
    """
    task_id = self.request.id
    logger.info(f"Начат асинхронный расчет конденсатора. Task ID: {task_id}")
    
    # Воркер выполняется в изолированном процессе, поэтому Dependency Injection (get_db) недоступен.
    # Открываем независимую сессию базы данных вручную.
    db = SessionLocal()
    try:
        # 1. Парсим входящий JSON обратно в валидированную Pydantic модель
        calc_input = CalculationInput(**payload)
        
        # 2. Загружаем геометрию конденсатора из базы данных
        condenser = db.query(Condenser).filter(Condenser.id == calc_input.condenser_id).first()
        
        if not condenser:
            return {
                "status": "error", 
                "error_type": "EntityNotFound", 
                "message": f"Конденсатор (ID {calc_input.condenser_id}) не найден в БД"
            }

        # Бизнес-правило: Определение материала трубок (Many-to-Many).
        # Если клиент передал конкретный материал — используем его. 
        # Если материал не передан, извлекаем первый доступный (по умолчанию) из связей конденсатора.
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
            
        # 3. Инициализируем адаптер и запускаем тяжелый физический расчет
        adapter = CondenserCalculationAdapter()
        result = adapter.calculate(calc_input, condenser, material)
        
        logger.info(f"Расчет успешно завершен. Task ID: {task_id}")
        
        # 4. Возвращаем результат в формате, который ожидает эндпоинт статуса (get_task_status)
        return {
            "status": "success",
            "result": result.model_dump()
        }
        
    except Exception as e:
        # Отлов всех непредвиденных математических или системных сбоев
        logger.error(f"Ошибка при расчете Task ID {task_id}: {str(e)}", exc_info=True)
        return {
            "status": "error", 
            "error_type": type(e).__name__, 
            "message": str(e)
        }
    finally:
        # Критически важный блок: гарантия освобождения пула соединений БД
        # даже при возникновении фатальной ошибки (Exception) внутри try.
        db.close()
        