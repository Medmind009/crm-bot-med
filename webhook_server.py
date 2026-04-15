#!/usr/bin/env python3
"""
Webhook сервер для CRM-бота.
"""
import asyncio
import logging
import os
import json
from aiohttp import web

# Конфигурация (из env)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") or "8712375566:AAGqUCjIf6MPy68Ayvrlx3LYZSdZxWLjgpE"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or "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"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


async def handle_webhook(request: web.Request) -> web.Response:
    """Обработать webhook от Telegram."""
    try:
        update = await request.json()
        logger.info(f"Received: {update.get('message', {}).get('text', 'no text')[:50]}")
        
        message = update.get("message", {})
        if not message:
            return web.Response(text="OK")
        
        chat = message.get("chat", {})
        from_user = message.get("from", {})
        
        chat_id = str(chat.get("id"))
        text = message.get("text", "")
        username = from_user.get("username", "unknown")
        first_name = from_user.get("first_name", "")
        
        logger.info(f"Message from {username}: {text[:30]}")
        
        # Обработка команд и отчетов
        if text == "/start":
            response = f"👋 Привет, {first_name}! Я CRM-бот для медицинских продаж. Отправь отчет о встрече с клиникой."
        elif text == "/help":
            response = """📖 <b>Справка</b>

Отправь отчет в свободной форме:
- Название клиники
- Контактное лицо и должность
- Телефон
- Реакция клиента
- Что передали
- Следующий шаг и дата"""
        elif text.startswith("/"):
            response = "❓ Неизвестная команда. /help — помощь."
        else:
            # Обрабатываем отчет через AI
            response = await process_report(update)
        
        # Отправляем ответ
        if response:
            await send_message(chat_id, response)
        
        return web.Response(text="OK")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return web.Response(text="Error", status=500)


async def process_report(update: dict) -> str:
    """Обработать отчет через AI."""
    message = update.get("message", {})
    chat = message.get("chat", {})
    from_user = message.get("from", {})
    
    chat_id = str(chat.get("id"))
    text = message.get("text", "")
    username = from_user.get("username", "unknown")
    first_name = from_user.get("first_name", "")
    
    # AI промпт
    system_prompt = """Ты — AI CRM-ассистент для медицинских продаж. 
Извлеки данные из отчета, верни JSON.
Статус: Новый, Интерес, Переговоры, Предложено, Сделка.
task_needed=true если нужен следующий шаг.
Верни только JSON начинающийся с {"""
    
    user_prompt = f"""Отчет:
{text}

Верни JSON:
{{
  "клиника": "",
  "contact_name": "",
  "должность": "",
  "decision_maker": "",
  "телефон": "",
  "реакция": "",
  "next_step": "",
  "next_step_date": "",
  "lead_status": "Интерес",
  "task_needed": false,
  "task_title": "",
  "task_priority": "Средний",
  "interaction_result": "",
  "ответственный": "{first_name}",
  "comment": ""
}}"""
    
    import httpx
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://crm-bot.example.com",
        "X-Title": "CRM Bot"
    }
    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers
        )
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        
        # Парсим JSON
        try:
            parsed = json.loads(content)
        except:
            parsed = {"клиника": "Не распознано", "lead_status": "Ошибка"}
        
        # Формируем ответ
        status_emoji = {"Интерес": "🤔", "Переговоры": "💬", "Сделка": "✅"}
        status = parsed.get("lead_status", "Интерес")
        
        response = f"""✅ <b>Отчет сохранен!</b>

🏥 Клиника: {parsed.get('клиника', '-')}
👤 Контакт: {parsed.get('contact_name', '-')}
📊 Статус: {status_emoji.get(status, '📋')} {status}

📌 Следующий шаг: {parsed.get('next_step', '-') or '—'}
📅 Дедлайн: {parsed.get('next_step_date', '-') or '—'}

Данные записаны в CRM."""
        
        return response


async def send_message(chat_id: str, text: str) -> dict:
    """Отправить сообщение в Telegram."""
    import httpx
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        )
        return r.json()


async def health(request: web.Request) -> web.Response:
    """Health check."""
    return web.Response(text="OK")


def create_app() -> web.Application:
    """Создать приложение."""
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    app.router.add_get("/health", health)
    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)