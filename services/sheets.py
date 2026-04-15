"""
Google Sheets интеграция.
Требует service account credentials.
"""
import os
import gspread
from google.oauth2 import service_account
from datetime import datetime


# Настройки
SPREADSHEET_ID = "1b7V6KHEPxcpthohDORDgK4X33OwcVxjcEdz_PSUOHbY"
CREDENTIALS_FILE = "google-credentials.json"  # Нужно скачать из Google Cloud Console


def get_client():
    """Подключиться к Google Sheets."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets"
    ]
    
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(f"❌ Файл {CREDENTIALS_FILE} не найден!")
    
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=scope
    )
    
    return gspread.authorize(credentials)


def add_lead(data: dict, client=None):
    """Добавить лида в таблицу."""
    if client is None:
        client = get_client()
    
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet("Лиды")
    
    row = [
        datetime.now().strftime("%d.%m.%Y"),  # Дата
        data.get("клиника", ""),  # Клиника
        data.get("contact_name", ""),  # Контакт
        data.get("должность", ""),  # Должность
        data.get("decision_maker", ""),  # ЛПР
        data.get("телефон", ""),  # Телефон
        data.get("реакция", ""),  # Реакция
        data.get("next_step", ""),  # Следующий шаг
        data.get("next_step_date", ""),  # Дата
        data.get("lead_status", "Новый"),  # Статус
        data.get("ответственный", ""),  # Ответственный
        data.get("comment", ""),  # Комментарий
    ]
    
    sheet.append_row(row)
    return True


def get_all_leads(client=None):
    """Получить все лиды."""
    if client is None:
        client = get_client()
    
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet("Лиды")
    return sheet.get_all_records()


# ================================================
# ИНСТРУКЦИЯ ПО ПОДКЛЮЧЕНИЮ GOOGLE SHEETS:
# ================================================
"""
1. Открой https://console.cloud.google.com/
2. Создай проект (или выбери существующий)
3. Перейди в APIs & Services → Enable → Google Sheets API + Google Drive API
4. Перейди в Credentials → Create Credentials → Service Account
5. Заполни имя (напр. "crm-bot"), нажми Create
6. Создай Key (JSON) → Download
7. Переименуй файл в google-credentials.json и положи в папку с ботом
8. Открой свою Google Таблицу
9. Нажми Поделиться → добавь email из service account (напр. crm-bot@project.iam.gserviceaccount.com)
10. Готово!
"""