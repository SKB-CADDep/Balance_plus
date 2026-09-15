# Развёртывание Balance+ с GitLab OAuth

**Назначение:** инструкция для DevOps по переходу оркестратора с общего
GitLab Personal Access Token на пользовательскую OAuth-авторизацию.

**Целевая среда:** Kubernetes, заводской GitLab `git.utz.local` с уже
настроенной LDAP-аутентификацией.

## 1. Как работает авторизация

1. Пользователь нажимает «Войти через GitLab» в Balance+.
2. GitLab проверяет его заводскую учётную запись через существующий LDAP.
3. Если пользователь существует и активен в GitLab, GitLab возвращает OAuth
   authorization code в Authentication Service.
4. Authentication Service проверяет OAuth state и PKCE, получает GitLab
   access/refresh tokens, шифрует их и сохраняет в PostgreSQL.
5. Frontend получает только одноразовый код Balance+, а после его обмена —
   собственные JWT Balance+.
6. При обращении к `/api/v1/*` оркестратор запрашивает у Authentication Service
   актуальный GitLab token пользователя через внутренний endpoint.
7. Issue, branch, commit и Merge Request создаются в GitLab от имени вошедшего
   пользователя.

Balance+ не создаёт GitLab-аккаунты. Если аккаунта нет, он заблокирован или
LDAP-вход не проходит, пользователь не получает доступ к оркестратору.

## 2. Создание OAuth Application в GitLab

В административной панели `git.utz.local` создать instance-wide OAuth
Application:

| Параметр | Значение |
| --- | --- |
| Name | `Balance+` |
| Redirect URI | `https://<balance-host>/auth/gitlab/callback` |
| Confidential | включено |
| Trusted | рекомендуется включить |
| Scope | `api` |

Redirect URI должен посимвольно совпадать с `GITLAB_OAUTH_REDIRECT_URI` в
Authentication Service. После создания сохранить Application ID и Secret.

Изменять существующую интеграцию GitLab с LDAP не требуется.

## 3. Secrets

Секреты следует передавать через принятый на площадке механизм: Vault,
External Secrets, Sealed Secrets или защищённые CI/CD variables. Не передавать
значения в аргументах команд и не выводить их в логи.

| Переменная | Компонент | Назначение |
| --- | --- | --- |
| `GITLAB_OAUTH_CLIENT_SECRET` | Authentication Service | Secret OAuth Application |
| `GITLAB_TOKEN_ENCRYPTION_KEY` | Authentication Service | шифрование GitLab tokens в БД |
| `ORCHESTRATOR_SERVICE_SECRET` | Authentication Service | защита внутреннего token endpoint |
| `AUTH_SERVICE_CLIENT_SECRET` | Orchestrator | то же значение, что `ORCHESTRATOR_SERVICE_SECRET` |
| `SECRET_KEY` | Authentication Service | подпись JWT Balance+ |
| `DATABASE_URL` | Authentication Service и migration Job | подключение к PostgreSQL |
| `REDIS_URL` | Authentication Service | OAuth state и refresh-token state |
| `GITLAB_OAUTH_CLIENT_ID` | Authentication Service | ID OAuth Application |

Fernet key для `GITLAB_TOKEN_ENCRYPTION_KEY` можно сгенерировать на защищённой
рабочей станции:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

`GITLAB_TOKEN_ENCRYPTION_KEY` нельзя менять без отдельной процедуры ротации:
сохранённые пользовательские GitLab tokens перестанут расшифровываться.
Изменение `SECRET_KEY` завершит существующие пользовательские сессии Balance+.

## 4. ConfigMap Authentication Service

```dotenv
AUTH_MODE=gitlab_oauth
FRONTEND_URL=https://<balance-host>
ALLOWED_ORIGINS=https://<balance-host>

GITLAB_URL=https://git.utz.local
GITLAB_OAUTH_REDIRECT_URI=https://<balance-host>/auth/gitlab/callback
GITLAB_OAUTH_SCOPES=api
GITLAB_SSL_VERIFY=true

OAUTH_STATE_TTL_SECONDS=300
OAUTH_LOGIN_CODE_TTL_SECONDS=60
```

Опциональное ограничение доступа:

```dotenv
GITLAB_REQUIRED_PROJECT_ID=41
GITLAB_REQUIRED_GROUP_ID=
```

Если оба параметра не заданы, войти может любой активный пользователь GitLab.
Если указан project/group, GitLab должен подтвердить доступ пользователя к
этому ресурсу.

Остальные обязательные настройки Authentication Service сохраняются:
`JWT_ISSUER`, `JWT_AUDIENCE`, сроки жизни JWT и параметры подключения к БД и
Redis.

## 5. ConfigMap оркестратора

```dotenv
GITLAB_URL=https://git.utz.local
GITLAB_AUTH_MODE=oauth
GITLAB_PROJECT_ID=41
GITLAB_SSL_VERIFY=true
GITLAB_TIMEOUT=10

AUTH_SERVICE_URL=http://authentication-service:8000
AUTH_SERVICE_TIMEOUT=5
ALLOWED_ORIGINS=https://<balance-host>
```

После перехода удалить из production-конфигурации:

```dotenv
GITLAB_PRIVATE_TOKEN
GITLAB_TOKEN
```

