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
    Реальная фоновая задача для расчета конденсатора.
    """
    task_id = self.request.id
    logger.info(f"Начат асинхронный расчет конденсатора. Task ID: {task_id}")
    
    # Воркер сам открывает сессию к БД
    db = SessionLocal()
    try:
        # 1. Парсим входящий JSON обратно в Pydantic модель
        calc_input = CalculationInput(**payload)
        
        # 2. Достаем конденсатор
        condenser = db.query(Condenser).filter(Condenser.id == calc_input.condenser_id).first()
        
        if not condenser:
            return {
                "status": "error", 
                "error_type": "EntityNotFound", 
                "message": f"Конденсатор (ID {calc_input.condenser_id}) не найден в БД"
            }

        # --- НОВАЯ ЛОГИКА MANY-TO-MANY ДЛЯ МАТЕРИАЛОВ ---
        material = None
        # Проверяем, передал ли клиент конкретный ID материала (через getattr на случай, если поле станет опциональным)
        requested_material_id = getattr(calc_input, 'material_id', None)
        
        if requested_material_id:
            # Ищем конкретный материал, который запросил пользователь
            material = db.query(Material).filter(Material.id == requested_material_id).first()
        elif condenser.materials:
            # Если не запросил, берем первый доступный (дефолтный для этого конденсатора)
            material = condenser.materials[0]

        if not material:
            return {
                "status": "error", 
                "error_type": "EntityNotFound", 
                "message": f"Не удалось определить материал для конденсатора (ID {condenser.id})"
            }
            
        # 3. Запускаем тяжелый физический расчет
        adapter = CondenserCalculationAdapter()
        result = adapter.calculate(calc_input, condenser, material)
        
        logger.info(f"Расчет успешно завершен. Task ID: {task_id}")
        
        # 4. Возвращаем результат в формате, утвержденном в контракте
        return {
            "status": "success",
            "result": result.model_dump()
        }
        
    except Exception as e:
        logger.error(f"Ошибка при расчете Task ID {task_id}: {str(e)}", exc_info=True)
        return {
            "status": "error", 
            "error_type": type(e).__name__, 
            "message": str(e)
        }
    finally:
        db.close()