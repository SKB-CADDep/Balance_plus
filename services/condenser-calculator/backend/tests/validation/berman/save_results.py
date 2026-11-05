"""
Скрипт автоматической генерации и сохранения эталонных результатов
на основе расчетов физического движка BermanStrategy.
"""

import os
import json
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from tests.validation.berman.test_berman_verification_calc import berman_calculate_wrapper, locate_and_load_json

RESULTS_DIR = os.path.join(BASE_DIR, "validation_data", "condenser-calculator", "strategies", "berman", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def generate_and_save(geom_name, mode_name, result_name):
    print(f"Расчет для {geom_name} + {mode_name}...")
    geom = locate_and_load_json(geom_name)
    mode = locate_and_load_json(mode_name)
    
    result = berman_calculate_wrapper(geom, mode)
    
    output_path = os.path.join(RESULTS_DIR, result_name)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"  -> Результаты успешно сохранены в {result_name}!")

if __name__ == "__main__":
    generate_and_save("geometry_k3100.json", "mode_k3100.json", "results_k3100.json")
    generate_and_save("geometry_kg2_6200.json", "mode_kg2_6200.json", "results_kg2_6200.json")
    generate_and_save("geometry_kg2_7300.json", "mode_kg2_7300.json", "results_kg2_7300.json")
    print("\n[УСПЕХ] Все файлы результатов успешно сгенерированы и сохранены!")