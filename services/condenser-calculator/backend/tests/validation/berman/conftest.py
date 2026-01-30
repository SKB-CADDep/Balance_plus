"""
Общие фикстуры и утилиты для валидационных тестов BermanStrategy.

Путь: services/condenser-calculator/backend/tests/validation/berman/conftest.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from app.utils.berman_strategy import BermanStrategy


# =============================================================================
# ПУТИ К ДАННЫМ
# =============================================================================


def _find_monorepo_root(start: Path) -> Path:
    """
    Поднимаемся вверх, пока не найдём корень монорепозитория.
    Критерий: наличие директорий `services/` и `docs/`.
    """
    start = start.resolve()
    for p in [start, *start.parents]:
        if (p / "services").is_dir() and (p / "docs").is_dir():
            return p
    # fallback: tests/validation/berman -> tests -> backend -> condenser-calculator -> services -> root
    return start.parents[5]


_MONOREPO_ROOT = _find_monorepo_root(Path(__file__))
VALIDATION_DATA_ROOT = _MONOREPO_ROOT / "validation_data"

# Переходный режим миграции: пока данные могут жить в старом месте `tests/validation_data`
_legacy_validation_root = _MONOREPO_ROOT / "tests" / "validation_data"
_sentinel = (
    VALIDATION_DATA_ROOT
    / "condenser-calculator"
    / "strategies"
    / "berman"
    / "results"
    / "results_1.json"
)
if not _sentinel.exists() and _legacy_validation_root.exists():
    VALIDATION_DATA_ROOT = _legacy_validation_root
BERMAN_DATA_PATH = VALIDATION_DATA_ROOT / "condenser-calculator" / "strategies" / "berman"

GEOMETRYS_PATH = BERMAN_DATA_PATH / "geometrys"
MODES_PATH = BERMAN_DATA_PATH / "modes"
RESULTS_PATH = BERMAN_DATA_PATH / "results"


# =============================================================================
# УТИЛИТЫ ЗАГРУЗКИ ДАННЫХ
# =============================================================================


def load_json(filepath: Path) -> dict:
    """Загрузка JSON-файла."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_geometry(name: str = "geometry") -> dict:
    """Загрузка файла геометрии."""
    filepath = GEOMETRYS_PATH / f"{name}.json"
    return load_json(filepath)


def load_mode(mode_num: int) -> dict:
    """Загрузка файла режима."""
    filepath = MODES_PATH / f"mode_{mode_num}.json"
    return load_json(filepath)


def load_results(results_num: int) -> dict:
    """Загрузка файла результатов."""
    filepath = RESULTS_PATH / f"results_{results_num}.json"
    return load_json(filepath)


# =============================================================================
# ПОСТРОЕНИЕ ПАРАМЕТРОВ РАСЧЁТА
# =============================================================================


def build_calculation_params(
    geometry: dict,
    mode: dict,
    W_main: float,
    W_builtin: float,
    t1_main: float,
    t1_builtin: float,
    G_steam: float,
    coefficient_b: float,
    G_air: float = 0.0,
    material_lambda: float = 90.0,
) -> dict:
    """
    Построение словаря параметров для BermanStrategy.calculate()
    на основе данных из geometry.json и mode_X.json.
    """
    geom = geometry["geometry"]

    return {
        # Геометрические параметры
        "L_main": geom["main_length"],
        "L_builtin": geom.get("builtin_length", 0.0),
        "N_main": int(geom["main_count"]),
        "N_builtin": int(geom.get("builtin_count", 0)),
        "d_in": geom["diameter_internal"],
        "S_tube": geom["wall_thickness"],
        "Z_main": int(geom["passes_main"]),
        "Z_builtin": int(geom.get("passes_builtin", 0)),

        # Параметры из limits
        "G_nom": geometry["limits"]["mass_flow_steam_nom"],

        # Параметры из mode
        "H_steam": mode["H_steam"],

        # Материал
        "lambda": material_lambda,

        # Рабочие параметры
        "W_main_list": [W_main],
        "W_builtin_list": [W_builtin],
        "t1_main_list": [t1_main],
        "t1_builtin_list": [t1_builtin],
        "G_steam_list": [G_steam],
        "coefficient_b_list": [coefficient_b],
        "G_air": G_air,
    }


