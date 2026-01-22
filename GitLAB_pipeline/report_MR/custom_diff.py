import os
import json
import yaml
import subprocess
import requests
import sys
import io

# Попытка импорта matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    import matplotlib.colors as mcolors
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("[DEBUG] ❌ Matplotlib is NOT installed!")

# --- НАСТРОЙКИ ---
CI_API_V4_URL = os.environ.get('CI_API_V4_URL')
CI_PROJECT_ID = os.environ.get('CI_PROJECT_ID')
GITLAB_TOKEN = os.environ.get('GITLAB_TOKEN')
CI_MERGE_REQUEST_IID = os.environ.get('CI_MERGE_REQUEST_IID')
CURRENT_BRANCH = os.environ.get('CI_COMMIT_REF_NAME')
TARGET_BRANCH = os.environ.get('CI_MERGE_REQUEST_TARGET_BRANCH_NAME', 'develop')

CONFIG_FILE = 'pattern/view_template.yaml'
HIDDEN_MARKER = "<!-- DIFF_BOT_MARKER_FINAL -->"

# --- ЦВЕТА (Blocked List) ---
BLOCKED_COLORS = [
    'yellow', '#FFFF00', 'lightgray', 'whitesmoke', 'beige', 
    'cornsilk', 'lightyellow', 'ivory', 'honeydew'
]

# --- API UPLOAD ---
def upload_image_to_gitlab(image_buffer, filename="chart.png"):
    if not CI_API_V4_URL or not CI_PROJECT_ID or not GITLAB_TOKEN:
        print("[DEBUG] ❌ Cannot upload: No API credentials.")
        return None

    url = f"{CI_API_V4_URL}/projects/{CI_PROJECT_ID}/uploads"
    headers = {'PRIVATE-TOKEN': GITLAB_TOKEN}
    files = {'file': (filename, image_buffer, 'image/png')}

    try:
        r = requests.post(url, headers=headers, files=files, verify=False)
        if r.status_code in [200, 201]:
            return r.json().get('markdown')
        else:
            print(f"[DEBUG] ❌ Upload failed! {r.status_code} {r.text}")
    except Exception as e:
        print(f"[DEBUG] ❌ Upload exception: {e}")
    return None

# --- COLOR UTILS ---
def get_safe_color(base_color):
    try:
        c_rgb = mcolors.to_rgb(base_color)
        blocked_rgbs = [mcolors.to_rgb(bc) for bc in BLOCKED_COLORS]
        is_bad = False
        for b_rgb in blocked_rgbs:
            distance = sum((a - b) ** 2 for a, b in zip(c_rgb, b_rgb)) ** 0.5
            if distance < 0.25: 
                is_bad = True
                break
        if is_bad:
            return (c_rgb[0]*0.6, c_rgb[1]*0.6, c_rgb[2]*0.6, 1.0)
        return base_color
    except Exception:
        return base_color

