"""
Telegram бот сервис.
"""
import logging
from typing import Dict, Any, Optional
import httpx
from config.settings import config

logger = logging.getLogger(__name__)


class TelegramService:
    """Сервис для работы с Telegram Bot API."""
    
    def __init__(self):
        self.token = config.telegram_token
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Закрыть соединение."""
        await self.client.aclose()
    
    async def send_message(
        self,
        chat_id: str,
        text: str,
        reply_markup: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Отправить сообщение."""
        url = f"{self.api_url}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    async def send_report_confirmation(
        self,
        chat_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Отправить подтверждение о сохранении отчета."""
        
        # Форматируем дату
        next_step_date = data.get("next_step_date", "")
        if next_step_date:
            # Российский формат даты
            try:
                from datetime import datetime
                dt = datetime.strptime(next_step_date, "%Y-%m-%d")
                next_step_date = dt.strftime("%d.%m.%Y")
            except:
                pass
        
        # Формируем сообщение
        status_emoji = {
            "Новый": "🆕",
            "Интерес": "🤔",
            "Переговоры": "💬",
            "Ожидание ответа": "⏳",
            "Предложено": "📝",
            "Неактуально": "❌",
            "Отказ": "🚫",
            "Сделка": "✅"
        }
        
        status = data.get("lead_status", "Новый")
        emoji = status_emoji.get(status, "")
        
        text = f"""✅ <b>Отчет успешно сохранен!</b>

🏥 Клиника: {data.get('клиника', '-')}
📊 Статус лида: {emoji} {status}
👤 Ответственный: {data.get('ответственный', '-')}

📌 Следующий шаг: {data.get('next_step', '-') or '–'}
📅 Дедлайн: {next_step_date or '–'}

Данные записаны в CRM."""
        
        return await self.send_message(chat_id, text)
    
    async def send_error(
        self,
        chat_id: str,
        error_message: str
    ) -> Dict[str, Any]:
        """Отправить сообщение об ошибке."""
        text = f"""❌ <b>Ошибка!</b>

{error_message}

Попробуйте еще раз или свяжитесь с администратором."""
        
        return await self.send_message(chat_id, text)
    
    async def send_help(self, chat_id: str) -> Dict[str, Any]:
        """Отправить справку."""
        text = """📖 <b>Справка по боту</b>

Бот для CRM медицинских продаж. Отправьте отчет о встрече с клиникой в свободной форме.

<b>Пример отчета:</b>
Клиника: Стоматология Дент-Люкс. Общался сегодня с главным врачом Марией Ивановной. ЛПР: да, она принимает решения. Телефон: +7 999 123-45-67. Реакция отличная, проявлен интерес. Передал каталог и прайс. Договорились о презентации в зуме. Дата следующего касания: 15 апреля.

<b>Команды:</b>
/start - Начать работу
/help - Эта справка
/stat - Статистика
/test - Тестовая проверка"""
        
        return await self.send_message(chat_id, text)
    
    async def send_start(self, chat_id: str, name: str = "") -> Dict[str, Any]:
        """Отправить приветствие."""
        text = f"""👋 <b>Привет{', ' + name if name else ''}!</b>

Добро пожаловать в CRM бота для медицинских продаж!

Отправьте отчет о взаимодействии с клиникой — бот автоматически:
• Распознает данные из текста
• Запишет лида в CRM
• Создаст задачу при необходимости

Нажмите /help для справки."""
        
        return await self.send_message(chat_id, text)
    
    async def get_me(self) -> Dict[str, Any]:
        """Получить информацию о боте."""
        url = f"{self.api_url}/getMe"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()


# Глобальный сервис
telegram_service = TelegramService()