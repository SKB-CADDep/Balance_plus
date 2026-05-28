#!/usr/bin/env python3
"""
Генератор дерева проекта → PROJECT_TREE.md
Запуск: python generate_tree.py
"""

import os
from pathlib import Path
from datetime import datetime

# ============================================================
# НАСТРОЙКИ
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = PROJECT_DIR / "PROJECT_TREE.md"

# Папки, которые нужно ПОЛНОСТЬЮ игнорировать
IGNORE_DIRS = {
    ".git",
    ".idea",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "venv",
    ".venv",
    "env",
    ".env",
    "node_modules",
    ".tox",
    "dist",
    "build",
    "*.egg-info",
    ".eggs",
    "migrations",       # раскомментируй/удали если нужны
}

# Файлы, которые нужно игнорировать (точные имена или расширения)
IGNORE_FILES = {
    ".DS_Store",
    "Thumbs.db",
    ".gitattributes",
    "desktop.ini",
}

# Расширения файлов, которые нужно игнорировать
IGNORE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".exe",
    ".obj",
    ".o",
}

# Максимальная глубина вложенности (None = без ограничений)
MAX_DEPTH = None

# ============================================================
# ЛОГИКА
# ============================================================


def should_ignore_dir(name: str) -> bool:
    """Проверяет, нужно ли игнорировать директорию."""
    if name in IGNORE_DIRS:
        return True
    # Проверка паттернов вроде *.egg-info
    for pattern in IGNORE_DIRS:
        if pattern.startswith("*") and name.endswith(pattern[1:]):
            return True
    return False


def should_ignore_file(name: str) -> bool:
    """Проверяет, нужно ли игнорировать файл."""
    if name in IGNORE_FILES:
        return True
    _, ext = os.path.splitext(name)
    if ext.lower() in IGNORE_EXTENSIONS:
        return True
    return False


def generate_tree(directory: Path, prefix: str = "", depth: int = 0) -> list[str]:
    """
    Рекурсивно строит список строк с деревом каталогов.
    
    Символы:
        ├── элемент (не последний)
        └── элемент (последний)
        │   отступ для вложенных
    """
    if MAX_DEPTH is not None and depth > MAX_DEPTH:
        return []

    lines = []

    try:
        entries = sorted(
            directory.iterdir(),
            key=lambda e: (e.is_file(), e.name.lower())  # папки первыми
        )
    except PermissionError:
        return [f"{prefix}└── [доступ запрещён]"]

    # Фильтруем
    filtered = []
    for entry in entries:
        if entry.is_dir() and should_ignore_dir(entry.name):
            continue
        if entry.is_file() and should_ignore_file(entry.name):
            continue
        # Не включаем сам файл дерева
        if entry == OUTPUT_FILE:
            continue
        filtered.append(entry)

    for i, entry in enumerate(filtered):
        is_last = (i == len(filtered) - 1)
        connector = "└── " if is_last else "├── "
        
        if entry.is_dir():
            lines.append(f"{prefix}{connector}📁 {entry.name}/")
            extension = "    " if is_last else "│   "
            lines.extend(
                generate_tree(entry, prefix + extension, depth + 1)
            )
        else:
            icon = get_file_icon(entry.name)
            lines.append(f"{prefix}{connector}{icon} {entry.name}")

    return lines


def get_file_icon(filename: str) -> str:
    """Возвращает эмодзи-иконку по расширению файла."""
    icons = {
        ".py":       "🐍",
        ".md":       "📝",
        ".txt":      "📄",
        ".json":     "📋",
        ".yaml":     "⚙️",
        ".yml":      "⚙️",
        ".toml":     "⚙️",
        ".cfg":      "⚙️",
        ".ini":      "⚙️",
        ".env":      "🔒",
        ".html":     "🌐",
        ".css":      "🎨",
        ".js":       "📜",
        ".ts":       "📜",
        ".sql":      "🗃️",
        ".db":       "🗃️",
        ".sqlite":   "🗃️",
        ".csv":      "📊",
        ".xlsx":     "📊",
        ".jpg":      "🖼️",
        ".jpeg":     "🖼️",
        ".png":      "🖼️",
        ".svg":      "🖼️",
        ".gif":      "🖼️",
        ".ico":      "🖼️",
        ".log":      "📃",
        ".sh":       "⚡",
        ".bat":      "⚡",
        ".cmd":      "⚡",
        ".dockerfile": "🐳",
        ".gitignore":"🙈",
        ".lock":     "🔒",
        ".req":      "📦",
    }

    name_lower = filename.lower()
    
    # Специальные имена файлов
    if name_lower == "dockerfile":
        return "🐳"
    if name_lower in ("requirements.txt", "setup.py", "setup.cfg", "pyproject.toml"):
        return "📦"
    if name_lower == ".gitignore":
        return "🙈"
    if name_lower in ("makefile", "justfile"):
        return "⚡"
    if name_lower.startswith("readme"):
        return "📖"
    if name_lower.startswith("license"):
        return "⚖️"

    _, ext = os.path.splitext(name_lower)
    return icons.get(ext, "📄")


def count_stats(directory: Path) -> tuple[int, int]:
    """Считает количество папок и файлов (с учётом фильтров)."""
    dirs_count = 0
    files_count = 0
    
    for root, dirs, files in os.walk(directory):
        # Фильтруем директории на месте
        dirs[:] = [d for d in dirs if not should_ignore_dir(d)]
        
        for d in dirs:
            dirs_count += 1
        for f in files:
            if not should_ignore_file(f):
                fp = Path(root) / f
                if fp != OUTPUT_FILE:
                    files_count += 1
    
    return dirs_count, files_count


def build_markdown() -> str:
    """Собирает полный markdown-документ."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tree_lines = generate_tree(PROJECT_DIR)
    dirs_count, files_count = count_stats(PROJECT_DIR)

    parts = [
        f"# 🌳 Дерево проекта: {PROJECT_DIR.name}",
        "",
        f"> Автоматически сгенерировано: `{now}`  ",
        f"> Директорий: **{dirs_count}** | Файлов: **{files_count}**",
        "",
        "```",
        f"{PROJECT_DIR.name}/",
        *tree_lines,
        "```",
        "",
        "---",
        "",
        "<details>",
        "<summary>🚫 Игнорируемые директории</summary>",
        "",
        ", ".join(f"`{d}`" for d in sorted(IGNORE_DIRS)),
        "",
        "</details>",
        "",
    ]

    return "\n".join(parts)


def main():
    print(f"🔍 Сканирую: {PROJECT_DIR}")
    print(f"📝 Выходной файл: {OUTPUT_FILE}")
    print()

    if not PROJECT_DIR.exists():
        print(f"❌ Директория не найдена: {PROJECT_DIR}")
        return

    content = build_markdown()
    
    OUTPUT_FILE.write_text(content, encoding="utf-8")

    dirs_count, files_count = count_stats(PROJECT_DIR)
    print(f"✅ Дерево успешно сгенерировано!")
    print(f"   📁 Директорий: {dirs_count}")
    print(f"   📄 Файлов:     {files_count}")
    print(f"   💾 Сохранено:  {OUTPUT_FILE}")


if __name__ == "__main__":
    main()