# schemas/task.py

"""
Схемы данных и конфигурация для управления расчетными задачами.

Этот модуль отвечает за маппинг (преобразование) сырых данных из внешнего трекера задач 
(например, GitLab Issues) во внутренние сущности системы оркестрации. 
Включает конфигурацию бюро, расчетных модулей, статусов, а также Pydantic-модели
для валидации и обогащения задач бизнес-метаданными через `computed_field`.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field, computed_field


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

# [ENGINEERING CONTEXT]
# Почему используется такой сложный, 4-уровневый маппинг (LABEL_TO_MODULE):
# Трекер задач (GitLab) исторически содержит зоопарк лейблов. Нам нужно "поймать" задачу,
# независимо от того, как пользователь или система её разметили. 
# Этот цикл создает плоский словарь, где любой вариант написания приводит к единому системному коду.

LABEL_TO_MODULE = {}
for _b_code, b_data in BUREAU_CONFIG.items():
    for m_code, m_name in b_data["modules"].items():
        # 1. Системный ключ (module::btr-balances)
        LABEL_TO_MODULE[f"module::{m_code}"] = m_code
        # 2. Просто код (btr-balances)
        LABEL_TO_MODULE[m_code] = m_code
        # 3. !!! РУССКИЙ ЛЕЙБЛ ИЗ GITLAB (Модуль::Балансы) !!!
        LABEL_TO_MODULE[f"Модуль::{m_name}"] = m_code
        # 4. На всякий случай просто название (Балансы) - для обратной совместимости
        LABEL_TO_MODULE[m_name] = m_code

# [ENGINEERING CONTEXT]
# Legacy маппинг для поддержки старых интеграций, где модули назывались иначе.
LEGACY_MAPPING = {
    "valves": "btr-valve-stems"
}
LABEL_TO_MODULE.update(LEGACY_MAPPING)


# Маппинг бизнес-статусов задач
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
    """
    Модель с детальной информацией о задаче (Issue).
    
    Содержит как сырые данные из трекера, так и автоматически вычисляемые
    поля (computed_fields) для удобного использования во фронтенде 
    без дополнительного парсинга.
    """
    iid: int = Field(..., description="Внутренний идентификатор задачи (Issue IID).", examples=[1054])
    project_id: int = Field(..., description="Уникальный ID проекта в трекере.", examples=[42])
    project_name: str = Field(..., description="Название проекта.", examples=["Турбина К-300"])
    title: str = Field(..., description="Заголовок задачи.", examples=["Расчет конденсатора (Вариант 2)"])
    description: str | None = Field(None, description="Полное текстовое описание задачи (Markdown).")
    state: str = Field(..., description="Системное состояние задачи (opened/closed).", examples=["opened"])
    labels: list[str] = Field(default=[], description="Список всех навешанных лейблов.", examples=[["Бюро::БТР", "Модуль::Конденсаторы"]])
    assignee: str | None = Field(None, description="Username назначенного исполнителя.", examples=["ivanov_i"])
    created_at: datetime = Field(..., description="Временная метка создания задачи.")
    due_date: date | None = Field(None, description="Крайний срок выполнения задачи.")
    web_url: str = Field(..., description="Прямая ссылка на задачу в UI трекера.", examples=["https://gitlab.local/project/issues/1054"])

    @computed_field
    def formatted_date(self) -> str:
        """
        Возвращает дату создания в удобочитаемом формате ДД.ММ.ГГ.
        
        Returns:
            str: Отформатированная дата (например, '24.10.23').
        """
        return self.created_at.strftime("%d.%m.%y")

    @computed_field
    def bureau(self) -> dict[str, str] | None:
        """
        Определяет инженерное бюро, к которому относится задача.

        [ENGINEERING CONTEXT]
        Алгоритм поиска двухуровневый: сначала мы ищем явные лейблы (bureau::... или Бюро::...).
        Если их нет, мы пытаемся "угадать" бюро по префиксу расчетного модуля 
        (например, если модуль начинается с 'btr-', значит это БТР). 
        Это защищает нас от случаев, когда пользователь забыл поставить лейбл бюро.

        Returns:
            dict | None: Словарь с кодом, названием и цветом бюро, либо None.
        """
        # 1. Явный лейбл бюро (Английский и Русский)
        for label in self.labels:
            if label.startswith("bureau::"):
                code = label.replace("bureau::", "")
                if code in BUREAU_CONFIG:
                    return {"code": code, "name": BUREAU_CONFIG[code]["name"], "color": BUREAU_CONFIG[code]["color"]}

            if label.startswith("Бюро::"):
                name = label.replace("Бюро::", "")
                for code, data in BUREAU_CONFIG.items():
                    if data["name"] == name:
                        return {"code": code, "name": data["name"], "color": data["color"]}

        # 2. Неявный (через модуль) - если лейбла бюро нет, но есть модуль
        module_code = self.calc_type
        if module_code:
            if module_code.startswith("btr-"):
                return {"code": "btr", "name": "БТР", "color": "#1976D2"}
            if module_code.startswith("bpr-"):
                return {"code": "bpr", "name": "БПР", "color": "#26A69A"}
            if module_code.startswith("bvp-"):
                return {"code": "bvp", "name": "БВП", "color": "#7E57C2"}

        return None

    @computed_field
    def calc_type(self) -> str | None:
        """
        Извлекает системный код расчетного модуля из лейблов задачи.

        Returns:
            str | None: Системный код (например, 'btr-valve-stems') или None.
        """
        for label in self.labels:
            # ИСПОЛЬЗУЕМ LABEL_TO_MODULE ВМЕСТО TYPE_MAPPING
            if label in LABEL_TO_MODULE:
                return LABEL_TO_MODULE[label]
        return None

    @computed_field
    def calc_type_human(self) -> str:
        """
        Возвращает человекочитаемое (русское) название модуля для UI.

        Returns:
            str: Название модуля (например, 'Конденсаторы') или 'Общая задача'.
        """
        code = self.calc_type
        if not code:
            return "Общая задача"

        # Ищем в конфиге
        for _b_code, b_data in BUREAU_CONFIG.items():
            if code in b_data["modules"]:
                return b_data["modules"][code]
        return code

    @computed_field
    def business_status(self) -> dict:
        """
        Извлекает текущий бизнес-статус задачи на основе лейблов 'Статус::...'.

        Если задача закрыта в самом трекере (state == 'closed'), статус переопределяется
        как закрытый, независимо от навешанных лейблов.

        Returns:
            dict: Объект статуса (текст, цвет для UI, системный ключ).
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
    """Модель для создания новой задачи во внешнем трекере (GitLab)."""
    title: str = Field(..., description="Заголовок новой задачи.", examples=["Новый расчет баланса"])
    description: str = Field(default="", description="Описание задачи.", examples=["Вводные данные: ..."])
    labels: list[str] = Field(default=[], description="Список стартовых лейблов.")
    project_id: int = Field(..., description="ОБЯЗАТЕЛЬНОЕ ПОЛЕ: ID проекта, в котором создается задача.", examples=[42])


class BranchCreate(BaseModel):
    """Модель для запроса создания новой Git-ветки, привязанной к задаче."""
    issue_iid: int = Field(..., description="IID задачи (Issue), к которой привязывается ветка.", examples=[1054])
    project_id: int = Field(..., description="ID проекта в Git.", examples=[42])


class BranchInfo(BaseModel):
    """Модель ответа с информацией о созданной Git-ветке."""
    branch_name: str = Field(..., description="Сгенерированное имя ветки.", examples=["1054-btr-condenser-calc"])
    issue_iid: int = Field(..., description="IID связанной задачи.")
    created: bool = Field(..., description="Флаг успешности создания ветки (True если создана).")

class BranchCreateRequest(BaseModel):
    """Запрос на создание ветки (упрощенный вариант)."""
    project_id: int = Field(..., description="Уникальный ID проекта.", examples=[42])
    