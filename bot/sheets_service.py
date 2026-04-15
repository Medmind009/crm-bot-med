"""
Google Sheets сервис для CRM-бота.
Запись в Лиды, Касания, Задачи с правильным маппингом колонок.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List
import gspread
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

# Конфиг
SPREADSHEET_ID = "1b7V6KHEPxcpthohDORDgK4X33OwcVxjcEdz_PSUOHbY"
CREDENTIALS_FILE = "google-credentials.json"


class SheetsService:
    """Сервис для работы с Google Таблицами."""
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
    
    def connect(self):
        """Подключиться к Google Sheets."""
        if self.client:
            return
        
        # Загружаем credentials
        with open(CREDENTIALS_FILE) as f:
            creds_dict = json.load(f)
        
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        creds = creds.with_scopes([
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets'
        ])
        
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(SPREADSHEET_ID)
        logger.info(f"Подключено к: {self.spreadsheet.title}")
    
    # ===========================================
    # ЛИДЫ - Маппинг колонок (точное соответствие)
    # ===========================================
    # A=ID, B=Дата, C=Клиника, D=Район, E=Адрес, F=Контакт, G=Должность
    # H=ЛПР, I=Телефон, J=Email, K=Telegram, L=Канал, M=Что передали
    # N=Реакция, O=Следующий шаг, P=Дата след.касания, Q=Статус
    # R=Ответственный, S=Комментарий
    
    def add_lead(self, data: dict, responsible: str) -> str:
        """Добавить лида в таблицу. Возвращает ID лида."""
        self.connect()
        ws = self.spreadsheet.worksheet("Лиды")
        
        # Автозаполнение
        now = datetime.now()
        lead_id = f"LD-{now.strftime('%Y%m%d')}-{ws.row_count}"
        
        # Если дата след.касания не указана - +5 дней
        next_date = data.get("next_step_date", "")
        if not next_date:
            next_date = (now + timedelta(days=5)).strftime("%Y-%m-%d")
        
        row = [
            lead_id,  # A: ID
            now.strftime("%d.%m.%Y"),  # B: Дата создания
            data.get("clinic_name", ""),  # C: Клиника
            data.get("district", ""),  # D: Район
            data.get("address", ""),  # E: Адрес
            data.get("contact_name", ""),  # F: Контакт
            data.get("position", ""),  # G: Должность
            data.get("decision_maker", ""),  # H: ЛПР
            data.get("phone", ""),  # I: Телефон
            data.get("email", ""),  # J: Email
            data.get("telegram", ""),  # K: Telegram
            data.get("channel", "Telegram"),  # L: Канал
            data.get("sent_materials", ""),  # M: Что передали
            data.get("reaction", ""),  # N: Реакция
            data.get("next_step", ""),  # O: Следующий шаг
            next_date,  # P: Дата след. касания
            data.get("status", "Новый"),  # Q: Статус
            responsible,  # R: Ответственный
            data.get("comment", ""),  # S: Комментарий
        ]
        
        ws.append_row(row)
        logger.info(f"Добавлен лид: {lead_id} - {data.get('clinic_name', '')}")
        return lead_id
    
    def update_lead(self, lead_id: str, data: dict):
        """Обновить данные лида."""
        self.connect()
        ws = self.spreadsheet.worksheet("Лиды")
        
        # Ищем по ID
        try:
            cell = ws.find(lead_id)
            # Обновляем только непустые поля
            if data.get("status"):
                ws.update_cell(cell.row, 17, data["status"])  # Q: Статус
            if data.get("next_step"):
                ws.update_cell(cell.row, 15, data["next_step"])  # O: Следующий шаг
            if data.get("next_step_date"):
                ws.update_cell(cell.row, 16, data["next_step_date"])  # P: Дата
            if data.get("reaction"):
                ws.update_cell(cell.row, 14, data["reaction"])  # N: Реакция
            logger.info(f"Обновлён лид: {lead_id}")
        except gspread.exceptions.CellNotFound:
            logger.error(f"Лид не найден: {lead_id}")
    
    def get_all_leads(self) -> List[dict]:
        """Получить все лиды."""
        self.connect()
        ws = self.spreadsheet.worksheet("Лиды")
        records = ws.get_all_records()
        return records
    
    def find_lead_by_name(self, name: str) -> Optional[dict]:
        """Найти лид по названию клиники."""
        leads = self.get_all_leads()
        name_lower = name.lower()
        for lead in leads:
            if name_lower in lead.get("Название клиники", "").lower():
                return lead
        return None
    
    def find_lead_by_id(self, lead_id: str) -> Optional[dict]:
        """Найти лид по ID."""
        leads = self.get_all_leads()
        for lead in leads:
            if lead.get("ID") == lead_id:
                return lead
        return None
    
    # ===========================================
    # КАСАНИЯ - Маппинг колонок
    # ===========================================
    # A=ID касания, B=ID лида, C=Дата, D=Кто, E=Формат, F=Что произошло
    # G=Что передали, H=Вопросы, I=Ответы, J=Итог, K=Следующий шаг, L=Комментарий
    
    def add_contact(self, lead_id: str, data: dict, who: str) -> str:
        """Добавить касание."""
        self.connect()
        ws = self.spreadsheet.worksheet("Касания")
        
        now = datetime.now()
        contact_id = f"CT-{now.strftime('%Y%m%d%H%M')}"
        
        row = [
            contact_id,  # A: ID
            lead_id,  # B: ID лида
            now.strftime("%d.%m.%Y"),  # C: Дата
            who,  # D: Кто общался
            data.get("format", "Telegram"),  # E: Формат
            data.get("what_happened", ""),  # F: Что произошло
            data.get("sent_materials", ""),  # G: Что передали
            data.get("client_questions", ""),  # H: Вопросы
            data.get("answers_given", ""),  # I: Ответы
            data.get("result", ""),  # J: Итог
            data.get("next_step", ""),  # K: Следующий шаг
            data.get("comment", ""),  # L: Комментарий
        ]
        
        ws.append_row(row)
        logger.info(f"Добавлено касание: {contact_id} для лида {lead_id}")
        return contact_id
    
    def get_contacts_for_lead(self, lead_id: str) -> List[dict]:
        """Получить все касания для лида."""
        self.connect()
        ws = self.spreadsheet.worksheet("Касания")
        records = ws.get_all_records()
        return [r for r in records if r.get("ID лида") == lead_id]
    
    # ===========================================
    # ЗАДАЧИ - Маппинг колонок
    # ===========================================
    # A=ID, B=ID лида, C=Клиника, D=Задача, E=Дата создания
    # F=Дедлайн, G=Ответственный, H=Статус, I=Приоритет, J=Комментарий
    
    def add_task(self, lead_id: str, clinic: str, data: dict, responsible: str) -> str:
        """Добавить задачу."""
        self.connect()
        ws = self.spreadsheet.worksheet("Задачи")
        
        now = datetime.now()
        task_id = f"TSK-{now.strftime('%Y%m%d%H%M')}"
        
        deadline = data.get("deadline", "")
        if not deadline:
            deadline = (now + timedelta(days=3)).strftime("%Y-%m-%d")
        
        row = [
            task_id,  # A: ID
            lead_id,  # B: ID лида
            clinic,  # C: Клиника
            data.get("title", ""),  # D: Задача
            now.strftime("%d.%m.%Y %H:%M"),  # E: Дата создания
            deadline,  # F: Дедлайн
            responsible,  # G: Ответственный
            data.get("status", "Новая"),  # H: Статус
            data.get("priority", "Средний"),  # I: Приоритет
            data.get("comment", ""),  # J: Комментарий
        ]
        
        ws.append_row(row)
        logger.info(f"Добавлена задача: {task_id}")
        return task_id
    
    def get_tasks_for_lead(self, lead_id: str) -> List[dict]:
        """Получить все задачи для лида."""
        self.connect()
        ws = self.spreadsheet.worksheet("Задачи")
        records = ws.get_all_records()
        return [r for r in records if r.get("ID лида") == lead_id]
    
    def get_open_tasks(self) -> List[dict]:
        """Получить открытые задачи."""
        self.connect()
        ws = self.spreadsheet.worksheet("Задачи")
        records = ws.get_all_records()
        return [r for r in records if r.get("Статус задачи") in ["Новая", "В работе"]]


# Глобальный сервис
sheets_service = SheetsService()