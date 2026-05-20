# Архитектура асинхронных расчетов (Celery + Redis)
**Паттерн взаимодействия:** Fan-out / Fan-in

## 1. Введение
Данный документ описывает контракт взаимодействия между сервисом Оркестратора (Balance Orchestrator) и вычислительными воркерами микросервисов (Condenser Calculator, Valve Stems Calculator). 
Интеграция построена на базе Celery, использующего Redis в качестве брокера сообщений (Broker) и хранилища результатов (Result Backend).

## 2. Схема взаимодействия (Fan-out / Fan-in)
1. **Fan-out:** Оркестратор разбивает задачу (например, расчет турбины) на независимые блоки (конденсатор, клапаны, отборы). Для каждого блока Оркестратор публикует задачу в соответствующую очередь Celery.
2. **Processing:** Свободные воркеры подхватывают задачи из своих очередей.
3. **Fan-in:** Оркестратор периодически (polling) проверяет статус запущенных задач. Как только все задачи завершаются (статус `SUCCESS`), Оркестратор агрегирует результаты и формирует итоговый баланс.

## 3. Контракты данных (JSON-сообщения)

### 3.1. Структура задачи (Task Payload)
При вызове асинхронной задачи Оркестратор должен передать сериализованный JSON. Формат Payload жестко привязан к Pydantic-схеме конкретного микросервиса.

**Пример A: Condenser Calculator (`app.worker.calculate_async_task`)**
```json
{
  "task_name": "app.worker.calculate_async_task",
  "kwargs": {
    "input_data": {
      "condenser_id": 1,
      "material_id": 1,
      "method": "berman",
      "coefficient_b": [0.85, 1.0],
      "G_steam": [150.0, 160.0],
      "W_main": [12000.0],
      "t1_main": [15.0],
      "H_steam": 550.0
    }
  }
}

```

**Пример B: Valve Stems Calculator (`app.worker.calculate_valves_task`)**

```json
{
  "task_name": "app.worker.calculate_valves_task",
  "kwargs": {
    "input_data": {
      "turbine_id": 1,
      "globals": {
        "P_fresh": 130.0,
        "P_fresh_unit": "кгс/см²",
        "T_fresh": 555.0,
        "T_fresh_unit": "°C",
        "P_air": 1.033,
        "T_air": 40.0,
        "P_lst_leak_off": 0.97
      },
      "groups": [
        {
          "valve_id": 9,
          "type": "СК",
          "valve_names": ["СК-1", "СК-2"],
          "quantity": 2,
          "p_leak_offs": [10.0],
          "p_leak_offs_unit": "кгс/см²"
        }
      ]
    }
  }
}

```

### 3.2. Формат ответа воркера (Result Payload)

Результат выполнения задачи сохраняется в Redis. Оркестратор обращается к Result Backend по `task_id` и получает ответ. Воркер обязан возвращать ответ в едином формате (`status`, `task_id`, `result` / `error`), внутри которого лежит специфика сервиса.

**Успешное выполнение — Condenser (State: `SUCCESS`):**

```json
{
  "status": "success",
  "task_id": "3f9612d0-36fc-4e58-afa6-8cb05b51d5d8",
  "result": {
    "tables": [
      {
        "meta": {"W_main": 12000.0, "coefficient_b": 0.85},
        "columns": [150.0, 160.0],
        "rows": [15.0],
        "values": [[0.045, 0.048]],
        "warnings": []
      }
    ],
    "ejectors": []
  }
}

```

**Успешное выполнение — Valve Stems (State: `SUCCESS`):**

```json
{
  "status": "success",
  "task_id": "5580e5b3-833d-4f0e-a7b5-65ba41fb5f43",
  "result": {
    "details": [
      {
        "valve_id": 9,
        "type": "СК",
        "valve_names": ["СК-1", "СК-2"],
        "quantity": 2,
        "Gi": [0.536, 0.074, 0.003],
        "Pi_in": [130.0, 10.0, 1.03],
        "Ti": [555.0, 503.6, 40.0],
        "Hi": [3487.0, 3487.0, 40.2],
        "deaerator_props": [0.925, 503.6, 3487.0, 10.0],
        "ejector_props": [{"g": 0.155, "t": 426.4, "h": 3333.6, "p": 0.97}],
        "group_total_g": 1.226
      }
    ],
    "summary": {
      "ск": {"total_g": 1.226, "mixed_h": 3487.0},
      "рк": {"total_g": 0.0, "mixed_h": 0.0},
      "срк": {"total_g": 0.0, "mixed_h": 0.0}
    }
  }
}

```

**Бизнес-ошибка / Ошибка валидации (State: `FAILURE`):**

```json
{
  "status": "error",
  "task_id": "3f9612d0-36fc-4e58-afa6-8cb05b51d5d8",
  "error_type": "ValidationError",
  "message": "В БД у клапана id=9 не заполнены длины участков!",
  "traceback": null
}

```

**Критическая ошибка (State: `FAILURE`):**

```json
{
  "status": "error",
  "task_id": "3f9612d0-36fc-4e58-afa6-8cb05b51d5d8",
  "error_type": "CalculationEngineError",
  "message": "ZeroDivisionError in matrix calculation",
  "traceback": "... stack trace ..."
}

```

## 4. Очереди маршрутизации (Routing)

Чтобы задачи не перемешивались, в конфигурации Celery определены явные очереди (Queues).

| Сервис | Название задачи (Task Name) | Название очереди (Queue) |
| --- | --- | --- |
| Condensers | `app.worker.calculate_async_task` | `condenser_calculations` |
| Valve Stems | `app.worker.calculate_valves_task` | `valve_calculations` |

## 5. Политика обработки ошибок (Retry Policies)

Для обеспечения отказоустойчивости применяются следующие правила повторов:

1. **Ошибки бизнес-логики (Business Errors):**
* *Примеры:* `ValidationError` (отрицательное давление), `CalculationEngineError` (метод Бермана не сошелся).
* *Политика:* **NO RETRY**. Задача немедленно переходит в статус `FAILURE`. Повторять бессмысленно, так как входные данные неверны. Оркестратор прерывает формирование баланса и возвращает ошибку пользователю.


2. **Временные (Transient) инфраструктурные ошибки:**
* *Примеры:* Отвал соединения с БД Postgres (при чтении геометрии клапана), кратковременный таймаут Redis.
* *Политика:* **AUTO-RETRY**.
* *Параметры:* `max_retries=3`, `default_retry_delay=5` (секунд). Воркер использует экспоненциальную задержку (backoff) для повторных попыток.


3. **Смерть воркера (OOM Killer / Pod Eviction):**
* *Механизм:* Используется `acks_late=True`. Celery-воркер подтверждает (acknowledge) выполнение задачи только *после* успешного сохранения результата. Если контейнер воркера убит (например, нехватка памяти при расчете огромной матрицы) до завершения, задача вернется в очередь `UNACKNOWLEDGED` и будет подхвачена другим воркером.