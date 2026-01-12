# [DB-EQUIP-CONDENSER] База данных: Конденсаторы паровых турбин

**Версия схемы:** 1.2<br>
**Статус:** Черновик<br>
**Ответственный:** @D0k2<br>
**Участник:** -<br> 
**Связанные методики:**
1. [CALC-COND-METRO_VIKKERS] [Метод Метро-Виккерс](https://github.com/LevShlyogin/Balance_plus/blob/main/docs/methods/balance/CALC-COND-METRO_VIKKERS.md)
2. [CALC-COND-BERMAN] [Метод Бермана](https://github.com/LevShlyogin/Balance_plus/blob/main/docs/methods/balance/CALC-COND-BERMAN.md)

## 1. Описание сущности
База данных хранит:
- основные данные конденсатора;
- геометрические характеристики поверхностных конденсаторов;
- допускаемые диапазоны работы конденсатор.

Данные используются для теплогидравлических расчетов.<br>
Источники данных: Теплогидравлический расчет конденсатора, Паспорт конденсатора, Сборочный чертеж.

## 2. Структура данных (Schema)

### 2.1. Основная информация (Main)
Связи с проектом, наименование конденсатора и вспомогательными документами

| Ключ (Code) | Название (UI) | Ед. изм. | Тип | Обяз. | Описание / Источник | Валидация |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `condenser_id` | ID конденсатора | - | Int | **Да** | - | проставляется автоматически |
| `name_condenser` | Наименование конденсатора | - | String | **Да** | Маркировка конденсатора | не требуется |
| `doc_num_thermo_calc` | Номер документа теплогидравлического расчета | - | String | Нет | Теплогидравлический расчет конденсатора | не требуется |
| `doc_num_assembly` | Номер документа сборочного чертежа | - | String | Нет | Сборочный чертеж конденсатора | не требуется |
| `doc_num_passport` | Номер документа паспорта | - | String | Нет | Паспорт конденсатора | не требуется |
| `project_id` | Связанные проекты | - | Ref | Нет | Справочник проектов [DB-PROJECTS](url) | Список |

### 2.2. Основная геометрия (Geometry)
Параметры трубной системы. Если конденсатор имеет разделение на потоки, указываются параметры для одного корпуса/потока, если не указано иное.

| Ключ (Code) | Название (UI) | Ед. изм. | Тип | Обяз. | Описание / Источник | Валидация |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `diameter_internal` | Внутренний диаметр труб ($d_{in}$) | мм | Float | **Да** | Внутренний диаметр труб охлаждения | > 0 |
| `wall_thickness` | Толщина стенки трубы ($S_{tube}$) | мм | Float | **Да** | Толщина стенки труб охлаждения | > 0 |
| `material_id` | Материал трубок | - | Ref | **Да** | Cправочник материалов [DB-MATERIALS](https://github.com/LevShlyogin/Balance_plus/blob/main/docs/methods/database_structure/DB-MATERIALS.md) | Список |
| `main_length` | Активная длина труб ОП ($L_{main}$) | мм | Float | **Да** | Длина теплообменной части основного пучка (между трубными досками) | > 0 |
| `main_count` | Число труб ОП ($N_{main}$) | шт | Int | **Да** | Количество охлаждающих труб основного пучка | > 0 |
| `builtin_length`| Активная длина труб ВП ($L_{builtin}$) | мм | Float | Нет | Длина труб встроенного пучка | >= 0 |
| `builtin_count` | Число труб ВП ($N_{builtin}$) | шт | Int | Нет | Количество охлаждающих труб встроенного пучка | >= 0 |
| `aircooler_count`| Число труб ВО ($N_{aircooler}$) | шт | Int | Нет | Количество трубок воздухоохладителя | >= 0 |
| `passes_main` | Число ходов воды ОП ($Z_{main}$) | - | Int | **Да** | Конструктивное число ходов в основном пучке | >= 1 |
| `passes_builtin` | Число ходов воды ВП ($Z_{builtin}$) | - | Int | Нет | Конструктивное число ходов во встроенном пучке | >= 1 |
| `ejectors_count` | Число эжекторов ($Z_{ej}$) | шт | Int | **Да** | Кол-во работающих эжекторов | >= 1 |

### 2.3. Паспортные ограничения (Limits & Ratings)
Используются для валидации введенного режима.

| Ключ (Code) | Название (UI) | Ед. изм. | Тип | Обяз. | Описание | Валидация |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `mass_flow_steam_nom` | Номинальный расход пара $G_{nom}$ | кг/ч | Float | **Да** | Номинальный расход пара в конденсатор | > 0 |
| `mass_flow_air` | Присосы воздуха $G_{air}$ | кг/ч | Float | **Да** | Номинальная величина присосов воздуха в конденсатор по паспорту | > 0 |
| `G_colling_water_max` | Максимальный расход охлаждающей воды $G_{CWmax}$ | т/ч | Float | Нет | Максимальный расход охлаждающей воды при скорости в трубках 2 м/с | >= 0 |
| `G_colling_water_nom` | Номинальный расход охлаждающей воды $G_{CWnom}$ | т/ч | Float | Нет | - | >= 0 |
| `G_colling_water_min` | Номинальный расход охлаждающей воды $G_{CWmin}$ | т/ч | Float | Нет | Минимальный расход охлаждающей воды при скорости в трубках не менее 0.5 м/с | >= 0 |
| `G_water_main_and_builtin_max` | Максимальный расход охлаждающей воды $G_{MBmax}$ | т/ч | Float | Нет | Максимальный расход охлаждающей воды через основные и встроенные пучки | >= 0 |
| `G_water_main_and_builtin_min` | Минимальный расход охлаждающей воды $G_{MBmin}$ | т/ч | Float | Нет | Минимальный расход охлаждающей воды через основные и встроенные пучки | >= 0 |
| `G_water_main_and_builtin_z1_max` | Максимальный расход охлаждающей воды $G_{MBZ1max}$ | т/ч | Float | Нет | Максимальный расход охлаждающей воды через основные и встроенные пучки в один ход | >= 0 |
| `G_water_main_and_builtin_z1_min` | Минимальный расход охлаждающей воды $G_{MBZ1min}$ | т/ч | Float | Нет | Минимальный расход охлаждающей воды через основные и встроенные пучки в один ход | >= 0 |
| `G_water_main_and_builtin_z2_max` | Максимальный расход охлаждающей воды $G_{MBZ2max}$ | т/ч | Float | Нет | Максимальный расход охлаждающей воды через основные и встроенные пучки в два хода | >= 0 |
| `G_water_main_and_builtin_z2_min` | Минимальный расход охлаждающей воды $G_{MBZ2min}$ | т/ч | Float | Нет | Минимальный расход охлаждающей воды через основные и встроенные пучки в два хода | >= 0 |
| `G_water_main_max` | Максимальный расход охлаждающей воды $G_{Mmax}$ | т/ч | Float | Нет | Максимальный расход охлаждающей воды через основной пучок | >= 0 |
| `G_water_main_min` | Минимальный расход охлаждающей воды $G_{Mmin}$ | т/ч | Float | Нет | Минимальный расход охлаждающей воды через основной пучок | >= 0 |
| `G_water_builtin_z1_max` | Максимальный расход охлаждающей воды $G_{BZ1max}$ | т/ч | Float | Нет | Максимальный расход охлаждающей воды через встроенный пучок в один ход (основные пучки отключены) | >= 0 |
| `G_water_builtin_z1_min` | Минимальный расход охлаждающей воды $G_{BZ1min}$ | т/ч | Float | Нет | Минимальный расход охлаждающей воды через встроенный пучок в один ход (основные пучки отключены) | >= 0 |
| `G_water_builtin_z2_max` | Максимальный расход охлаждающей воды $G_{BZ2max}$ | т/ч | Float | Нет | Максимальный расход охлаждающей воды через встроенный пучок в два хода (основные пучки отключены) | >= 0 |
| `G_water_builtin_z2_min` | Минимальный расход охлаждающей воды $G_{BZ2min}$ | т/ч | Float | Нет | Минимальный расход охлаждающей воды через встроенный пучок в два хода (основные пучки отключены) | >= 0 |
| `G_water_builtin_z4_max` | Максимальный расход охлаждающей воды $G_{BZ4max}$ | т/ч | Float | Нет | Максимальный расход охлаждающей воды через встроенный пучок в четыре хода (основные пучки отключены) | >= 0 |
| `G_water_builtin_z4_min` | Минимальный расход охлаждающей воды $G_{BZ4min}$ | т/ч | Float | Нет | Минимальный расход охлаждающей воды через встроенный пучок в четыре хода (основные пучки отключены) | >= 0 |

### 2.4. Кодировка данных БД (Code)

| Название | Системная ед. | Короткий код | Длинный код |
| :---: | :---: | :---: | :---: |
| Активная длина труб ВП | мм | L_builtin | dimension.metal.data.condenser.db-equip-condenser.builtin-length |
| Внутренний диаметр труб | мм | d_in | dimension.metal.data.condenser.db-equip-condenser.diameter-internal |
| Активная длина труб ОП | мм | L_main | dimension.metal.data.condenser.db-equip-condenser.main-length |
| Толщина стенки труб | мм | S_tube | dimension.metal.data.condenser.db-equip-condenser.wall-thickness |
| Присосы воздуха | кг/ч | G_air | mass-flow.air.data.condenser.db-equip-condenser |
| Номинальный расход пара | т/ч | G_nom | mass-flow.steam.inlet.condenser.nom.db-equip-condenser |
| Максимальный расход охлаждающей воды | т/ч | G_CWmax | mass-flow.water.inlet.condenser.max.db-equip-condenser.colling |
| Максимальный расход охлаждающей воды | т/ч | G_BZ1max | mass-flow.water.inlet.condenser.max.db-equip-condenser.colling-builtin-z1 |
| Максимальный расход охлаждающей воды | т/ч | G_BZ2max | mass-flow.water.inlet.condenser.max.db-equip-condenser.colling-builtin-z2 |
| Максимальный расход охлаждающей воды | т/ч | G_BZ4max | mass-flow.water.inlet.condenser.max.db-equip-condenser.colling-builtin-z4 |
| Максимальный расход охлаждающей воды | т/ч | G_Mmax | mass-flow.water.inlet.condenser.max.db-equip-condenser.colling-main |
| Максимальный расход охлаждающей воды | т/ч | G_MBmax | mass-flow.water.inlet.condenser.max.db-equip-condenser.colling-main-and-builtin |
| Максимальный расход охлаждающей воды | т/ч | G_MBZ1max | mass-flow.water.inlet.condenser.max.db-equip-condenser.colling-main-and-builtin-z1 |
| Максимальный расход охлаждающей воды | т/ч | G_MBZ2max | mass-flow.water.inlet.condenser.max.db-equip-condenser.colling-main-and-builtin-z2 |
| Минимальный расход охлаждающей воды | т/ч | G_CWmin | mass-flow.water.inlet.condenser.min.db-equip-condenser.colling |
| Минимальный расход охлаждающей воды | т/ч | G_BZ1min | mass-flow.water.inlet.condenser.min.db-equip-condenser.colling-builtin-z1 |
| Минимальный расход охлаждающей воды | т/ч | G_BZ2min | mass-flow.water.inlet.condenser.min.db-equip-condenser.colling-builtin-z2 |
| Минимальный расход охлаждающей воды | т/ч | G_BZ4min | mass-flow.water.inlet.condenser.min.db-equip-condenser.colling-builtin-z4 |
| Минимальный расход охлаждающей воды | т/ч | G_Mmin | mass-flow.water.inlet.condenser.min.db-equip-condenser.colling-main |
| Минимальный расход охлаждающей воды | т/ч | G_MBmin | mass-flow.water.inlet.condenser.min.db-equip-condenser.colling-main-and-builtin |
| Минимальный расход охлаждающей воды | т/ч | G_MBZ1min | mass-flow.water.inlet.condenser.min.db-equip-condenser.colling-main-and-builtin-z1 |
| Минимальный расход охлаждающей воды | т/ч | G_MBZ2min | mass-flow.water.inlet.condenser.min.db-equip-condenser.colling-main-and-builtin-z2 |
| Номинальный расход охлаждающей воды | т/ч | G_CWnom | mass-flow.water.inlet.condenser.nom.db-equip-condenser.colling |
| Номер сборочного чертежа конденсатора | - | doc_num_assembly | names.data.condenser.db-equip-condenser.doc-num-assembly |
| Номер паспорта конденсатора | - | doc_num_passport | names.data.condenser.db-equip-condenser.doc-num-passport |
| Номер документа теплогидравлического расчета | - | doc_num_thermo_calc | names.data.condenser.db-equip-condenser.doc-num-thermo-calc |
| Наименование конденсатора | - | name_condenser | names.data.condenser.db-equip-condenser.name |
| ID материала охлаждающих труб | - | material_id | names.metal.data.condenser.db-equip-condenser.material-id |
| ID конденсатора | - | condenser_id | names.other.data.condenser.db-equip-condenser.condenser-id |
| ID проекта | - | project_id | names.other.data.condenser.db-equip-condenser.project-id |
| Число труб ВО | шт | N_aircooler | quantity.metal.data.condenser.db-equip-condenser.aircooler-count |
| Число труб ВП | шт | N_builtin | quantity.metal.data.condenser.db-equip-condenser.builtin-count |
| Количество охлаждающих труб основного пучка | шт | N_main | quantity.metal.data.condenser.db-equip-condenser.main-count |
| Число эжекторов | шт | Z_ejectors | quantity.other.json.condenser.db-equip-condenser.ejectors-count |
| Число ходов воды ВП | шт | Z_builtin | quantity.water.json.condenser.db-equip-condenser.passes-builtin |
| Число ходов воды ОП | шт | Z_main | quantity.water.json.condenser.db-equip-condenser.passes-main |

## 3. Пример JSON (Payload)

```json
{
  "condenser_id": "uuid-v4-generated-string",
  "main_info": {
    "name_condenser": "80-КЦС-3",
    "project_id": "proj-12345",
    "doc_num_thermo_calc": "№ 123-ТГР",
    "doc_num_assembly": "Черт. АБВГ.123456.001 СБ",
    "doc_num_passport": "ПС-123-456"
  },
  "geometry": {
    "diameter_internal": 24.0,
    "wall_thickness": 1.0,
    "material_id": "858dc196-6712-4dbb-bfdd-201c8ca5c65c",
    "main_length": 8950.0,
    "main_count": 8400,
    "L_builtin": 8950.0,
    "builtin_count": 1200,
    "aircooler_count": 450,
    "passes_main": 2,
    "passes_builtin": 2,
    "ejectors_count": 1
  },
  "limits": {
    "mass_flow_steam_nom": 155000.0,
    "mass_flow_air": 40.0,
    "G_colling_water_max": 18000.0,
    "G_colling_water_nom": 16000.0,
    "G_colling_water_min": 8000.0,
    "main_and_builtin_limits": {
      "G_water_main_and_builtin_max": 18000.0,
      "G_water_main_and_builtin_min": 4000.0,
      "one_pass": {
        "G_water_main_and_builtin_z1_max": 36000.0,
        "G_water_main_and_builtin_z1_min": 10000.0
      },
      "two_passes": {
        "G_water_main_and_builtin_z2_max": 18000.0,
        "G_water_main_and_builtin_z2_min": 4000.0
      }
    },
    "main_bundle_limits": {
      "G_water_main_max": 14000.0,
      "G_water_main_min": 3500.0
    },
    "builtin_bundle_limits": {
      "one_pass": {
        "G_water_builtin_z1_max": 5000.0,
        "G_water_builtin_z1_min": 1500.0
      },
      "two_passes": {
        "G_water_builtin_z2_max": 2500.0,
        "G_water_builtin_z2_min": 750.0
      },
      "four_passes": {
        "G_water_builtin_z4_max": 1250.0,
        "G_water_builtin_z4_min": 375.0
      }
    }
  }
}
```

## 4. Связь параметров БД с Методиками

| Параметр БД | Методика Метро-Виккерс (код) | Методика Бермана (код) | Комментарий |
| :--- | :--- | :--- | :--- |
| `diameter_internal` | `d_in` | `d_in` | - |
| `wall_thickness` | `S_tube` | `S_tube` | - |
| `material_id` | `lambda` | `lambda` | - |
| `main_length` | `L_main` | `L_main` | - |
| `main_count` | `N_main` | `N_main` | - |
| `builtin_length`| `L_builtin` | *Не используется* | - |
| `builtin_count` | `N_builtin` | `N_builtin` | - |
| `aircooler_count` | *Не используется* | `N_aircooler` | - |
| `passes_main` | `Z_main` | `Z_main` | - |
| `passes_builtin` | `Z_builtin` | *Не используется* | - |
| `ejectors_count` | `Z_ejectors` | *Не используется* | - |

## 5. Особые указания
1. **Материал трубок:** В расчетах требуется теплопроводность $\lambda$. Она должна подтягиваться из справочника материалов [DB-MATERIALS](https://github.com/LevShlyogin/Balance_plus/blob/main/docs/methods/database_structure/DB-MATERIALS.md) по `material_id` в ввиде зависимости $lambda = f(t_{avg})$.
