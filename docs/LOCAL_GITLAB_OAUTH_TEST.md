# Локальная проверка GitLab OAuth

Стенд проверяет полный контракт Balance+: имитацию LDAP-входа в GitLab,
OAuth Authorization Code + PKCE, callback, выдачу Balance+ JWT, получение
персонального GitLab token оркестратором и создание issue, branch и Merge
Request от имени пользователя.

Это не замена единственной приёмочной проверке на `git.utz.local`: LDAP
находится внутри GitLab, поэтому настройки LDAP самого GitLab проверяются только
на заводском сервере. Для кода Balance+ симулятор воспроизводит границу
интеграции полностью.

## Автоматическая проверка

Предварительно запустите Docker Desktop. Репозиторий Auth Service
должен быть выкачан в `./authentication-service`, как в текущем рабочем
каталоге. Это отдельный Git-репозиторий и в коммит Balance+ не входит.

Из корня репозитория:

```powershell
docker compose -f docker-compose.oauth-smoke.yml up --build -d --wait
python dev/gitlab-oauth-simulator/smoke.py
```

Ожидаемый результат:

```text
OK: OAuth + PKCE + simulated LDAP + per-user GitLab writes passed
```

## Ручная проверка в браузере

1. Откройте `http://localhost:3030`.
2. Нажмите «Войти через GitLab».
3. На странице GitLab-симулятора введите:
   - логин: `engineer`;
   - пароль: `factory-password`.
4. Убедитесь, что открылся Balance+ и доступны проекты и задачи.
5. Создайте задачу, ветку и Merge Request.
6. Журнал GitLab-вызовов доступен по `http://localhost:8088/__mock__/audit`;
   у всех событий должен быть пользователь `engineer`.

Другой логин или пароль возвращает `401` и имитирует отсутствие/блокировку
учётной записи в GitLab/LDAP.

## Остановка

```powershell
docker compose -f docker-compose.oauth-smoke.yml down
```

Тестовые данные сохраняются в Docker volumes. Удаляйте их только осознанно:

```powershell
docker compose -f docker-compose.oauth-smoke.yml down -v
```

Все пароли и ключи в этом Compose-файле тестовые и предназначены только для
локального стенда. Их нельзя переносить в production.
