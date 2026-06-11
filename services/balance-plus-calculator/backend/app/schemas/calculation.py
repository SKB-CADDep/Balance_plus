from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum

class ReportStatus(str, Enum):
    CONVERGED = "CONVERGED"
    NOT_CONVERGED = "NOT_CONVERGED"
    ERROR = "ERROR"
    VALIDATION_FAILED = "VALIDATION_FAILED"

class SolverSettings(BaseModel):
    max_iter: int = Field(50, description="Максимальное количество итераций")
    dg_abs_tol: float = Field(0.001, description="Абсолютная погрешность сходимости по расходам")
    use_condenser: bool = Field(True, description="Включить расчет конденсатора")
    use_heaters: bool = Field(True, description="Включить расчет ПСГ")
    use_seals: bool = Field(True, description="Включить расчет уплотнений")

class NodeInput(BaseModel):
    index: int = Field(..., description="1-based индекс узла")
    name_u: str = Field(..., description="Пользовательское имя узла (NAMU)")
    IO: int = Field(..., description="Тип оборудования (1-расширение, 2-дроссель и т.д.)")
    IP: int = Field(0, description="Инструкция расчета давления")
    P: float = Field(0.0, description="Давление, кгс/см2")
    T: float = Field(0.0, description="Температура, °C")
    H: float = Field(0.0, description="Энтальпия, ккал/кг")
    G: float = Field(0.0, description="Расход, т/ч")
    AD: List[float] = Field(default_factory=list, description="Массив доп. параметров узла (AD1, AD2...)")

class LinkInput(BaseModel):
    index: int = Field(..., description="1-based индекс связи")
    node_from: int = Field(..., description="Индекс узла источника")
    node_to: int = Field(..., description="Индекс узла приемника")
    nsb1: int = Field(..., description="Тип связи (NTIP)")
    ndop: int = Field(0, description="Спец. режим связи (NDOP)")
    gsw: float = Field(0.0, description="Заданный расход, т/ч")
    hsw: float = Field(0.0, description="Заданная энтальпия, ккал/кг")
    dop: float = Field(0.0, description="Доп. параметр (обычно потери давления)")

class CalculationInput(BaseModel):
    solver_settings: SolverSettings = Field(default_factory=SolverSettings)
    nodes: List[NodeInput] = Field(..., description="Массив узлов схемы")
    links: List[LinkInput] = Field(..., description="Массив связей схемы")
    regime_targets: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Режимные уставки: t_охл, P_ot_target, Q_sn и т.д."
    )

class NodeOutput(NodeInput):
    S: float = Field(0.0, description="Энтропия (расчетная)")
    V: float = Field(0.0, description="Удельный объем (расчетный)")
    X: float = Field(0.0, description="Степень сухости (расчетная)")

class LinkOutput(LinkInput):
    SB: List[float] = Field(..., description="Массив рассчитанных параметров связи (G, H, P и т.д.)")

class IterationMetric(BaseModel):
    iteration: int
    dg_abs: float
    worst_link_abs: Optional[int]

class CalculationOutput(BaseModel):
    status: ReportStatus
    trace_events: List[str] = Field(default_factory=list, description="Лог событий решателя")
    metrics: List[IterationMetric] = Field(default_factory=list, description="Статистика по итерациям")
    nodes_result: List[NodeOutput]
    links_result: List[LinkOutput]
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)