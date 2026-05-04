# .github/scripts/ai_reviewer.py
import os
import re
import time
import json
import requests
from github import Github, Auth
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════

# Лучшая бесплатная coding-модель на май 2026.
# Запасные варианты (раскомментируй если нужно):
# Запасные варианты (раскомментируй если нужно):
# "qwen/qwen3.6-plus-preview:free"  — 1M контекст, reasoning, май 2026
# "moonshotai/kimi-k2:free"         — сильна в агентном коде
# "deepseek/deepseek-r1:free"       — если нужен reasoning
# "openrouter/free"                 — авто-роутер, выберет сам

OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "qwen/qwen3-coder:free")

MAX_DIFF_CHARS   = int(os.environ.get("MAX_DIFF_CHARS", 60_000))
MAX_RETRIES      = 3
RETRY_STATUSES   = {524, 529, 500, 502, 503}

# Reasoning лучше держать выключенным на :free — бесплатные инстансы
# медленнее и легко уходят в Cloudflare 524 при долгом TTFT.
# Включи через env: REASONING_ENABLED=true
REASONING_ENABLED = os.environ.get("REASONING_ENABLED", "false").lower() == "true"


# ═══════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════

def load_system_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.md"
    if prompt_path.exists():
        text = prompt_path.read_text(encoding="utf-8").strip()
        if text:
            return text
    # Дефолтный встроенный промт (см. ниже отдельный файл)
    return _default_system_prompt()


def _default_system_prompt() -> str:
    return """\
Ты — Senior Software Engineer с 15+ годами опыта. Проводишь код-ревью на русском языке.

## Твоя задача
Проанализируй предоставленный diff и дай структурированный отзыв.

## Структура ответа (строго соблюдай)

### 🔴 Критические проблемы
Баги, уязвимости безопасности, утечки памяти, гонки данных.
Если нет — напиши «Не обнаружено».

### 🟡 Улучшения
Производительность, читаемость, нарушения принципов SOLID/DRY/KISS.
Если нет — напиши «Не обнаружено».

### 🟢 Хорошие решения
Что сделано хорошо — обязательно отметь.

### 💡 Рекомендации
Конкретные предложения с примерами кода (если применимо).

### ✅ Итог
Одна строка: можно мёрджить / нужны правки / блокирую мёрдж.

## Правила
- Будь конкретным: указывай файл и строку где возможно.
- Не придирайся к стилю если есть линтер (eslint/flake8/etc).
- Игнорируй изменения в lock-файлах (package-lock.json, poetry.lock и т.п.).
- Если diff слишком большой — сфокусируйся на логике, а не форматировании.
"""


