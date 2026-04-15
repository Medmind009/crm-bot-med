"""
Конфигурация CRM-бота.
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """Настройки приложения."""
    
    # Telegram (получить у @BotFather)
    telegram_token: str = os.environ.get("TELEGRAM_TOKEN", "")
    
    # Google Sheets (из URL таблицы)
    google_spreadsheet_id: str = os.environ.get(
        "GOOGLE_SPREADSHEET_ID", 
        "1b7V6KHEPxcpthohDORDgK4X33OwcVxjcEdz_PSUOHbY"
    )
    google_credentials_path: str = os.environ.get(
        "GOOGLE_CREDENTIALS_PATH", 
        "credentials.json"
    )
    
    # AI (OpenRouter)
    openrouter_api_key: str = os.environ.get("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.environ.get(
        "OPENROUTER_MODEL",
        "google/gemini-2.0-flash-001"
    )
    
    # Альтернативный AI (directly Google)
    google_ai_api_key: str = os.environ.get("GOOGLE_AI_API_KEY", "")
    
    # ID администратора для уведомлений
    admin_chat_id: Optional[str] = os.environ.get("ADMIN_CHAT_ID")
    
    # Режим отладки
    debug: bool = os.environ.get("DEBUG", "false").lower() == "true"
    
    # Имена листов в Google Таблице
    sheet_leads: str = "Лиды"
    sheet_contacts: str = "Касания"
    sheet_tasks: str = "Задачи"


# Глобальный конфиг
config = Config()