Старый общий PAT отозвать в GitLab только после успешной приёмочной проверки.

## 6. Внутренний центр сертификации

Если сертификат `git.utz.local` подписан внутренним CA:

1. Добавить сертификат CA в trust store образа или контейнера Authentication
   Service.
2. Добавить тот же CA в trust store оркестратора.
3. При использовании отдельного файла в Authentication Service указать:

   ```dotenv
   GITLAB_CA_BUNDLE=/etc/ssl/certs/utz-root-ca.crt
   ```

В production не использовать `GITLAB_SSL_VERIFY=false`.

## 7. Service DNS, Ingress и NetworkPolicy

Текущий frontend Nginx ожидает следующие Kubernetes Service DNS:

```text
backend:8000
authentication-service:8000
```

Маршрутизация:

```text
https://<balance-host>/        -> frontend
https://<balance-host>/api/*   -> frontend Nginx -> backend:8000
https://<balance-host>/auth/*  -> frontend Nginx -> authentication-service:8000
backend -> /internal/gitlab/token -> authentication-service:8000
```

`/internal/*` не должен публиковаться через Ingress.

NetworkPolicy должна разрешать:

- Ingress Controller -> frontend;
- frontend -> backend и `authentication-service`;
- backend -> `authentication-service` и `git.utz.local`;
- Authentication Service -> PostgreSQL, Redis и `git.utz.local`.

PostgreSQL и Redis наружу не публиковать. Требуется Redis 6.2 или новее;
рекомендуется Redis 7.

## 8. Миграция базы данных

До обновления Authentication Service выполнить отдельный Kubernetes Job из
того же application image:

```bash
alembic upgrade head
```

Job должен получить тот же `DATABASE_URL`, что и Authentication Service. После
успешного выполнения в PostgreSQL должна присутствовать таблица:

```text
user_gitlab_identities
```

Миграция добавляющая: таблица `users` и существующие пользовательские данные не
удаляются.

## 9. Порядок rollout

Предпочтительный вариант — blue-green deployment:

1. Создать OAuth Application в GitLab.
2. Подготовить Secrets, ConfigMaps и внутренний CA.
3. Проверить PostgreSQL и Redis.
4. Выполнить migration Job и дождаться успешного завершения.
5. Развернуть новую версию Authentication Service.
6. Развернуть новый orchestrator backend.
7. Развернуть frontend.
8. Переключить Ingress на новую версию.
9. Выполнить smoke-проверку.
10. Отозвать старый общий GitLab PAT.

Если blue-green недоступен, выполнять переключение в короткое окно
обслуживания. Старые JWT-сессии не содержат GitLab-привязку, поэтому
пользователям потребуется выйти и войти заново через GitLab.

Репозиторий Authentication Service разворачивается раньше Balance+. Изменения
в этих репозиториях должны попасть в релиз согласованно.

## 10. Health probes

| Компонент | Probe | Ожидаемый результат |
| --- | --- | --- |
| Authentication Service | `GET /health` | `200`, БД `connected` |
| Orchestrator backend | `GET /health` | `200` |
| Frontend | `GET /` | `200` |

Authentication Service должен запускаться только после готовности PostgreSQL и
Redis. Backend — после готовности Authentication Service.

## 11. Приёмочная проверка

После rollout проверить:

1. Health probes всех компонентов возвращают `200`.
2. `/api/v1/config/bureaus` без Bearer token возвращает `401`.
3. Пользователь с существующим GitLab-аккаунтом проходит LDAP-вход на стороне
   GitLab и возвращается в Balance+.
4. Пользователь видит только доступные ему проекты и задачи.
5. Issue, branch, commit и Merge Request создаются от имени вошедшего
   пользователя, а не сервисной учётной записи.
6. Пользователь без GitLab-аккаунта или с заблокированным аккаунтом не входит.
7. Повторный вход существующего пользователя проходит успешно.
8. После истечения GitLab access token выполняется refresh-token rotation.
9. Одноразовый frontend login code нельзя обменять повторно.
10. GitLab access/refresh tokens отсутствуют в URL, frontend storage и логах.
11. В логах нет `MissingGreenlet`, ошибок OAuth state, расшифровки token или
    HTTP 5xx.

## 12. Откат

Возвращать предыдущие образы Authentication Service, backend и frontend нужно
согласованно.

Откатывать миграцию необязательно: новая таблица не мешает старой версии. Не
удалять `user_gitlab_identities` без отдельного решения, поскольку таблица
содержит пользовательские OAuth-привязки.

Простого переключения `AUTH_MODE=legacy` недостаточно: новый frontend больше
не содержит форму логина и пароля. Для полноценного legacy-отката нужны
предыдущий frontend, предыдущая согласованная версия сервисов и общий PAT.

## 13. Локальная репетиция

Перед production rollout процесс можно воспроизвести на локальном
GitLab/LDAP-симуляторе. Инструкция находится в
[`docs/LOCAL_GITLAB_OAUTH_TEST.md`](../LOCAL_GITLAB_OAUTH_TEST.md).

`docker-compose.oauth-smoke.yml` и симулятор предназначены только для
разработки и не должны разворачиваться на заводском сервере.
