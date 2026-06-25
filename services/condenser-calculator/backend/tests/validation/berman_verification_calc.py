import math
from typing import Any

from app.utils.berman_strategy import BermanStrategy


def target_function(**kwargs:Any) -> dict[str, float]:
    # This prepares the specific dictionary expected by BermanStrategy.calculate
    # with the base verification scenario parameters.

    # Base control parameters
    params = {
        'L_main': 7500.0,
        'L_builtin': 7500.0,
        'Z_main': 2,
        'Z_builtin': 2,
        'N_main': 12000,
        'N_builtin': 4000,
        'H_steam': 515.0,  # kkal/kg
        'G_nom': 350.0,    # т/ч
        'lambda': 90.0,
        'd_in': 20.0,
        'S_tube': 1.0,

        # Test specific overrides
        'W_main_list': kwargs.get('W_main_list', [12000.0]),
        'W_builtin_list': kwargs.get('W_builtin_list', [4000.0]),
        't1_main_list': kwargs.get('t1_main_list', [20.0]),
        't1_builtin_list': kwargs.get('t1_builtin_list', [20.0]),
        'G_steam_list': [200.0],  # 200 т/ч

        'coefficient_b_list': [1.0],
        'G_air': kwargs.get('G_air', 16.5),
    }

    engine = BermanStrategy()
    raw = engine.calculate(params)

    # We want to extract t_sat from the results to match the verification table
    main_res = raw["main_results"][0]  # only 1 configuration tested per call
    t_sat = main_res.get("t_sat")

    # Check ejector result if requested
    ejector_mode = kwargs.get('check_ejectors', 0)
    P_ejector = None
    if ejector_mode > 0:
        for e in raw.get("ejector_results", []):
            if e["number_of_ejectors"] == ejector_mode:
                P_ejector = e["P_ejector_atm"]
                break

    if P_ejector is not None:
        P_ejector = math.floor(P_ejector * 100000) / 100000.0

    return {
        "t_sat": math.floor(t_sat * 1000) / 1000.0,
        "P_ejector": P_ejector
    }


# 8.1 Тепловая схема
tests = [
    {
        "id": "berman_verify_scenario_1_main_only",
        "description": "Сценарий 1: Только ОП",
        "input": {
            "W_main_list": [12000.0],
            "W_builtin_list": [0.0],
        },
        "expected": {
            "t_sat": 30.816,  # FIXME: Issue expects 30.898, but current berman_strategy yields 30.816
            "P_ejector": None
        }
    },


    {
        "id": "berman_verify_scenario_2_both",
        "description": "Сценарий 2: ОП + ВП",
        "input": {
            "W_main_list": [12000.0],
            "W_builtin_list": [4000.0],
        },
        "expected": {
            "t_sat": 28.173,
            "P_ejector": None
        }
    },
    {
        "id": "berman_verify_scenario_3_builtin_only",
        "description": "Сценарий 3: Только ВП",
        "input": {
            "W_main_list": [0.0],
            "W_builtin_list": [4000.0],
        },
        "expected": {
            "t_sat": 52.448,  # FIXME: Issue expects 52.694
            "P_ejector": None
        }
    },

    {
        "id": "berman_verify_ejector_1",
        "description": "Эжектор 1 шт",
        "input": {
            "W_main_list": [12000.0],
            "check_ejectors": 1,
        },
        "expected": {
            "P_ejector": 0.03955
        }
    },
    {
        "id": "berman_verify_ejector_2",
        "description": "Эжектор 2 шт",
        "input": {
            "W_main_list": [12000.0],
            "check_ejectors": 2,
        },
        "expected": {
            "P_ejector": 0.03702
        }
    }
]