# --- ГРАФИКИ ---
def generate_local_chart(title, old_x, old_y, old_z, new_x, new_y, new_z, force_draw_all=False):
    """
    force_draw_all: Если True (изменился X), фильтр отключается, рисуем ВСЕ линии.
    """
    if not MATPLOTLIB_AVAILABLE:
        return "**Matplotlib not installed.**"

    try:
        plt.figure(figsize=(11, 6))
        plt.title(title)
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.xlabel("X")
        plt.ylabel("Value")

        old_x = old_x or []
        old_z = old_z or []
        new_x = new_x or []
        new_z = new_z or []

        is_family = (len(old_z) > 0) or (len(new_z) > 0)
        has_anything_plotted = False

        if is_family:
            max_curves = max(len(old_z), len(new_z))
            base_colors = [cm.gist_rainbow(x) for x in np.linspace(0, 0.95, max_curves)]

            for i in range(max_curves):
                # Подготовка данных
                curve_old = old_z[i] if i < len(old_z) else []
                curve_new = new_z[i] if i < len(new_z) else []
                label_val_old = old_y[i] if (old_y and i < len(old_y)) else None
                label_val_new = new_y[i] if (new_y and i < len(new_y)) else None

                # --- ФИЛЬТР ---
                # Если НЕ принудительная отрисовка (X не менялся) 
                # И данные кривой не менялись
                # И подпись не менялась
                # -> Пропускаем
                if not force_draw_all:
                    if str(curve_old) == str(curve_new) and str(label_val_old) == str(label_val_new):
                        continue

                has_anything_plotted = True
                color = get_safe_color(base_colors[i])
                
                label_txt = f"{i+1}"
                if label_val_new is not None: label_txt = f"Y={label_val_new}"
                elif label_val_old is not None: label_txt = f"Y={label_val_old}"

                # Рисуем Старую
                if i < len(old_z) and isinstance(curve_old, list):
                    limit = min(len(old_x), len(curve_old))
                    if limit > 1:
                        plt.plot(old_x[:limit], curve_old[:limit], color=color, linestyle='--', linewidth=1.5, alpha=0.35)

                # Рисуем Новую
                if i < len(new_z) and isinstance(curve_new, list):
                    limit = min(len(new_x), len(curve_new))
                    if limit > 1:
                        plt.plot(new_x[:limit], curve_new[:limit], color=color, linestyle='-', linewidth=2, alpha=1.0, marker='.', markersize=4, label=label_txt)

        else:
            # Одиночная кривая
            has_anything_plotted = True
            if old_x and old_y:
                limit = min(len(old_x), len(old_y))
                if limit > 1:
                    plt.plot(old_x[:limit], old_y[:limit], color='gray', linestyle='--', linewidth=2, label='Было', alpha=0.5)
            if new_x and new_y:
                limit = min(len(new_x), len(new_y))
                if limit > 1:
                    plt.plot(new_x[:limit], new_y[:limit], color='blue', linestyle='-', linewidth=2.5, marker='o', label='Стало')

        if not has_anything_plotted:
            # Если мы здесь, значит force_draw_all=False, но что-то вызвало отрисовку.
            # На всякий случай пишем заглушку.
            plt.text(0.5, 0.5, "Нет визуальных изменений", ha='center', va='center', transform=plt.gca().transAxes)

        plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close()
        
        return upload_image_to_gitlab(buf, filename=f"chart_{title}.png")
    except Exception as e:
        print(f"[DEBUG] ❌ Error drawing chart {title}: {e}")
        return None

# --- UTILS ---
def get_git_file_content(branch, filename):
    try:
        return subprocess.check_output(['git', 'show', f'origin/{branch}:{filename}'], stderr=subprocess.DEVNULL).decode('utf-8')
    except subprocess.CalledProcessError:
        return None

def find_mr_iid():
    if CI_MERGE_REQUEST_IID: return CI_MERGE_REQUEST_IID
    if not CI_API_V4_URL or not CI_PROJECT_ID or not GITLAB_TOKEN: return None
    try:
        url = f"{CI_API_V4_URL}/projects/{CI_PROJECT_ID}/merge_requests"
        params = {'source_branch': CURRENT_BRANCH, 'state': 'opened'}
        headers = {'PRIVATE-TOKEN': GITLAB_TOKEN}
        r = requests.get(url, params=params, headers=headers, verify=False)
        if r.status_code == 200 and r.json(): return r.json()[0]['iid']
    except: pass
    return None

def load_json_file(filepath, from_git_branch=None):
    content = None
    paths = [filepath, filepath + ".json"]
    for p in paths:
        if from_git_branch: content = get_git_file_content(from_git_branch, p)
        elif os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f: content = f.read()
        if content: break
    if not content: return {}
    try: return json.loads(content)
    except: return {}

def try_parse_float(val):
    try: return float(val)
    except (ValueError, TypeError): return None

def format_value(val):
    if val is None: return "null"
    if isinstance(val, float): return f"{val:.2f}"
    s_val = str(val)
    if len(s_val) > 30: return s_val[:30] + "..."
    return s_val

def get_diff_info(v_old, v_new):
    f_old, f_new = try_parse_float(v_old), try_parse_float(v_new)
    if f_old is not None and f_new is not None:
        diff = f_new - f_old
        if abs(diff) < 0.000001: return False, None, None
        return True, f"{diff:+.2f}", ("⬆️" if diff > 0 else "⬇️")
    if str(v_old) != str(v_new):
        if v_old == "N/A": return True, "New", "🆕"
        if v_new == "N/A": return True, "Del", "❌"
        return True, "MOD", "✏️"
    return False, None, None

def find_root(data, config_root_name):
    if config_root_name in data: return data[config_root_name]
    keys = list(data.keys())
    return data[keys[0]] if keys else {}

