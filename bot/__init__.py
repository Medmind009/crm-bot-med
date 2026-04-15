"""
Инициализация бота и регистрация обработчиков.
"""
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


# Токен бота
TELEGRAM_TOKEN = "8712375566:AAGqUCjIf6MPy68Ayvrlx3LYZSdZxWLjgpE"


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
    
    # Если это callback query (кнопки в карточке)
    # обрабатывается отдельно
    
    # Проверяем какой flow активен
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
        # Это меню
        await handle_menu_choice(update, context)


def run_bot():
    """Запуск бота."""
    # Создаём приложение
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu_command))
    
    # Обработчик callback (inline кнопок)
    app.add_handler(CallbackQueryHandler(handle_card_callback))
    
    # Обработчик сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 Бот запущен!")
    
    # Запускаем polling
    app.run_polling(poll_interval=1.0)


if __name__ == "__main__":
    run_bot()