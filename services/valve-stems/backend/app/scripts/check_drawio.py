"""
Скрипт локального тестирования и отладки генератора схем Draw.io.

Утилита проверяет работоспособность классов `ParameterMapper` и `DiagramModifier`.
Берет заготовленный шаблон (XML/Draw.io), подставляет в него тестовые размеры 
геометрии клапана (mock data) и сохраняет результат в отдельную папку 
для визуального контроля разработчиком.
"""

import os

from app.api.routes.drawio import DiagramModifier, ParameterMapper
from app.schemas import ValveInfo


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "templates", "template_2_parts.xml")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "generated_diagrams")

os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "test_output.drawio")

print(f"Директория скрипта: {SCRIPT_DIR}")
print(f"Путь к шаблону: {TEMPLATE_PATH}")
print(f"Путь для сохранения результата: {OUTPUT_PATH}")

# [ENGINEERING CONTEXT]
# Тестовый набор данных (Mock). Представляет собой типичную геометрию двухучасткового
# штока клапана. Эти размеры будут подставлены вместо плейсхолдеров на чертеже.
sample_valve = ValveInfo(
    count_parts=2,
    diameter=65.0,
    clearance=0.35,
    len_part1=210.0,
    len_part2=125.0
)


def run_test():
    """
    Функция для запуска теста генерации диаграммы.

    Читает шаблон, формирует словарь обновлений на основе входных параметров,
    модифицирует узлы графа и сохраняет итоговый файл.
    """
    print("\n--- Запуск теста генерации схемы ---")

    if not os.path.exists(TEMPLATE_PATH):
        print(f"Ошибка: Файл шаблона не найден по пути: {TEMPLATE_PATH}")
        return

    try:
        # [ENGINEERING CONTEXT]
        # Как работает интеграция с Draw.io под капотом:
        # Файлы .drawio по сути являются XML-документами (модель mxGraph). 
        # Каждый визуальный элемент (текст, стрелка, рамка) имеет свой уникальный `cell_id`.
        # Значения внутри блоков часто хранятся в виде HTML-строк (html_value).
        # ParameterMapper знает, какому ID соответствует какой размер (например, длина L1),
        # а DiagramModifier просто находит этот узел в XML-дереве и перезаписывает его текст.
        mapper = ParameterMapper(count_parts=sample_valve.count_parts)
        updates = mapper.map_parameters(sample_valve)
        print(f"Подготовлены обновления для {len(updates)} полей: {list(updates.keys())}")
        
        modifier = DiagramModifier(template_path=TEMPLATE_PATH)

        for cell_id, html_value in updates.items():
            modifier.update_parameter(cell_id, html_value)

        modifier.save_modified_diagram(OUTPUT_PATH)
        print(f"Успех! Схема сохранена в: {OUTPUT_PATH}")

    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    run_test()
    