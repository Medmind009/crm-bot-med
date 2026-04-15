"""
Google Sheets сервис для CRM.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import gspread

from config.settings import config

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """Сервис для работы с Google Таблицами."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.spreadsheet = None
    
    async def connect(self) -> None:
        """Подключиться к Google Sheets."""
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Загружаем_credentials
            import os
            creds_path = config.google_credentials_path
            
            # Пробуем разные способы загрузки
            try:
                # Способ 1: gspread + service account
                from google.oauth2 import service_account
                from google.auth import default
                
                credentials, _ = default()
                self.client = gspread.authorize(credentials)
            except Exception:
                # Способ 2: через JSON
                if os.path.exists(creds_path):
                    self.client = gspread.service_account(creds_path)
                else:
                    # Пробуем из переменной окружения
                    import json
                    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
                    if creds_json:
                        import io
                        credentials = json.loads(creds_json)
                        self.client = gspread.service_account_from_dict(credentials)
                    else:
                        raise ValueError("Google credentials not found")
            
            # Открываем таблицу
            self.spreadsheet = self.client.open_by_key(config.google_spreadsheet_id)
            logger.info(f"Connected to Google Sheets: {self.spreadsheet.title}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            raise
    
    async def add_lead(self, data: Dict[str, Any]) -> None:
        """Добавить новый лид."""
        worksheet = self.spreadsheet.worksheet(config.sheet_leads)
        
        row = [
            "",  # A: Дата создания
            data.get("клиника", ""),  # B: Название клиники
            data.get("contact_name", ""),  # C: Контакт
            data.get("должность", ""),  # D: Должность
            data.get("decision_maker", ""),  # E: ЛПР
            data.get("телефон", ""),  # F: Телефон
            "",  # G: Email
            data.get("interaction_format", "Telegram"),  # H: Канал
            data.get("sent_materials", ""),  # I: Что передали
            data.get("реакция", ""),  # J: Реакция
            data.get("next_step", ""),  # K: Следующий шаг
            data.get("next_step_date", ""),  # L: Дата след. шага
            data.get("lead_status", "Новый"),  # M: Статус
            data.get("ответственный", ""),  # N: Ответственный
            data.get("comment", ""),  # O: Комментарий
        ]
        
        worksheet.append_row(row)
        logger.info(f"Added lead: {data.get('клиника')}")
    
    async def add_contact(self, data: Dict[str, Any]) -> None:
        """Добавить касание."""
        worksheet = self.spreadsheet.worksheet(config.sheet_contacts)
        
        row = [
            "",  # A: Дата
            data.get("who_talked", ""),  # B: Кто общался
            data.get("interaction_format", "Telegram"),  # C: Формат
            data.get("реакция", ""),  # D: Что произошло
            data.get("sent_materials", ""),  # E: Что передали
            data.get("client_questions", ""),  # F: Вопросы клиента
            data.get("ответы_даны", ""),  # G: Что ответили
            data.get("interaction_result", ""),  # H: Итог
            data.get("next_step", ""),  # I: Следующий шаг
            data.get("comment", ""),  # J: Комментарий
            data.get("клиника", ""),  # K: Клиника
        ]
        
        worksheet.append_row(row)
        logger.info(f"Added contact: {data.get('клиника')}")
    
    async def add_task(self, data: Dict[str, Any]) -> None:
        """Добавить задачу."""
        if not data.get("task_needed", False):
            return
        
        worksheet = self.spreadsheet.worksheet(config.sheet_tasks)
        
        row = [
            data.get("клиника", ""),  # A: Клиника
            data.get("task_title", ""),  # B: Задача
            datetime.now().strftime("%Y-%m-%d %H:%M"),  # C: Дата создания
            data.get("next_step_date", ""),  # D: Дедлайн
            data.get("ответственный", ""),  # E: Ответственный
            "Новая",  # F: Статус
            data.get("task_priority", "Средний"),  # G: Приоритет
        ]
        
        worksheet.append_row(row)
        logger.info(f"Added task: {data.get('task_title')}")
    
    async def update_lead_status(
        self, 
        clinic_name: str, 
        new_status: str
    ) -> None:
        """Обновить статус лида."""
        worksheet = self.spreadsheet.worksheet(config.sheet_leads)
        
        # Ищем клинику
        cells = worksheet.findall(clinic_name)
        
        if cells:
            cell = cells[0]
            # Статус в колонке M (13)
            worksheet.update_cell(cell.row, 13, new_status)
            logger.info(f"Updated status for {clinic_name}: {new_status}")


# Глобальный сервис
sheets_service = GoogleSheetsService()