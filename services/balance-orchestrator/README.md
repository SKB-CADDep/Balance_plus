# Balance Orchestrator

Сервис управляет задачами, ветками, результатами расчётов и Merge Request в
заводском GitLab.

## Вход через GitLab

Оркестратор работает с GitLab от имени вошедшего пользователя. Authentication
Service получает персональный OAuth token, хранит его зашифрованно и передаёт
оркестратору только по внутреннему API. Общий Personal Access Token не нужен.

В `backend/.env` укажите:

```dotenv
GITLAB_URL=https://git.utz.local
GITLAB_AUTH_MODE=oauth
GITLAB_PROJECT_ID=41
GITLAB_SSL_VERIFY=true
GITLAB_TIMEOUT=10
AUTH_SERVICE_CLIENT_SECRET=<same-value-as-auth-service>
```

`GITLAB_PRIVATE_TOKEN` допускается только при временном
`GITLAB_AUTH_MODE=legacy`. После перехода на OAuth старый токен следует отозвать.
Для внутреннего CA добавьте его сертификат в trust store контейнера, не отключая
TLS-проверку.

## Настройка Authentication Service

Оркестратор принимает только access-токены, подтверждённые отдельным
Authentication Service. Оба Compose-проекта подключаются к общей внешней сети,
при этом базы данных и Redis Auth Service остаются в его приватной сети.

Один раз создайте сеть на Docker-хосте:

```bash
docker network create utz_shared_services
```

Сначала запустите Compose-проект Authentication Service, затем — Compose-проект
оркестратора. Порядок остановки обратный; внешняя сеть при `docker compose down`
не удаляется.

Добавьте в `backend/.env`:

```dotenv
AUTH_SERVICE_URL=http://authentication-service:8000
AUTH_SERVICE_TIMEOUT=5
AUTH_SERVICE_CLIENT_SECRET=<same-value-as-auth-service>
ALLOWED_ORIGINS=http://localhost:3000
```

Во внешнем `.env` Compose при необходимости можно изменить имя сети:

```dotenv
SHARED_NETWORK_NAME=utz_shared_services
```

Frontend проксирует `/auth/*` в Authentication Service через Nginx. Вход
начинается на `/auth/gitlab/login`: пользователь вводит заводские LDAP-данные на
стороне GitLab. Callback возвращает во frontend одноразовый код, а не OAuth token.
После его обмена Axios добавляет Balance+ access token ко всем запросам
`/api/v1/*` и выполняет одноразовую ротацию refresh token.

## Запуск и диагностика

Полный локальный OAuth smoke-стенд с GitLab/LDAP-симулятором
описан в [`docs/LOCAL_GITLAB_OAUTH_TEST.md`](../../docs/LOCAL_GITLAB_OAUTH_TEST.md).

```bash
docker compose up --build -d
```

- `GET http://localhost:8005/health` — проверка самого API без обращения к GitLab.
- `GET http://localhost:8005/health/gitlab` — проверка конфигурации режима GitLab.
  Пользовательский token и доступ проверяются на защищённых запросах.
- `GET http://localhost:8005/api/v1/config/bureaus` без Bearer-токена должен
  возвращать `401 Unauthorized`.

Если `/health/gitlab` сообщает сетевую ошибку, сначала проверьте, что имя
`git.utz.local` разрешается внутри контейнера. При отсутствии заводского DNS
необходимо настроить DNS/hosts на Docker-хосте или указать корректный внутренний
URL в `GITLAB_URL`.