def read_file_safe(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def truncate_diff(diff: str, max_chars: int = MAX_DIFF_CHARS) -> str:
    """
    Обрезает diff умно: сначала убирает lock-файлы,
    потом обрезает по символам если всё ещё большой.
    """
    # Удаляем блоки для lock-файлов (они бесполезны для ревью)
    lock_pattern = re.compile(
        r'diff --git a/.*?(package-lock\.json|poetry\.lock|yarn\.lock|Pipfile\.lock|composer\.lock).*?(?=diff --git|$)',
        re.DOTALL
    )
    diff = lock_pattern.sub('', diff)

    if len(diff) <= max_chars:
        return diff

    return diff[:max_chars] + "\n\n... [DIFF TRUNCATED — слишком большой] ..."


def clean_thinking_tags(text: str) -> str:
    """Удаляет <think>...</think> теги из ответа модели."""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<think>.*', '', text, flags=re.DOTALL)
    return text.strip()


# ═══════════════════════════════════════════════════════════════
# STREAMING-ВЫЗОВ OPENROUTER
# ═══════════════════════════════════════════════════════════════

def call_openrouter(system_prompt: str, user_prompt: str) -> str:
    """
    Вызывает OpenRouter через streaming (SSE).
    Streaming критически важен для избежания 524-таймаутов:
    OpenRouter шлёт SSE keep-alive комментарии пока думает,
    и Cloudflare не рвёт соединение.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY не задан")

    payload: dict = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
        "stream": True,  # ← ключевое изменение: стримим чтобы избежать 524
    }

    if REASONING_ENABLED:
        payload["reasoning"] = {"enabled": True}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "GitHub AI Code Reviewer",
    }

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"Попытка {attempt}/{MAX_RETRIES} | модель: {OPENROUTER_MODEL}")
        try:
            result = _stream_request(headers, payload)
            return result
        except RetryableError as e:
            last_error = e
            wait = 2 ** attempt  # 2, 4, 8 секунд
            print(f"  ↳ Ошибка {e}, жду {wait}с перед повтором...")
            time.sleep(wait)
        except Exception as e:
            raise  # не-ретраябельные ошибки пробрасываем сразу

    raise Exception(f"Все {MAX_RETRIES} попытки исчерпаны. Последняя ошибка: {last_error}")


class RetryableError(Exception):
    pass


def _stream_request(headers: dict, payload: dict) -> str:
    """Делает streaming-запрос и собирает полный текст из чанков."""
    with requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        stream=True,
        timeout=(10, 300),  # (connect_timeout, read_timeout)
    ) as response:

        print(f"  HTTP статус: {response.status_code}")

        if response.status_code in RETRY_STATUSES:
            raise RetryableError(f"HTTP {response.status_code}")

        if response.status_code != 200:
            body = response.text[:500]
            raise Exception(f"API Error {response.status_code}: {body}")

        return _parse_sse_stream(response)


def _parse_sse_stream(response: requests.Response) -> str:
    """Парсит Server-Sent Events и собирает контент из дельта-чанков."""
    full_content = []
    last_finish_reason = None

    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            continue

        # SSE keep-alive комментарии (начинаются с ':') — игнорируем
        if raw_line.startswith(":"):
            continue

        if raw_line.startswith("data: "):
            data_str = raw_line[6:].strip()

            if data_str == "[DONE]":
                break

            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            # Проверяем ошибки внутри стрима
            if "error" in chunk:
                err = chunk["error"]
                code = err.get("code", 0)
                msg  = err.get("message", str(err))
                if code in RETRY_STATUSES:
                    raise RetryableError(f"Stream error {code}: {msg}")
                raise Exception(f"Stream API error {code}: {msg}")

            choices = chunk.get("choices", [])
            if not choices:
                continue

            choice = choices[0]
            delta  = choice.get("delta", {})

            # Собираем контент
            content_piece = delta.get("content")
            if content_piece:
                full_content.append(content_piece)

            # Запоминаем причину остановки
            finish_reason = choice.get("finish_reason")
            if finish_reason:
                last_finish_reason = finish_reason

    result = "".join(full_content)
    result = clean_thinking_tags(result)

    if not result.strip():
        raise RetryableError("Пустой ответ от модели")

    print(f"  Стрим завершён. finish_reason={last_finish_reason}, символов={len(result)}")
    return result


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main() -> int:
    print("=" * 60)
    print("Starting AI Code Review")
    print(f"Model            : {OPENROUTER_MODEL}")
    print(f"Max diff chars   : {MAX_DIFF_CHARS}")
    print(f"Reasoning enabled: {REASONING_ENABLED}")
    print("=" * 60)

    github_token = os.environ.get("GITHUB_TOKEN")
    pr_number    = int(os.environ.get("PR_NUMBER", 0))
    repo_name    = os.environ.get("REPO_NAME", "")
    pr_title     = os.environ.get("PR_TITLE", "Untitled")
    pr_body      = os.environ.get("PR_BODY") or "No description"
    pr_author    = os.environ.get("PR_AUTHOR", "unknown")

    if not all([github_token, pr_number, repo_name]):
        print("❌ Отсутствуют обязательные env-переменные (GITHUB_TOKEN / PR_NUMBER / REPO_NAME)")
        return 1

    diff          = read_file_safe("pr_diff.txt")
    changed_files = read_file_safe("changed_files.txt")

    if not diff.strip():
        print("Diff пустой — пропускаем ревью.")
        return 0

    diff_for_review = truncate_diff(diff)
    print(f"Diff: {len(diff)} → {len(diff_for_review)} символов после обрезки")

    system_prompt = load_system_prompt()

    user_prompt = (
        "## Pull Request для ревью\n\n"
        f"**Автор:** @{pr_author}\n"
        f"**Название:** {pr_title}\n\n"
        f"**Описание:**\n{pr_body}\n\n"
        "---\n\n"
        f"**Изменённые файлы:**\n```\n{changed_files}\n```\n\n"
        f"**Diff:**\n```diff\n{diff_for_review}\n```\n\n"
        "---\n\nПроведи код-ревью этого PR."
    )

    print("Вызываем модель...")

    try:
        review_text = call_openrouter(system_prompt, user_prompt)
        print(f"✅ Ревью получено ({len(review_text)} символов)")
    except Exception as e:
        review_text = (
            f"**⚠️ Ошибка AI-ревьюера:** `{e}`\n\n"
            f"Попробуй перезапустить workflow или проверь логи."
        )
        print(f"❌ Ошибка: {e}")

    print("Постим комментарий в PR...")

    try:
        gh   = Github(auth=Auth.Token(github_token))
        repo = gh.get_repo(repo_name)
        pr   = repo.get_pull(pr_number)

        model_label = OPENROUTER_MODEL.split("/")[-1]  # "qwen3-coder-480b:free"

        comment = (
            "## 🤖 AI Code Review\n\n"
            f"{review_text}\n\n"
            "---\n"
            f"<sub>Model: `{model_label}` via OpenRouter · "
            f"Diff: {len(diff_for_review):,} chars</sub>"
        )

        pr.create_issue_comment(comment)
        print("✅ Комментарий опубликован!")

    except Exception as e:
        print(f"❌ Не удалось опубликовать комментарий: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
