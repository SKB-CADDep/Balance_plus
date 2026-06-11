from fastapi import APIRouter, status
from app.schemas.balance import CalculationInput, CalculationOutput, ReportStatus

router = APIRouter(prefix="/api/v1/balance", tags=["Balance Calculation"])

@router.post(
    "/calculate",
    response_model=CalculationOutput,
    status_code=status.HTTP_200_OK,
    summary="Запуск термодинамического расчета баланса",
    description=(
        "Синхронный эндпоинт для расчета баланса турбины. "
        "Принимает граф схемы (узлы и связи) и параметры режима. "
        "Выполняет итеративный расчет и возвращает обновленные состояния графа и метрики сходимости."
    )
)
async def calculate_balance(payload: CalculationInput) -> CalculationOutput:
    """
    Заглушка для генерации OpenAPI схемы.
    В будущем здесь будет вызов чистой функции из пакета balance-core-math:
    result = run_balance_solver(payload)
    """
    # Моковый ответ для Swagger UI и тестирования контракта фронтендом
    return CalculationOutput(
        status=ReportStatus.CONVERGED,
        trace_events=[
            "solver: start", 
            "init_nominal_scale: pkp1 = 1.000000",
            "solver: converged at iteration 15"
        ],
        metrics=[],
        nodes_result=[],
        links_result=[],
        warnings=["Бизнес-логика пока не подключена. Возвращен мок."],
        errors=[]
    )