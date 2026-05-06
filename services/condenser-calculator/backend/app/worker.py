import time
import logging
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="calculate_async_task")
def calculate_async_task(self, input_data: dict):
    """
    PoC асинхронной задачи.
    В будущем здесь будет распаковка JSON и вызов CondenserCalculationAdapter.
    """
    logger.info(f"Начат асинхронный расчет. Task ID: {self.request.id}")
    
    # Имитируем тяжелый расчет (5 секунд)
    time.sleep(5)
    
    logger.info(f"Расчет завершен. Task ID: {self.request.id}")
    
    return {
        "status": "success",
        "message": "Расчет выполнен успешно",
        "processed_data": input_data
    }