def generate_test_cases_from_results(
    results: dict,
    mode: dict,
    include_ejectors: bool = False,  # noqa: ARG001 (оставлено для совместимости)
) -> List[Dict[str, Any]]:
    """
    Генерация списка тестовых случаев из results_X.json.

    Возвращает список словарей с параметрами и ожидаемыми значениями.
    """
    test_cases: List[Dict[str, Any]] = []

    for mode_data in results["condenser_modes"]:
        W_main = mode_data["W_main"]
        W_builtin = mode_data["W_builtin"]
        coefficient_b = mode_data["coefficient_b"]

        table = mode_data["table_data"][0]
        t1_main_list = table["t1_main"]
        G_steam_list = table["G_steam_axis"]
        pressures = table["pressures_axis"]

        has_different_builtin_temps = (
            mode.get("t1_builtin") and mode["t1_builtin"] != mode["t1_main"]
        )

        for t_idx, t1_main in enumerate(t1_main_list):
            if has_different_builtin_temps:
                t1_builtin = mode["t1_builtin"][t_idx]
            else:
                t1_builtin = t1_main

            for g_idx, G_steam in enumerate(G_steam_list):
                expected_pressure = pressures[t_idx][g_idx]

                test_cases.append(
                    {
                        "W_main": W_main,
                        "W_builtin": W_builtin,
                        "t1_main": t1_main,
                        "t1_builtin": t1_builtin,
                        "G_steam": G_steam,
                        "coefficient_b": coefficient_b,
                        "expected_pressure": expected_pressure,
                        "id": f"W{W_main}_Wb{W_builtin}_t{t1_main}_G{G_steam}_b{coefficient_b}",
                    }
                )

    return test_cases


def generate_ejector_test_cases(results: dict) -> List[Dict[str, Any]]:
    """Генерация тестовых случаев для эжекторов."""
    test_cases: List[Dict[str, Any]] = []

    ejector_limits = results.get("ejector_limits", {})
    if not ejector_limits:
        return test_cases

    t1_axis = ejector_limits["t1_main_axis"]

    for curve in ejector_limits["curves"]:
        status = curve["status_z"]
        if "1" in status:
            num_ejectors = 1
        elif "2" in status:
            num_ejectors = 2
        else:
            continue

        for t1, expected_P in zip(t1_axis, curve["values"]):
            test_cases.append(
                {
                    "num_ejectors": num_ejectors,
                    "t1": t1,
                    "expected_pressure": expected_P,
                    "id": f"ej{num_ejectors}_t{t1}",
                }
            )

    return test_cases


# =============================================================================
# ФИКСТУРЫ PYTEST
# =============================================================================


@pytest.fixture(scope="session")
def strategy():
    """Экземпляр BermanStrategy для всей сессии тестов."""
    return BermanStrategy()


@pytest.fixture(scope="module")
def geometry_standard():
    """Стандартная геометрия (geometry.json)."""
    return load_geometry("geometry")


@pytest.fixture(scope="module")
def geometry_mode4():
    """Геометрия для mode_4 (geometry_4.json)."""
    return load_geometry("geometry_4")


@pytest.fixture(scope="module")
def mode_1():
    return load_mode(1)


@pytest.fixture(scope="module")
def mode_2():
    return load_mode(2)


@pytest.fixture(scope="module")
def mode_3():
    return load_mode(3)


@pytest.fixture(scope="module")
def mode_4():
    return load_mode(4)


@pytest.fixture(scope="module")
def results_1():
    return load_results(1)


@pytest.fixture(scope="module")
def results_2():
    return load_results(2)


@pytest.fixture(scope="module")
def results_3():
    return load_results(3)


@pytest.fixture(scope="module")
def results_4():
    return load_results(4)


# =============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ТЕСТОВ
# =============================================================================


def find_mode_in_results(
    results: dict, W_main: float, W_builtin: float, coefficient_b: float
) -> Optional[dict]:
    """Поиск конкретного режима в results_X.json."""
    for mode in results["condenser_modes"]:
        if (
            mode["W_main"] == W_main
            and mode["W_builtin"] == W_builtin
            and mode["coefficient_b"] == coefficient_b
        ):
            return mode
    return None


def get_expected_pressure(mode_data: dict, t1_idx: int, G_steam_idx: int) -> float:
    """Получение ожидаемого давления по индексам."""
    return mode_data["table_data"][0]["pressures_axis"][t1_idx][G_steam_idx]


def assert_pressure_approx(
    calculated: float,
    expected: float,
    rel_tolerance: float = 0.001,
    context: str = "",
):
    """Проверка давления с информативным сообщением об ошибке."""
    assert calculated == pytest.approx(expected, rel=rel_tolerance), (
        f"{context}\n"
        f"  Ожидаемое P = {expected:.6f} кгс/см²\n"
        f"  Рассчитанное P = {calculated:.6f} кгс/см²\n"
        f"  Отклонение = {abs(calculated - expected) / expected * 100:.3f}%"
    )

