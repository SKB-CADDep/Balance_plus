import os
import re
import sys
import yaml
import subprocess

# --- ANSI Цвета для UI ---
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

IGNORE_DIRS = {'.git', 'venv', '.venv', '__pycache__', 'node_modules', '.pytest_cache', '.github'}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def extract_py_description(filepath):
    """Вытаскивает первую строку docstring из класса/модуля .py файла."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if match:
                desc = match.group(1).strip().split('\n')[0]
                return desc if len(desc) <= 60 else desc[:57] + '...'
    except Exception:
        pass
    return "Нет описания"

def extract_yaml_description(filepath):
    """Вытаскивает test_name (Tavern) или description из .yaml файла."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data and isinstance(data, dict):
                # Поддержка Tavern (test_name) и кастомных DB YAML (description)
                desc = str(data.get('test_name', data.get('description', 'Нет описания'))).strip()
                return desc if len(desc) <= 60 else desc[:57] + '...'
    except Exception:
        pass
    return "Нет описания"

def scan_for_test_groups(root_dir):
    groups = {}
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        
        if '__group__.yml' not in filenames:
            continue
            
        group_name = os.path.basename(dirpath)
        group_desc = "Нет описания"
        
        try:
            with open(os.path.join(dirpath, '__group__.yml'), 'r', encoding='utf-8') as f:
                meta = yaml.safe_load(f) or {}
                group_name = meta.get('name', group_name)
                group_desc = meta.get('description', group_desc)
        except Exception:
            pass
            
        test_files =[]
        for file in filenames:
            if file.startswith('test_') and (file.endswith('.py') or file.endswith('.yaml')):
                filepath = os.path.join(dirpath, file)
                
                if file.endswith('.py'):
                    desc = extract_py_description(filepath)
                    file_icon = '🐍'
                else:
                    desc = extract_yaml_description(filepath)
                    # Визуально разделим Tavern API-тесты и DB-тесты
                    file_icon = '🌐' if 'tavern' in file else '🗄️' if 'db' in file else '📄'
                    
                test_files.append({'name': file, 'path': filepath, 'icon': file_icon, 'desc': desc})
        
        if test_files:
            groups[group_name] = {'path': dirpath, 'desc': group_desc, 'files': sorted(test_files, key=lambda x: x['name'])}
            
    return groups

def parse_selection(selection_str, max_val):
    if selection_str.strip() == '#': return list(range(1, max_val + 1))
    indices = set()
    for part in selection_str.split(','):
        part = part.strip()
        if not part: continue
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if 1 <= start <= end <= max_val: indices.update(range(start, end + 1))
            except ValueError: pass
        else:
            try:
                val = int(part)
                if 1 <= val <= max_val: indices.add(val)
            except ValueError: pass
    return sorted(list(indices))

def draw_header(title):
    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD} {title}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}")

def find_project_root(test_path):
    current = os.path.dirname(test_path)
    while current != os.path.dirname(current): 
        if os.path.exists(os.path.join(current, 'pytest.ini')) or os.path.exists(os.path.join(current, 'pyproject.toml')):
            return current
        current = os.path.dirname(current)
    return os.path.dirname(test_path)

# --- ГЛАВНЫЙ ИСПОЛНИТЕЛЬ (ТОЛЬКО PYTEST) ---
def run_tests(selected_files):
    clear_screen()
    draw_header("▶ ЗАПУСК ТЕСТОВ (Оркестрация Pytest)")

    # Группируем ВСЕ выбранные файлы (и py, и yaml) по проектам
    projects = {}
    for f in selected_files:
        root = find_project_root(f['path'])
        rel_path = os.path.relpath(f['path'], root)
        projects.setdefault(root,[]).append(rel_path)
        
    for project_root, files in projects.items():
        print(f"\n{Colors.CYAN}🚀 Запуск тестов (Проект: {os.path.basename(project_root)})...{Colors.RESET}")
        
        # Pytest сам разберется: py отдаст своим функциям, tavern.yaml отдаст плагину Tavern!
        cmd =[sys.executable, "-m", "pytest"] + files + ["-v", "--tb=short", "--color=yes"]
        try:
            subprocess.run(cmd, cwd=project_root)
        except Exception as e:
            print(f"{Colors.RED}❌ Ошибка вызова pytest: {e}{Colors.RESET}")

    print(f"\n{Colors.GRAY}{'-'*80}{Colors.RESET}")
    print(f"{Colors.BOLD}Нажмите Enter, чтобы вернуться в меню...{Colors.RESET}")
    input()

def main_menu():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    while True:
        clear_screen()
        groups = scan_for_test_groups(root_dir)
        group_names = sorted(groups.keys())
        
        draw_header("🚀 УНИВЕРСАЛЬНЫЙ ТЕСТ-РАННЕР")
        
        if not group_names:
            print(f"\n{Colors.RED}Тесты не найдены!{Colors.RESET} Создайте папку с файлом __group__.yml")
            sys.exit(0)
            
        print(f"{Colors.GRAY}Найдены следующие группы тестов:{Colors.RESET}\n")
        
        for i, g_name in enumerate(group_names, 1):
            g_data = groups[g_name]
            file_count = len(g_data['files'])
            print(f"[{Colors.GREEN}{i:2}{Colors.RESET}] {Colors.BOLD}{g_name:<25}{Colors.RESET} {Colors.GRAY}— {g_data['desc']} (файлов: {file_count}){Colors.RESET}")
            
        print(f"\n[{Colors.GREEN}#{Colors.RESET}] Запустить ВСЕ группы")
        print(f"[{Colors.GREEN}q{Colors.RESET}] Выход")
        print(f"{Colors.CYAN}{'-'*80}{Colors.RESET}")
        
        choice = input(f"Введите номер группы или действие: ").strip().lower()
        
        if choice == 'q':
            clear_screen()
            print("Выход из тест-раннера. Хорошего дня! 👋")
            break
        elif choice == '#':
            all_files = [f for g in groups.values() for f in g['files']]
            if all_files: run_tests(all_files)
        else:
            try:
                idx = int(choice)
                if 1 <= idx <= len(group_names):
                    group_menu(groups[group_names[idx-1]], group_names[idx-1])
            except ValueError:
                pass

def group_menu(group_data, group_name):
    while True:
        clear_screen()
        draw_header(f"📂 Группа: {group_name} ({group_data['desc']})")
        
        files = group_data['files']
        for i, f in enumerate(files, 1):
            print(f"[{Colors.GREEN}{i:2}{Colors.RESET}] {f['icon']} {Colors.BOLD}{f['name']:<30}{Colors.RESET} {Colors.GRAY}{f['desc']}{Colors.RESET}")
            
        print(f"\n[{Colors.GREEN}#{Colors.RESET}] Запустить ВСЕ файлы в группе")
        print(f"[{Colors.GREEN}0{Colors.RESET}] Назад")
        print(f"{Colors.CYAN}{'-'*80}{Colors.RESET}")
        
        choice = input(f"Выберите тесты (например 1,3 или 1-3): ").strip()
        
        if choice == '0': break
        selected_indices = parse_selection(choice, len(files))
        if selected_indices:
            selected_files = [files[i-1] for i in selected_indices]
            run_tests(selected_files)

if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nПрервано пользователем. Выход...")
        sys.exit(0)