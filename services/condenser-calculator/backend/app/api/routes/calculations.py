from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.schemas.calculation import CalculationInput, CalculationOutput
from app.models.condenser import Condenser
from app.models.material import Material
from app.adapters.calculation_adapter import CondenserCalculationAdapter
from app.core.condenser_validators import validate_condenser_for_method
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
adapter = CondenserCalculationAdapter()


@router.post("/", response_model=CalculationOutput)
def calculate_modes(
    payload: CalculationInput,
    db: Session = Depends(get_db)
):
    """
    Расчет матрицы режимов конденсатора.
    """
    # 1. Запрашиваем конденсатор
    condenser = db.query(Condenser).filter(
        Condenser.id == payload.condenser_id).first()
    if not condenser:
        raise HTTPException(
            status_code=404, detail=f"Конденсатор с ID {payload.condenser_id} не найден.")

    # 2. Запрашиваем материал
    material = db.query(Material).filter(
        Material.id == payload.material_id).first()
    if not material:
        raise HTTPException(
            status_code=404, detail=f"Материал с ID {payload.material_id} не найден.")

    # 3. Валидация BR-02
    try:
        validate_condenser_for_method(condenser, payload.method)
    except ValueError as e:
        logger.warning(f"Validation failed (BR-02): {e}")
        raise HTTPException(status_code=422, detail=str(e))

    # 4. Выполняем адаптер (Там же будут внедряться варнинги BR-06/07)
    try:
        result = adapter.calculate(
            input_data=payload,
            condenser=condenser,
            material=material
        )
        return result
    except Exception as e:
        logger.exception("Calculation error")
        raise HTTPException(status_code=500, detail=str(e))
