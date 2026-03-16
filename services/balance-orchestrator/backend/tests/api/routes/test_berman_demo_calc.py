# Описание для красивого отображения в нашем CLI-Оркестраторе
description = "Демо: Проверка математики (с генерацией логов)"

# 1. ФУНКЦИЯ-ЗАГЛУШКА (В реальности тут будет: from app.utils... import calculate_berman)
def dummy_thermal_calculation(pressure: float, temperature: float, flow_rate: float):
    """Простая формула для демонстрации работы тестов."""
    if flow_rate <= 0:
        return {"efficiency": 0.0, "power_output": 0.0}
    
    # Искусственная логика расчета
    power = (pressure * 10) + (temperature * 0.5)
    efficiency = 0.85 if pressure > 3.0 else 0.50
    
    return {
        "efficiency": efficiency,
        "power_output": power
    }

# 2. УКАЗЫВАЕМ PYTEST-У, КАКУЮ ФУНКЦИЮ ТЕСТИРОВАТЬ
target_function = dummy_thermal_calculation

# 3. МАССИВ С ДАННЫМИ (То, что будут писать аналитики)
tests =[
    {
        "id": "mode_1_normal_load",
        "input": {
            "pressure": 4.5, 
            "temperature": 120.0,
            "flow_rate": 500
        },
        "expected": {
            "efficiency": 0.85,
            "power_output": 105.0  # (4.5*10) + (120*0.5) = 45 + 60 = 105
        }
    },
    {
        "id": "mode_2_zero_flow",
        "input": {
            "pressure": 4.5, 
            "temperature": 120.0,
            "flow_rate": 0
        },
        "expected": {
            "efficiency": 0.0,
            "power_output": 0.0
        }
    },
    {
        "id": "mode_3_intentional_error",
        # 🔥 СПЕЦИАЛЬНО ЛОМАЕМ ТЕСТ, чтобы проверить сохранение лог-файла!
        "input": {
            "pressure": 5.0, 
            "temperature": 100.0,
            "flow_rate": 500
        },
        "expected": {
            "efficiency": 0.85,
            # Реальный ответ будет 100.0, но мы ждем 999.0
            "power_output": 999.0 
        }
    }
]