def list_to_dict_by_id(data_list, id_key):
    res = {}
    if not isinstance(data_list, list): return res
    for item in data_list:
        if isinstance(item, dict):
            key_val = str(item.get(id_key, "Unknown"))
            res[key_val] = item
    return res

# --- PROCESSORS ---
def process_direct_group(old_data, new_data, whitelist):
    rows = []
    all_keys = set(old_data.keys()) | set(new_data.keys())
    for key in sorted(all_keys):
        v_old = old_data.get(key, "N/A")
        v_new = new_data.get(key, "N/A")
        is_changed, diff_txt, icon = get_diff_info(v_old, v_new)
        if is_changed or key in whitelist:
            bold_new = f"**{format_value(v_new)}**" if is_changed else format_value(v_new)
            rows.append(f"| {key} | {format_value(v_old)} | {bold_new} | {icon or ''} {diff_txt or ''} |")
    return rows

def process_list_group(old_list, new_list, lookup_id, whitelist):
    rows = []
    old_map = list_to_dict_by_id(old_list, lookup_id)
    new_map = list_to_dict_by_id(new_list, lookup_id)
    all_ids = set(old_map.keys()) | set(new_map.keys())
    
    for uid in sorted(all_ids):
        obj_old = old_map.get(uid, {})
        obj_new = new_map.get(uid, {})
        obj_exists_old = uid in old_map
        obj_exists_new = uid in new_map
        all_params = set(obj_old.keys()) | set(obj_new.keys())
        if lookup_id in all_params: all_params.remove(lookup_id)
        for param in sorted(all_params):
            v_old = obj_old.get(param, "N/A") if obj_exists_old else "N/A"
            v_new = obj_new.get(param, "N/A") if obj_exists_new else "N/A"
            if isinstance(v_new, (list, dict)) or isinstance(v_old, (list, dict)): continue
            is_changed, diff_txt, icon = get_diff_info(v_old, v_new)
            if is_changed or param in whitelist:
                full_name = f"{uid}.{param}"
                bold_new = f"**{format_value(v_new)}**" if is_changed else format_value(v_new)
                rows.append(f"| {full_name} | {format_value(v_old)} | {bold_new} | {icon or ''} {diff_txt or ''} |")
    return rows

def process_chart_group(old_list, new_list, lookup_id, x_key, y_key, z_key):
    charts_md = ""
    old_map = list_to_dict_by_id(old_list, lookup_id)
    new_map = list_to_dict_by_id(new_list, lookup_id)
    all_ids = set(old_map.keys()) | set(new_map.keys())

    for uid in sorted(all_ids):
        obj_old = old_map.get(uid, {})
        obj_new = new_map.get(uid, {})

        # Данные
        old_x = obj_old.get(x_key, []) or []
        old_y = obj_old.get(y_key, []) or []
        old_z = obj_old.get(z_key, []) or []

        new_x = obj_new.get(x_key, []) or []
        new_y = obj_new.get(y_key, []) or []
        new_z = obj_new.get(z_key, []) or []
        
        # Определяем типы изменений
        x_diff = str(old_x) != str(new_x)
        z_diff = str(old_z) != str(new_z)
        y_diff = str(old_y) != str(new_y)
        
        # 1. Если ничего не изменилось -> Пропуск
        if not x_diff and not z_diff and not y_diff:
            continue
            
        # 2. Если удалено полностью -> Сообщение (можно тоже рисовать, но текст проще)
        if not new_x and not new_z:
            charts_md += f"#### ❌ Удалена кривая: {uid}\n\n"
            continue

        # 3. СЦЕНАРИЙ: Только Y изменился (X и Z те же) -> Текстовый вывод
        if y_diff and not x_diff and not z_diff:
            charts_md += f"#### ✏️ Изменения параметров кривой: {uid}\n"
            # Ищем конкретные изменения в списке Y
            changes_found = False
            
            # Таблица изменений Y
            y_table = "| Индекс | Было | Стало |\n|---|---|---|\n"
            max_len = max(len(old_y), len(new_y))
            for i in range(max_len):
                val_o = old_y[i] if i < len(old_y) else "-"
                val_n = new_y[i] if i < len(new_y) else "-"
                if str(val_o) != str(val_n):
                    y_table += f"| #{i+1} | {val_o} | **{val_n}** |\n"
                    changes_found = True
            
            if changes_found:
                charts_md += y_table + "\n"
            continue

        # 4. СЦЕНАРИЙ: Изменился X или Z -> Рисуем график
        # Если X_diff = True, передаем force_draw_all=True
        print(f"[DEBUG] 📉 Drawing chart for {uid} (X_diff={x_diff}, Z_diff={z_diff})...")
        link = generate_local_chart(f"{uid}", old_x, old_y, old_z, new_x, new_y, new_z, force_draw_all=x_diff)
        
        if link:
            charts_md += f"#### 📈 Кривая: {uid}\n{link}\n\n"
        
    return charts_md

