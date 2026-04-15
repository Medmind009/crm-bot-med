"""
Типы и константы для CRM-бота.
Единый источник истины для всех сущностей.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


# ===========================================
# КОНСТАНТЫ - Статусы лида
# ===========================================
class LeadStatus(str, Enum):
    """Статусы лида."""
    NEW = "Новый"
    INTEREST = "Интерес"
    NEGOTIATIONS = "Переговоры"
    WAITING = "Ожидание ответа"
    OFFERED = "Предложено"
    INACTIVE = "Неактуально"
    REJECTED = "Отказ"
    DEAL = "Сделка"


LEAD_STATUSES = [s.value for s in LeadStatus]
LEAD_STATUS_MAP = {
    "новый": LeadStatus.NEW,
    "интерес": LeadStatus.INTEREST,
    "переговоры": LeadStatus.NEGOTIATIONS,
    "ожидание": LeadStatus.WAITING,
    "ожидание ответа": LeadStatus.WAITING,
    "предложено": LeadStatus.OFFERED,
    "неактуально": LeadStatus.INACTIVE,
    "отказ": LeadStatus.REJECTED,
    "сделка": LeadStatus.DEAL,
}


# ===========================================
# КОНСТАНТЫ - Статусы задач
# ===========================================
class TaskStatus(str, Enum):
    """Статусы задач."""
    NEW = "Новая"
    IN_PROGRESS = "В работе"
    DONE = "Выполнена"
    CANCELLED = "Отменена"


TASK_STATUSES = [s.value for s in TaskStatus]


# ===========================================
# КОНСТАНТЫ - Приоритеты
# ===========================================
class TaskPriority(str, Enum):
    """Приоритеты задач."""
    LOW = "Низкий"
    MEDIUM = "Средний"
    HIGH = "Высокий"


TASK_PRIORITIES = [s.value for s in TaskPriority]
TASK_PRIORITY_MAP = {
    "низкий": TaskPriority.LOW,
    "средний": TaskPriority.MEDIUM,
    "высокий": TaskPriority.HIGH,
}


# ===========================================
# КОНСТАНТЫ - Каналы
# ===========================================
class ContactChannel(str, Enum):
    """Каналы первого контакта."""
    TELEGRAM = "Telegram"
    WHATSAPP = "WhatsApp"
    MAX = "Max"
    MEETING = "Личная встреча"
    PHONE = "Телефон"


CONTACT_CHANNELS = [s.value for s in ContactChannel]


# ===========================================
# КОНСТАНТЫ - Форматы контакта
# ===========================================
class InteractionFormat(str, Enum):
    """Форматы контакта (для касаний)."""
    TELEGRAM = "Telegram"
    WHATSAPP = "WhatsApp"
    PHONE = "Телефон"
    MEETING = "Личная встреча"
    VIDEO = "Видеозвонок"
    EMAIL = "Email"


INTERACTION_FORMATS = [s.value for s in InteractionFormat]


# ===========================================
# КОНСТАНТЫ - Меню
# ===========================================
class MenuAction(str, Enum):
    """Действия меню."""
    NEW_LEAD = "new_lead"
    NEW_CONTACT = "new_contact"
    NEW_TASK = "new_task"
    LEAD_CARD = "lead_card"
    SEARCH = "search"
    CANCEL = "cancel"
    BACK = "back"
    SKIP = "skip"
    SAVE = "save"


MENU_KEYBOARD = [
    ["➕ Новый лид", "📞 Новое касание"],
    ["✅ Новая задача", "🗂 Карточка лида"],
    ["🔎 Поиск лида"],
]


# ===========================================
# ТИПЫ ДАННЫХ
# ===========================================
@dataclass
class Lead:
    """Лид (клиника)."""
    id: Optional[str] = None
    created_date: str = ""
    clinic_name: str = ""
    district: str = ""
    address: str = ""
    contact_name: str = ""
    position: str = ""
    decision_maker: str = ""
    phone: str = ""
    email: str = ""
    telegram: str = ""
    channel: str = ""
    sent_materials: str = ""
    reaction: str = ""
    next_step: str = ""
    next_step_date: str = ""
    status: str = "Новый"
    responsible: str = ""
    comment: str = ""


@dataclass
class Contact:
    """Касание (взаимодействие с лидом)."""
    id: Optional[str] = None
    lead_id: str = ""
    date: str = ""
    who_talked: str = ""
    format: str = ""
    what_happened: str = ""
    sent_materials: str = ""
    client_questions: str = ""
    answers_given: str = ""
    result: str = ""
    next_step: str = ""
    comment: str = ""


@dataclass
class Task:
    """Задача."""
    id: Optional[str] = None
    lead_id: str = ""
    clinic: str = ""
    title: str = ""
    created_date: str = ""
    deadline: str = ""
    responsible: str = ""
    status: str = "Новая"
    priority: str = "Средний"
    comment: str = ""


@dataclass
class LeadCard:
    """Карточка лида для отображения."""
    lead: Lead
    contacts: List[Contact] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    total_contacts: int = 0
    open_tasks: int = 0


# ===========================================
# AI РЕЗУЛЬТАТЫ
# ===========================================
@dataclass
class AILeadResult:
    """Результат AI определения статуса лида."""
    status: str
    next_step: str = ""
    next_step_date: str = ""
    confidence: float = 0.0


@dataclass
class AITaskResult:
    """Результат AI генерации задачи."""
    title: str
    priority: str = "Средний"
    status: str = "Новая"


@dataclass
class AIContactResult:
    """Результат AI для касания."""
    next_step: str = ""
    result: str = ""