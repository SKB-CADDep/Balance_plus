# schemas/task.py
from pydantic import BaseModel, computed_field
from typing import Optional, List, Dict
from datetime import datetime, date


# --- КОНФИГУРАЦИЯ БЮРО И МОДУЛЕЙ ---

BUREAU_CONFIG = {
    "btr": {
        "name": "БТР",
        "color": "#1976D2",
        "modules": {
            "btr-balances": "Балансы",
            "btr-velocity-triangles": "Треугольники скоростей",
            "btr-steam-distribution": "Парораспределение",
            "btr-condensers": "Конденсаторы",
            "btr-valve-stems": "Штоки клапанов",
            "btr-aux-calcs": "Вспомогательные",
            "btr-wsprop": "WSProp",
            "btr-gasdynamics-ansys": "Газодинамика (Ansys)",
            "btr-thermal-expansions": "Тепловые перемещения"
        }
    },
    "bpr": {
        "name": "БПР",
        "color": "#26A69A",
        "modules": {
            "bpr-flowpath-design": "Проектирование ПЧ",
            "bpr-cylinders": "Цилиндры",
            "bpr-heat-exchangers": "Теплообменники",
            "bpr-materials": "Материалы",
            "bpr-acts": "Акты"
        }
    },
    "bvp": {
        "name": "БВП",
        "color": "#7E57C2",
        "modules": {
            "bvp-static-shaft-deflection": "Прогибы",
            "bvp-static-alignment": "Центровка",
            "bvp-dynamic-bending-vibration": "Изгибные колебания",
            "bvp-dynamic-torsional-vibration": "Крутильные колебания",
            "bvp-working-blades": "Рабочие лопатки"
        }
    }
}

# Обратный маппинг (module::code -> code)
LABEL_TO_MODULE = {}
for b_code, b_data in BUREAU_CONFIG.items():
    for m_code, m_name in b_data["modules"].items():
        # 1. Системный ключ (module::btr-balances)
        LABEL_TO_MODULE[f"module::{m_code}"] = m_code
        # 2. Просто код (btr-balances)
        LABEL_TO_MODULE[m_code] = m_code
        # 3. !!! РУССКИЙ ЛЕЙБЛ ИЗ GITLAB (Модуль::Балансы) !!!
        LABEL_TO_MODULE[f"Модуль::{m_name}"] = m_code
        # 4. На всякий случай просто название (Балансы) - для обратной совместимости
        LABEL_TO_MODULE[m_name] = m_code

# LEGACY_MAPPING для старых английских названий
LEGACY_MAPPING = {
    "valves": "btr-valve-stems"
}
LABEL_TO_MODULE.update(LEGACY_MAPPING)


# Маппинг статусов (Текст лейбла -> Цвет)
STATUS_CONFIG = {
    "Статус::Без исполнителя": {"color": "#9E9E9E", "key": "unassigned"},
    "Статус::Сделать":         {"color": "#B0BEC5", "key": "todo"},
    "Статус::В работе":        {"color": "#1976D2", "key": "in-progress"},
    "Статус::Ожидает данных":  {"color": "#FFA000", "key": "waiting-input"},
    "Статус::На паузе":        {"color": "#7E57C2", "key": "on-hold"},
    "Статус::На проверке":     {"color": "#29B6F6", "key": "in-review"},
    "Статус::На согласовании": {"color": "#26A69A", "key": "in-approval"},
    "Статус::Выполнена":       {"color": "#2E7D32", "key": "done"},
}


class TaskInfo(BaseModel):
    iid: int
    project_id: int
    project_name: str
    title: str
    description: Optional[str] = None
    state: str
    labels: List[str] = []
    assignee: Optional[str] = None
    created_at: datetime
    due_date: Optional[date] = None
    web_url: str

    @computed_field
    def formatted_date(self) -> str:
        return self.created_at.strftime("%d.%m.%y")

    @computed_field
    def bureau(self) -> Optional[Dict[str, str]]:
        """Определяет бюро по лейблу bureau::... / Бюро::... или по модулю"""
        
        # 1. Явный лейбл бюро (Английский и Русский)
        for label in self.labels:
            # Английский: bureau::btr
            if label.startswith("bureau::"):
                code = label.replace("bureau::", "")
                if code in BUREAU_CONFIG:
                    return {"code": code, "name": BUREAU_CONFIG[code]["name"], "color": BUREAU_CONFIG[code]["color"]}
            
            # Русский: Бюро::БТР
            if label.startswith("Бюро::"):
                name = label.replace("Бюро::", "")
                # Ищем код бюро по русскому названию
                for code, data in BUREAU_CONFIG.items():
                    if data["name"] == name:
                        return {"code": code, "name": data["name"], "color": data["color"]}
        
        # 2. Неявный (через модуль) - если лейбла бюро нет, но есть модуль
        module_code = self.calc_type
        if module_code:
            if module_code.startswith("btr-"): return {"code": "btr", "name": "БТР", "color": "#1976D2"}
            if module_code.startswith("bpr-"): return {"code": "bpr", "name": "БПР", "color": "#26A69A"}
            if module_code.startswith("bvp-"): return {"code": "bvp", "name": "БВП", "color": "#7E57C2"}
        
        return None

    @computed_field
    def calc_type(self) -> Optional[str]:
        """Возвращает код модуля (например, 'btr-valve-stems')"""
        for label in self.labels:
            # ИСПОЛЬЗУЕМ LABEL_TO_MODULE ВМЕСТО TYPE_MAPPING
            if label in LABEL_TO_MODULE:
                return LABEL_TO_MODULE[label]
        return None

    @computed_field
    def calc_type_human(self) -> str:
        """Русское название модуля для отображения"""
        code = self.calc_type
        if not code:
            return "Общая задача"
        
        # Ищем в конфиге
        for b_code, b_data in BUREAU_CONFIG.items():
            if code in b_data["modules"]:
                return b_data["modules"][code]
        return code

    @computed_field
    def business_status(self) -> dict:
        """
        Парсим лейбл Статус::...
        Возвращаем dict: { text: 'В работе', color: '#...', key: '...' }
        """
        for label in self.labels:
            if label.startswith("Статус::"):
                config = STATUS_CONFIG.get(label)
                if config:
                    clean_text = label.replace("Статус::", "")
                    return {
                        "text": clean_text,
                        "color": config["color"],
                        "key": config["key"]
                    }
                return {"text": label.replace("Статус::", ""), "color": "#999", "key": "unknown"}

        if self.state == 'closed':
            return {"text": "Закрыто (GitLab)", "color": "#2E7D32", "key": "closed"}

        return {"text": "Новая", "color": "#9E9E9E", "key": "new"}


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    labels: List[str] = []
    project_id: int  # ОБЯЗАТЕЛЬНОЕ ПОЛЕ


class BranchCreate(BaseModel):
    issue_iid: int
    project_id: int


class BranchInfo(BaseModel):
    branch_name: str
    issue_iid: int
    created: bool

class BranchCreateRequest(BaseModel):
    project_id: int