# --- MAIN ---
def main():
    requests.packages.urllib3.disable_warnings()
    if not os.path.exists(CONFIG_FILE):
        print("❌ Config file not found.")
        sys.exit(1)

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f: config = yaml.safe_load(f)
    data_path = config.get('data_file_path', 'calculations/balance/zone')
    
    new_json_full = load_json_file(data_path)
    subprocess.run(['git', 'fetch', 'origin', TARGET_BRANCH], check=False)
    old_json_full = load_json_file(data_path, from_git_branch=TARGET_BRANCH)

    root_name = config.get('root_key_name', 'TEST_1')
    new_data = find_root(new_json_full, root_name)
    old_data = find_root(old_json_full, root_name)

    md_output = "## 📊 Анализ изменений данных\n\n"
    has_content = False

    for group in config['groups']:
        title = group['title']
        g_path = group['path']
        g_type = group['type']
        
        old_sub = old_data.get(g_path)
        new_sub = new_data.get(g_path)

        if not old_sub and not new_sub: continue
        
        if g_type == 'direct':
            whitelist = set(group.get('whitelist', []))
            rows = process_direct_group(old_sub or {}, new_sub or {}, whitelist)
            if rows:
                md_output += f"### {title}\n| Параметр | Было | Стало | Изм. |\n|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
                has_content = True

        elif g_type == 'list_lookup':
            whitelist = set(group.get('whitelist', []))
            lookup_id = group.get('lookup_id', 'NAME')
            rows = process_list_group(old_sub or [], new_sub or [], lookup_id, whitelist)
            if rows:
                md_output += f"### {title}\n| Параметр | Было | Стало | Изм. |\n|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
                has_content = True
        
        elif g_type == 'list_chart':
            lookup_id = group.get('lookup_id', 'NAME')
            x_key = group.get('x_key', 'X')
            y_key = group.get('y_key', 'Y')
            z_key = group.get('z_key', 'Z')
            
            chart_md = process_chart_group(old_sub or [], new_sub or [], lookup_id, x_key, y_key, z_key)
            if chart_md:
                md_output += f"### {title}\n{chart_md}\n"
                has_content = True

    if not has_content:
        md_output += "✅ Изменений в отслеживаемых блоках не найдено."

    print(md_output)
    
    mr_iid = find_mr_iid()
    if mr_iid:
        if len(md_output) > 2500:
             md_output = f"## 📊 Анализ данных (Large)\n<details><summary>Показать полный отчет</summary>\n\n{md_output}\n</details>"
        post_or_update_comment(mr_iid, md_output)
    else:
        print("⚠️ MR IID not found.")

def post_or_update_comment(mr_iid, body):
    if not GITLAB_TOKEN: return
    headers = {'PRIVATE-TOKEN': GITLAB_TOKEN}
    notes_url = f"{CI_API_V4_URL}/projects/{CI_PROJECT_ID}/merge_requests/{mr_iid}/notes"
    full_body = f"{HIDDEN_MARKER}\n{body}"
    try:
        r = requests.get(notes_url, headers=headers, params={'per_page': 100}, verify=False)
        existing_id = None
        if r.status_code == 200:
            for note in r.json():
                if HIDDEN_MARKER in note.get('body', '') and not note.get('system'):
                    existing_id = note['id']
                    break
        if existing_id:
            requests.put(f"{notes_url}/{existing_id}", headers=headers, json={'body': full_body}, verify=False)
        else:
            requests.post(notes_url, headers=headers, json={'body': full_body}, verify=False)
    except Exception as e:
        print(f"❌ Error posting comment: {e}")

if __name__ == "__main__":
    main()
