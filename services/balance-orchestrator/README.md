# Balance Orchestrator

Сервис управляет задачами, ветками, результатами расчётов и Merge Request в
заводском GitLab.

## Настройка GitLab

1. Скопируйте `backend/.env.example` в `backend/.env`.
2. Создайте в GitLab новый Personal Access Token со scope `api`.
3. Запишите токен только в `backend/.env`.
4. Укажите URL и ID проекта:

```dotenv
GITLAB_URL=http://git.utz.local
GITLAB_PRIVATE_TOKEN=<new-token>
GITLAB_PROJECT_ID=41
GITLAB_SSL_VERIFY=false
GITLAB_TIMEOUT=10
```

`GITLAB_SSL_VERIFY=false` предназначен только для внутреннего сервера с
self-signed сертификатом. При наличии доверенного сертификата установите `true`.

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
ALLOWED_ORIGINS=http://localhost:3000
```

Во внешнем `.env` Compose при необходимости можно изменить имя сети:

```dotenv
SHARED_NETWORK_NAME=utz_shared_services
```

Frontend проксирует `/auth/*` в Authentication Service через Nginx. LDAP-пароль
не попадает в backend оркестратора. После входа Axios добавляет access-токен ко
всем запросам `/api/v1/*` и выполняет одноразовую ротацию refresh-токена.

## Запуск и диагностика

```bash
docker compose up --build -d
```

- `GET http://localhost:8005/health` — проверка самого API без обращения к GitLab.
- `GET http://localhost:8005/health/gitlab` — проверка URL, токена и доступа к
  проекту по умолчанию. Токен в ответ никогда не включается.
- `GET http://localhost:8005/api/v1/config/bureaus` без Bearer-токена должен
  возвращать `401 Unauthorized`.

Если `/health/gitlab` сообщает сетевую ошибку, сначала проверьте, что имя
`git.utz.local` разрешается внутри контейнера. При отсутствии заводского DNS
необходимо настроить DNS/hosts на Docker-хосте или указать корректный внутренний
URL в `GITLAB_URL`.
