"""
Инициализация бота и регистрация обработчиков.
Webhook версия для Render.
"""
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from bot.handlers.menu import show_main_menu, handle_menu_choice
from bot.handlers.lead import handle_lead_input, start_lead_creation
from bot.handlers.contact import handle_contact_input
from bot.handlers.task import handle_task_input
from bot.handlers.search import search_leads, show_leads_for_selection, handle_lead_selection
from bot.handlers.card import handle_card_callback


# Токен бота (из env или по умолчанию)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") or "8712375566:AAGqUCjIf6MPy68Ayvrlx3LYZSdZxWLjgpE"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start."""
    await show_main_menu(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help."""
    await update.message.reply_text(
        "📖 <b>Справка CRM-бота</b>\n\n"
        "Команды:\n"
        "/start — Главное меню\n"
        "/menu — Показать меню\n"
        "/help — Эта справка\n\n"
        "Или просто выберите действие из меню.",
        parse_mode="HTML"
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /menu."""
    await show_main_menu(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик сообщений."""
    text = update.message.text.strip()
    flow = context.user_data.get("flow", "")
    
    if flow == "lead":
        await handle_lead_input(update, context)
    elif flow == "contact_select_lead":
        await handle_lead_selection(update, context)
    elif flow == "contact":
        await handle_contact_input(update, context)
    elif flow == "task_select_lead":
        await handle_lead_selection(update, context)
    elif flow == "task":
        await handle_task_input(update, context)
    elif flow == "card_select_lead":
        await handle_lead_selection(update, context)
    elif flow == "search":
        await search_leads(update, context)
    else:
        await handle_menu_choice(update, context)


def run_bot():
    """Запуск бота."""
    from telegram.ext import ApplicationBuilder
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu_command))
    
    # Обработчик callback (inline кнопок)
    app.add_handler(CallbackQueryHandler(handle_card_callback))
    
    # Обработчик сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # webhook URL ( Render дает URL )
    webhook_url = os.environ.get("WEBHOOK_URL")
    port = int(os.environ.get("PORT", 8080))
    
    if webhook_url:
        # Webhook режим для production
        app.bot.delete_webhook()
        app.bot.set_webhook(url=f"{webhook_url}/{TELEGRAM_TOKEN}")
        print(f"🔗 Webhook: {webhook_url}")
        print(f"🚀 Бот запущен на порту {port}")
        
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=f"/{TELEGRAM_TOKEN}",
            drop_pending_updates=True
        )
    else:
        # Polling режим для локального запуска
        print("🚀 Бот запущен (polling)")
        app.run_polling(poll_interval=1.0, drop_pending_updates=True)