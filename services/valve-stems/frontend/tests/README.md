# 🧪 Тестовая инфраструктура модуля Valve Stems (E2E)

Настоящая директория содержит инфраструктуру автотестирования для фронтенд-сервиса `valve-stems`.

---

## 📁 Структура каталогов

* `tests/e2e/` — E2E спеки и сценарии (включая `smoke.infra.spec.ts`).
* `tests/pages/` — Page Object классы (`BasePage.ts`, `MainPage.ts`).
* `tests/mocks/` — Перехват и мокирование REST API (`api-mocks.ts`).
* `tests/fixtures/` — Фикстуры тестовых данных (`test-data.ts`).
* `tests/helpers/` — Вспомогательные функции (`test-utils.ts`).

---

## ⚙️ Согласование портов и конфигурация

* **Vite Dev Server:** `http://127.0.0.1:3001`
* **Playwright BaseURL:** `http://127.0.0.1:3001`
* **StorageState:** Отключен (авторизация в модуле не требуется).

---

## 🚀 Команды запуска

Перед запуском убедитесь, что установлены npm зависимости:
```bash
cd services/valve-stems/frontend
npm install
```

### Запуск тестов:

* **Запуск E2E тестов в headless режиме:**
  ```bash
  npm run test:e2e
  ```

* **Запуск в интерактивном UI режиме:**
  ```bash
  npm run test:e2e:ui
  ```

* **Запуск для CI/CD:**
  ```bash
  npm run test:e2e:ci
  ```

---

## 🌐 Режимы запуска (Backend vs Mocks)

1. **Режим с моками (по умолчанию):**  
   Запросы к бэкендуавтоматически эмулируются файлом `tests/mocks/api-mocks.ts`. Запуск бэкенда **не требуется**.

2. **Режим с реальным бэкендом:**  
   Запустите бэкенд на `http://localhost:5253` или через `docker compose up -d` перед запуском спеков без вызова моков.