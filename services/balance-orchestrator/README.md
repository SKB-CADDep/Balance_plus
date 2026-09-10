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

## Запуск и диагностика

```bash
docker compose up --build -d
```

- `GET http://localhost:8005/health` — проверка самого API без обращения к GitLab.
- `GET http://localhost:8005/health/gitlab` — проверка URL, токена и доступа к
  проекту по умолчанию. Токен в ответ никогда не включается.

Если `/health/gitlab` сообщает сетевую ошибку, сначала проверьте, что имя
`git.utz.local` разрешается внутри контейнера. При отсутствии заводского DNS
необходимо настроить DNS/hosts на Docker-хосте или указать корректный внутренний
URL в `GITLAB_URL`.
