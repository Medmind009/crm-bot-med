#!/usr/bin/env python3
"""
CRM Бот для медицинских продаж - Главный модуль.
"""
import asyncio
import logging
import os
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional

import aiohttp
from aiohttp import web
from aiohttp.web import Request, Response

from config.settings import config
from services.ai_service import ai_service
from services.sheets_service import sheets_service
from services.telegram_service import telegram_service

# Логирование
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CRMBot:
    """CRM Бот для обработки отчетов о продажах."""
    
    def __init__(self):
        self.token = config.telegram_token
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.session: Optional[aiohttp.ClientSession] = None
        self.offset = 0
    
    async def start(self):
        """Запустить бота."""
        logger.info("Starting CRM Bot...")
        
        # Проверяем токен
        if not self.token:
            logger.warning("TELEGRAM_TOKEN not set!")
            return
        
        # Подключаемся к Google Sheets
        try:
            await sheets_service.connect()
        except Exception as e:
            logger.warning(f"Google Sheets connection failed: {e}")
        
        # Создаем сессию
        self.session = aiohttp.ClientSession()
        
        # Запускаем polling
        asyncio.create_task(self._polling_loop())
        
        logger.info("CRM Bot started!")
    
    async def stop(self):
        """Остановить бота."""
        if self.session:
            await self.session.close()
        await telegram_service.close()
    
    async def _polling_loop(self):
        """Основной цикл опроса Telegram."""
        while True:
            try:
                await self._poll_updates()
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)
    
    async def _poll_updates(self):
        """Получить обновления."""
        url = f"{self.api_url}/getUpdates"
        
        params = {"timeout": 30, "offset": self.offset}
        
        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                logger.error(f"API error: {response.status}")
                return
            
            data = await response.json()
            
            if not data.get("ok"):
                logger.error(f"API not ok: {data}")
                return
            
            for update in data.get("result", []):
                await self._handle_update(update)
                self.offset = update["update_id"] + 1
    
    async def _handle_update(self, update: Dict[str, Any]):
        """Обработать обновление."""
        message = update.get("message")
        if not message:
            return
        
        chat = message.get("chat", {})
        from_user = message.get("from", {})
        
        chat_id = str(chat.get("id"))
        text = message.get("text", "")
        username = from_user.get("username", "unknown")
        first_name = from_user.get("first_name", "")
        
        logger.info(f"Message from {username}: {text[:50]}...")
        
        # Обрабатываем команды
        if text == "/start":
            await self._send_start(chat_id, first_name)
        elif text == "/help":
            await self._send_help(chat_id)
        elif text == "/test":
            await self._send_test(chat_id)
        elif text.startswith("/"):
            await self._send_unknown(chat_id)
        else:
            # Обрабатываем отчет
            await self._handle_report(chat_id, username, first_name, text)
    
    async def _handle_report(
        self,
        chat_id: str,
        username: str,
        name: str,
        text: str
    ):
        """Обработать отчет о продаже."""
        try:
            # Парсим через AI
            logger.info(f"Parsing report with AI...")
            parsed = await ai_service.parse_report(chat_id, username, name, text)
            
            logger.info(f"Parsed data: {parsed}")
            
            # Сохраняем в Google Sheets
            if sheets_service.spreadsheet:
                await sheets_service.add_lead(parsed)
                await sheets_service.add_contact(parsed)
                await sheets_service.add_task(parsed)
            
            # Отправляем подтверждение
            await telegram_service.send_report_confirmation(chat_id, parsed)
            
        except Exception as e:
            logger.error(f"Error handling report: {e}")
            await telegram_service.send_error(chat_id, str(e))
    
    async def _send_start(self, chat_id: str, name: str):
        """Отправить приветствие."""
        await telegram_service.send_start(chat_id, name)
    
    async def _send_help(self, chat_id: str):
        """Отправить справку."""
        await telegram_service.send_help(chat_id)
    
    async def _send_test(self, chat_id: str):
        """Тестовая проверка."""
        await telegram_service.send_message(chat_id, "🔧 <b>Тест</b>\n\nБот работает!")
    
    async def _send_unknown(self, chat_id: str):
        """Неизвестная команда."""
        await telegram_service.send_message(
            chat_id, 
            "❓ Неизвестная команда. Нажмите /help для справки."
        )


# HTTP хендлеры для Webhook
async def handle_webhook(request: Request) -> Response:
    """Обработать webhook от Telegram."""
    try:
        update = await request.json()
        
        message = update.get("message", {})
        if not message:
            return web.Response(text="OK")
        
        bot = request.app["bot"]
        chat = message.get("chat", {})
        from_user = message.get("from", {})
        
        chat_id = str(chat.get("id"))
        text = message.get("text", "")
        username = from_user.get("username", "unknown")
        first_name = from_user.get("first_name", "")
        
        logger.info(f"Webhook: {username}: {text[:30]}...")
        
        # Обрабатываем команды
        if text == "/start":
            await telegram_service.send_start(chat_id, first_name)
        elif text == "/help":
            await telegram_service.send_help(chat_id)
        elif text == "/stat":
            await telegram_service.send_message(chat_id, "📊 Статистика скоро!")
        elif text == "/test":
            await telegram_service.send_message(chat_id, "✅ Бот работает!")
        elif text.startswith("/"):
            await telegram_service.send_message(
                chat_id, 
                "❓ Неизвестная команда. /help — помощь."
            )
        else:
            # Обрабатываем отчет
            await bot._handle_report(chat_id, username, first_name, text)
        
        return web.Response(text="OK")
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(text="Error", status=500)


async def handle_health(request: Request) -> Response:
    """Проверка здоровья."""
    return web.Response(text="OK")


async def on_startup(app):
    """Запуск приложения."""
    bot = CRMBot()
    app["bot"] = bot
    await bot.start()


async def on_shutdown(app):
    """Остановка приложения."""
    bot = app.get("bot")
    if bot:
        await bot.stop()


def create_app() -> web.Application:
    """Создать приложение."""
    app = web.Application()
    
    app.router.add_post("/webhook", handle_webhook)
    app.router.add_get("/health", handle_health)
    
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)