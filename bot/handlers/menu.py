"""
Главное меню бота.
"""
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from bot.types import MENU_KEYBOARD


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню."""
    keyboard = MENU_KEYBOARD
    
    # Добавляем кнопки Назад и Отмена если нужно
    extra_buttons = []
    if context.user_data.get("state"):
        extra_buttons.append(KeyboardButton("⬅️ Назад"))
    extra_buttons.append(KeyboardButton("❌ Отмена"))
    
    if extra_buttons:
        keyboard.append(extra_buttons)
    
    await update.message.reply_text(
        "🏠 <b>Главное меню CRM</b>\n\nВыберите действие:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="HTML"
    )


async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора из меню."""
    text = update.message.text
    
    if text == "➕ Новый лид":
        context.user_data["flow"] = "lead"
        context.user_data["lead_data"] = {}
        await update.message.reply_text(
            "📝 <b>Создание нового лида</b>\n\n"
            "Введите название клиники:",
            parse_mode="HTML"
        )
    
    elif text == "📞 Новое касание":
        # Сначала нужно выбрать лида
        from bot.handlers.search import show_leads_for_selection
        context.user_data["flow"] = "contact_select_lead"
        await show_leads_for_selection(update, context)
    
    elif text == "✅ Новая задача":
        from bot.handlers.search import show_leads_for_selection
        context.user_data["flow"] = "task_select_lead"
        await show_leads_for_selection(update, context)
    
    elif text == "🗂 Карточка лида":
        from bot.handlers.search import show_leads_for_selection
        context.user_data["flow"] = "card_select_lead"
        await show_leads_for_selection(update, context)
    
    elif text == "🔎 Поиск лида":
        context.user_data["flow"] = "search"
        await update.message.reply_text(
            "🔍 <b>Поиск лида</b>\n\nВведите название клиники для поиска:",
            parse_mode="HTML"
        )
    
    elif text == "❌ Отмена":
        context.user_data.clear()
        await show_main_menu(update, context)
    
    elif text == "⬅️ Назад":
        # Возврат назад по flow
        flow = context.user_data.get("flow", "")
        if "lead" in flow:
            # Сброс лида
            context.user_data["lead_data"] = {}
            await update.message.reply_text(
                "📝 <b>Создание нового лида</b>\n\nВведите название клиники:",
                parse_mode="HTML"
            )
        else:
            await show_main_menu(update, context)
    
    else:
        await update.message.reply_text("Выберите действие из меню.")


async def handle_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка 'Пропустить'."""
    flow = context.user_data.get("flow", "")
    lead_data = context.user_data.get("lead_data", {})
    
    if "lead" in flow:
        # Пропуск поля лида - переход к следующему
        field = context.user_data.get("current_field", "")
        lead_data[field] = ""
        context.user_data["lead_data"] = lead_data
        
        # Продолжаем flow
        from bot.handlers.lead import lead_fields, ask_next_field
        next_field = lead_fields[lead_fields.index(field) + 1] if field in lead_fields else None
        if next_field:
            await ask_next_field(update, context, next_field)
        else:
            # Завершаем
            from bot.handlers.lead import finish_lead_creation
            await finish_lead_creation(update, context)