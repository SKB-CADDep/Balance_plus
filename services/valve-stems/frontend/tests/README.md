# 🧪 E2E Тестовая инфраструктура: Valve Stems Frontend

Комплексный набор сквозных автотестов на базе **Playwright** для фронтенд-модуля расчёта штоков клапанов паровых турбин (`services/valve-stems/frontend`).

Тесты полностью изолированы от внешних сервисов с помощью встроенного сетевого мокирования, построены по паттерну **Page Object Model (POM)** и покрывают весь жизненный цикл приложения: от оболочки и навигации до пошагового визарда расчёта, экспорта отчётов и iframe-интеграции с платформой **Balance+**.

---

## 📋 Содержание

1. [🚀 Быстрый старт и команды](#-быстрый-старт-и-команды)
2. [📁 Структура каталогов](#-структура-каталогов)
3. [🏛 Карта классов Page Object Model (POM)](#-карта-классов-page-object-model-pom)
4. [🛠 Хелперы и утилиты](#-хелперы-и-утилиты)
5. [📦 Каталог моковых данных](#-каталог-моковых-данных)
6. [📝 Детальный реестр всех тестовых наборов](#-детальный-реестр-всех-тестовых-наборов)
   - [1. Инфраструктура (`smoke.infra.spec.ts`)](#1-инфраструктура-smokeinfraspects)
   - [2. Оболочка, меню и 404 (`smoke.navigation.spec.ts`)](#2-оболочка-меню-и-404-smokenavigationspects)
   - [3. Шаг 1: Поиск турбин (`calculator.turbine-search.spec.ts`)](#3-шаг-1-поиск-турбин-calculatorturbine-searchspects)
   - [4. Шаг 2: Выбор клапанов (`calculator.stock-selection.spec.ts`)](#4-шаг-2-выбор-клапанов-calculatorstock-selectionspects)
   - [5. Шаг 3: Ввод параметров и валидация (`calculator.stock-input.spec.ts`)](#5-шаг-3-ввод-параметров-и-валидация-calculatorstock-inputspects)
   - [6. Шаг 4: Результаты, Excel, Draw.io (`calculator.results.spec.ts`)](#6-шаг-4-результаты-excel-drawio-calculatorresultsspects)
   - [7. Локальная история расчётов (`calculator.history.spec.ts`)](#7-локальная-история-расчётов-calculatorhistoryspects)
   - [8. Iframe-интеграция с Balance+ (`calculator.embedded.spec.ts`)](#8-iframe-интеграция-с-balance-calculatorembeddedspects)
   - [9. Сквозной Happy Path CI (`calculator.happy-path.spec.ts`)](#9-сквозной-happy-path-ci-calculatorhappy-pathspects)
   - [10. Сквозной Live Happy Path (`calculator.happy-path.live.spec.ts`)](#10-сквозной-live-happy-path-calculatorhappy-pathlivespects)
7. [⚙️ Конфигурация и особенности окружения](#️-конфигурация-и-особенности-окружения)

---

## 🚀 Быстрый старт и команды

Все команды выполняются из директории `services/valve-stems/frontend`:

```bash
cd services/valve-stems/frontend
```

### Основные сценарии запуска:

| Команда | Описание |
| :--- | :--- |
| `npm run test:e2e` | Запуск **всех основных тестов** в Chromium (быстрый CI) |
| `npm run test:e2e:ui` | Запуск в интерактивном UI-режиме Playwright |
| `npm run test:e2e:ci` | Прогон для CI/CD пайплайнов (с отчётом и ретраями) |
| `npx playwright test --grep @live` | Запуск Live-тестов против реального бэкенда (`:5253`) |
| `npx playwright show-report` | Просмотр детального HTML-отчёта с трассировкой и видео |

### Запуск отдельных спецификаций:

```bash
# Smoke и навигация
npx playwright test tests/e2e/smoke.infra.spec.ts --project=chromium
npx playwright test tests/e2e/smoke.navigation.spec.ts --project=chromium

# Пошаговые сценарии калькулятора
npx playwright test tests/e2e/calculator.turbine-search.spec.ts --project=chromium
npx playwright test tests/e2e/calculator.stock-selection.spec.ts --project=chromium
npx playwright test tests/e2e/calculator.stock-input.spec.ts --project=chromium
npx playwright test tests/e2e/calculator.results.spec.ts --project=chromium

# История и интеграция
npx playwright test tests/e2e/calculator.history.spec.ts --project=chromium
npx playwright test tests/e2e/calculator.embedded.spec.ts --project=chromium

# Сквозной Happy Path ("Как инженер")
npx playwright test tests/e2e/calculator.happy-path.spec.ts --project=chromium
```

---

## 📁 Структура каталогов

```text
services/valve-stems/frontend/tests/
├── 📁 e2e/                             # Спецификации E2E-тестов (.spec.ts)
│   ├── 📜 smoke.infra.spec.ts                  # Проверка работоспособности тестовой среды
│   ├── 📜 smoke.navigation.spec.ts             # Тесты оболочки, роутинга и страницы 404
│   ├── 📜 calculator.turbine-search.spec.ts    # Шаг 1: Поиск и фильтрация турбин
│   ├── 📜 calculator.stock-selection.spec.ts   # Шаг 2: Выбор клапанов и количества
│   ├── 📜 calculator.stock-input.spec.ts       # Шаг 3: Ввод термодинамики и валидация
│   ├── 📜 calculator.results.spec.ts           # Шаг 4: Таблицы, экспорт Excel, Draw.io
│   ├── 📜 calculator.history.spec.ts           # Локальная история расчетов (localStorage)
│   ├── 📜 calculator.embedded.spec.ts          # Интеграция с Balance+ (postMessage)
│   ├── 📜 calculator.happy-path.spec.ts        # Сквозной сценарий на моках для CI
│   └── 📜 calculator.happy-path.live.spec.ts   # Сквозной Live-сценарий (тег @live)
├── 📁 pages/                           # Классы Page Object Model (POM)
│   ├── 📜 BasePage.ts                          # Базовый класс: навигация, ожидание сети, шапка
│   ├── 📜 MainPage.ts                          # Базовая обёртка главной страницы
│   ├── 📜 HomePage.ts                          # Главная страница: заголовок, CTA, feature-карточки
│   ├── 📜 AboutPage.ts                         # Страница «О программе»
│   ├── 📜 HelpPage.ts                          # Страница «Помощь» с FAQ-аккордеоном
│   ├── 📜 TurbineSearchPage.ts                 # Шаг 1: Форма поиска турбины и фильтры
│   ├── 📜 StockSelectionPage.ts                # Шаг 2: Список клапанов и выбор количества
│   ├── 📜 StockInputPage.ts                    # Шаг 3: Глобальные параметры, T/H, отсосы
│   ├── 📜 ResultsPage.ts                       # Шаг 4: Таблицы вывода, Excel и Draw.io
│   └── 📜 SidebarHistory.ts                    # Сайдбар истории (открытие, клик, очистка)
├── 📁 mocks/                           # Моковые JSON-файлы ответов REST API
│   ├── 📋 api-mocks.ts                         # Базовая утилита мокирования API
│   ├── 📋 turbines-search.json                 # Список турбин с привязанными клапанами
│   ├── 📋 turbine-valves.json                  # Список клапанов для конкретной турбины
│   ├── 📋 units.json                           # Справочник единиц измерения (P, T, H)
│   ├── 📋 calculation-result.json              # Успешный результат MultiCalculationResult
│   └── 📋 calculation-error.json               # Ответ с ошибкой 500 при расчёте
├── 📁 helpers/                         # Вспомогательные функции
│   ├── 📜 form-fillers.ts                      # Быстрый переход по шагам визарда
│   ├── 📜 localStorage.ts                      # Утилиты работы с wsaCalculatorHistory
│   ├── 📜 postMessage.ts                       # Перехват и валидация window.parent.postMessage
│   └── 📜 test-utils.ts                        # Общие хелперы ассертов и консоли
├── 📁 fixtures/                        # Статические фикстуры
│   └── 📜 test-data.ts
└── 📖 README.md                        # Настоящая документация
```

---

## 🏛 Карта классов Page Object Model (POM)

Все локаторы инкапсулированы внутри классов `tests/pages/`. Прямой хардкод CSS/XPath локаторов внутри `.spec.ts` файлов запрещён:

| Класс POM | Путь | Инкапсулированная функциональность |
| :--- | :--- | :--- |
| **`BasePage`** | `tests/pages/BasePage.ts` | Базовая навигация, ожидание `domcontentloaded`/`networkidle`, ссылки шапки. |
| **`HomePage`** | `tests/pages/HomePage.ts` | Проверка заголовка, feature-карточек и клик по CTA «Начать расчет». |
| **`AboutPage`** | `tests/pages/AboutPage.ts` | Проверка загрузки контента страницы «О программе». |
| **`HelpPage`** | `tests/pages/HelpPage.ts` | Раскрытие секций FAQ аккордеона (`expandFaqItem`) и проверка текста ответа. |
| **`TurbineSearchPage`** | `tests/pages/TurbineSearchPage.ts` | Фильтры марки, станции, заводского номера, чертежа клапана, очистка и выбор турбины. |
| **`StockSelectionPage`** | `tests/pages/StockSelectionPage.ts` | Установка `quantity` клапанов, проверка блокировки кнопки «Далее», кнопка «Изменить проект». |
| **`StockInputPage`** | `tests/pages/StockInputPage.ts` | Ввод $P_{fresh}$, переключение $T \leftrightarrow H$, ввод давлений в камерах отсосов, проверка ошибок. |
| **`ResultsPage`** | `tests/pages/ResultsPage.ts` | Проверка таблиц участков, потребителей и сводки, выгрузка Excel, генерация Draw.io. |
| **`SidebarHistory`** | `tests/pages/SidebarHistory.ts` | Открытие/закрытие Drawer, выбор записи по ID, удаление элемента и полная очистка. |

---

## 🛠 Хелперы и утилиты

* **`form-fillers.ts`**: Содержит функцию `navigateToStep3WithSelectedValves()`, позволяющую тестам шагов 3 и 4 моментально проходить предварительные шаги выбора оборудования.
* **`localStorage.ts`**: Содержит функции прямого чтения (`getHistoryFromLocalStorage`), записи (`setHistoryInLocalStorage`), генерации (`generateMockHistoryEntries`) и очистки истории расчетов с отправкой браузерного события `wsaHistoryUpdated`.
* **`postMessage.ts`**: Устанавливает перехватчик `window.parent.postMessage` через `page.addInitScript()`, позволяет асинхронно дожидаться сообщений нужного типа (`waitForPostMessage`) и валидировать их payload.
* **`test-utils.ts`**: Содержит слушатели ошибок браузерной консоли (`assertNoConsoleErrors`).

---

## 📦 Каталог моковых данных

| Файл мока | Эндпоинт API | Описание структуры |
| :--- | :--- | :--- |
| **`turbines-search.json`** | `GET /api/v1/turbines/search` | Массив найденных турбин с метаданными станции, зав. номером и списком клапанов. |
| **`turbine-valves.json`** | `GET /api/v1/turbines/{id}/valves` | Детальный список клапанов для выбранной турбины с типами (`РК`, `СК`) и числом участков. |
| **`units.json`** | `GET /api/v1/utils/units` | Справочник доступных размерностей давления, температуры и энтальпии. |
| **`calculation-result.json`**| `POST /api/v1/calculations/calculate` | Ответ мульти-расчета с массивами $G_i, P_i, T_i, H_i$, свойствами деаэратора и эжекторов. |
| **`calculation-error.json`** | `POST /api/v1/calculations/calculate` | Ответ со статусом ошибки 500/400 и описанием причины сбоя. |

---

## 📝 Детальный реестр всех тестовых наборов

### 1. Инфраструктура (`smoke.infra.spec.ts`)
* `[SMOKE-01]` **Проверка тестовой среды:** Проверяет запуск Vite на согласованном порту `3001`, успешный рендеринг и отсутствие ошибок инициализации.

### 2. Оболочка, меню и 404 (`smoke.navigation.spec.ts`)
* `[NAV-01]` **Главная страница:** Проверка заголовка `WSAPropertiesCalculator`, 3 feature-карточек и перехода по CTA-кнопке на `/calculator`.
* `[NAV-02]` **Меню навигации:** Проверка роутинга между статичными страницами `/about` и `/help`.
* `[NAV-03]` **Раздел Help (FAQ):** Проверка раскрытия первого вопроса в аккордеоне и видимости ответа.
* `[NAV-04]` **Раздел About:** Успешная загрузка страницы «О программе» без сбоев.
* `[NAV-05]` **Страница 404 NotFound:** Перехват неизвестного URL `/unknown-route`, отображение ошибки `404 / Page not found` и возврат на главную по кнопке «Go back».

### 3. Шаг 1: Поиск турбин (`calculator.turbine-search.spec.ts`)
* `[STEP1-01]` **Пустое состояние:** Проверка отсутствия лишних сетевых запросов при пустых фильтрах (подсказка *«Введите параметры для поиска»*).
* `[STEP1-02]` **Поиск по марке турбины:** Проверка работы debounce (500 мс) и корректного рендеринга карточек результатов.
* `[STEP1-03]` **Комплексная фильтрация:** Проверка одновременной фильтрации по станции, заводскому номеру и чертежу клапана в query-параметрах.
* `[STEP1-04]` **Кнопка «Очистить»:** Полный сброс значений всех инпутов фильтрации и возврат к пустому состоянию.
* `[STEP1-05]` **Выбор турбины:** Клик по найденной турбине скрывает экран поиска и открывает Шаг 2.
* `[STEP1-06]` **Ошибка сервера (500):** Показ красного блока *«Произошла ошибка при поиске!»* с деталями от бэкенда без падения UI.
* `[STEP1-07]` **Пустой результат:** Отображение сообщения *«Проекты не найдены. Попробуйте изменить критерии поиска.»*.

### 4. Шаг 2: Выбор клапанов (`calculator.stock-selection.spec.ts`)
* `[STEP2-01]` **Загрузка клапанов:** Отображение списка клапанов выбранной турбины с бейджами типов (`РК`, `СК`) и числом участков.
* `[STEP2-02]` **Блокировка перехода:** Кнопка «Далее» заблокирована (`disabled`) при `totalSelected = 0`.
* `[STEP2-03]` **Указание количества:** Ввод `quantity` для одного и нескольких клапанов с динамическим обновлением счётчика на кнопке `Далее (Выбрано: N)`.
* `[STEP2-04]` **Кнопка «Изменить проект»:** Корректный возврат на Шаг 1 к поиску турбины.
* `[STEP2-05]` **Переход на Шаг 3:** Переход к вводу параметров с передачей выбранного состава клапанов.
* `[STEP2-06]` **Пустой список клапанов:** Отображение сообщения *«Для данного проекта клапаны не найдены.»*.

### 5. Шаг 3: Ввод параметров и валидация (`calculator.stock-input.spec.ts`)
* `[STEP3-01]` **Дефолтные значения:** Проверка глобальных параметров ($P_{fresh} = 130$, $t_{fresh} = 555$, $P_{air} = 1.033$, $T_{air} = 20$, $P_{lst} = 0.97$).
* `[STEP3-02]` **Переключение $T \leftrightarrow H$:** Переключение режимов между «Температура» ($t_{fresh}$) и «Энтальпия» ($h_{fresh} = 832.9$).
* `[STEP3-03]` **Геометрия отсосов:** Динамическое формирование полей давлений в камерах по формуле $count\_parts - 2$.
* `[STEP3-04]` **Валидация полей:** Проверка ошибок обязательности, запрета буквенного ввода и ограничения точности (не более 4 знаков после запятой).
* `[STEP3-05]` **Смена единиц и отправка расчёта:** Смена размерности на `МПа`, валидация сформированного тела `MultiCalculationParams` и переход к результатам.
* `[STEP3-06]` **Кнопка «Изменить состав клапанов»:** Возврат на Шаг 2 с сохранением состояния.

### 6. Шаг 4: Результаты, Excel, Draw.io (`calculator.results.spec.ts`)
* `[STEP4-01]` **Happy Path отображения таблиц:** Проверка рендеринга Таблицы 1 (участки), Таблицы 2 (потребители) и Итоговой сводной таблицы отсосов.
* `[STEP4-02]` **Параметры $G, P, T, H$:** Отображение расчётных величин расходов, давлений, температур и энтальпий.
* `[STEP4-03]` **Сводка отсосов:** Отображение бейджей и строк деаэратора и эжекторов.
* `[STEP4-04]` **Экспорт в Excel:** Клик по кнопке «Скачать Excel», генерация книги XLSX и появление toast-уведомления *«Excel файл успешно создан»*.
* `[STEP4-05]` **Генерация Draw.io:** Скачивание сгенерированного файла `.drawio`.
* `[STEP4-06]` **Ошибка генерации Draw.io:** Показ toast-уведомления об ошибке при 500 статусе сервиса схем.
* `[STEP4-07]` **Ошибка API расчёта (500):** Показ toast-ошибки с деталями от сервера и сохранение пользователя на Шаге 3 без перехода на пустой экран результатов.
* `[STEP4-08]` **Кнопка «Изменить параметры расчета»:** Возврат на Шаг 3 с сохранением всех ранее заполненных полей.

### 7. Локальная история расчётов (`calculator.history.spec.ts`)
* `[HIST-01]` **Автосохранение:** Появление записи в истории сразу после успешного расчёта без перезагрузки страницы (`wsaHistoryUpdated`).
* `[HIST-02]` **Отображение списка:** Открытие Sidebar с выводом сохранённых карточек, чертежей и времени расчёта.
* `[HIST-03]` **Восстановление по ID:** Клик по записи в истории, запрос расчёта по ID из БД и переход на экран результатов.
* `[HIST-04]` **Очистка всей истории:** Удаление всех записей из UI и полная очистка ключа `wsaCalculatorHistory` в `localStorage`.
* `[HIST-05]` **Лимит 20 записей:** Добавление 21-го расчёта и проверка вытеснения самой старой записи.
* `[HIST-06]` **Ошибка битого ID:** Обработка ошибки 500 при загрузке несуществующего расчёта с показом toast-ошибки и возвратом к поиску.

### 8. Iframe-интеграция с Balance+ (`calculator.embedded.spec.ts`)
* `[EMBED-01]` **Режим `?embedded=true`:** Отображение кнопок «Сохранить в Balance+» / «Вернуться в Balance+» и скрытие стандартных кнопок.
* `[EMBED-02]` **Событие `WSA_CALCULATION_COMPLETE`:** Отправка сообщения родительскому окну через `window.parent.postMessage` с полной полезной нагрузкой (`input`, `output`, `stockId`).
* `[EMBED-03]` **Событие `WSA_CLOSE`:** Отправка сообщения закрытия при клике на кнопку «Вернуться в Balance+».
* `[EMBED-04]` **Known Gap (#VALVE-GAP-01):** Зафиксирован статус входящего слушателя `WSA_RESTORE_STATE` (помечен `test.skip` до реализации на стороне роутера).
* `[EMBED-05]` **Standalone режим:** Проверка отсутствия интеграционных кнопок и postMessage при запуске без параметра `embedded=true`.

### 9. Сквозной Happy Path CI (`calculator.happy-path.spec.ts`)
* `[HAPPY-MOCK]` **Сквозной сценарий «Как инженер» на моках:** Полный проход от Главной страницы через все 4 шага визарда до генерации отчёта Excel (время выполнения < 5 сек).

### 10. Сквозной Live Happy Path (`calculator.happy-path.live.spec.ts`)
* `[HAPPY-LIVE]` **Сквозной сценарий на живом бэкенде (`@live`):** Проверка работы против реального API на порту `:5253` со встроенным **Smart Fallback** механизмом (автоматическая подстановка моков при пустой БД или сбоях сети).

---

## ⚙️ Конфигурация и особенности окружения

1. **Единый порт разработки:**  
   Vite Dev Server и Playwright BaseURL согласованы на порту `http://127.0.0.1:3001`.

2. **Автоподдержка системного Chromium (Linux / Arch Linux):**  
   Конфигурация `playwright.config.ts` автоматически проверяет наличие системного `/usr/bin/chromium`. Если тесты запускаются в среде без предустановленных браузеров Playwright, раннер прозрачно использует системный Chromium.

3. **CORS Preflight обработка:**  
   В моках настроена автоматическая обработка HTTP `OPTIONS` запросов со статусом `204 No Content` и заголовками `Access-Control-Allow-Origin: *`, что исключает блокировку браузером кросс-доменных вызовов к API бэкенда (`http://localhost:5253`).

4. **Изоляция URL в регулярных выражениях:**  
   Все шаблоны перехвата запросов строго типизированы через регулярные выражения с префиксом `api` (например `/\/api\/.*calc/`), что исключает случайный перехват файлов сборщика Vite.