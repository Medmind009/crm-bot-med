"""
Обработчик поиска лидов и выбора лида для других операций.
"""
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from bot.sheets_service import sheets_service


async def search_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск лидов по названию."""
    text = update.message.text.strip()
    
    # Ищем лиды
    leads = sheets_service.get_all_leads()
    
    # Фильтруем по названию
    matching = []
    for lead in leads:
        name = lead.get("Название клиники", "")
        if text.lower() in name.lower():
            matching.append(lead)
    
    if not matching:
        await update.message.reply_text(
            "🔍 Лиды не найдены. Попробуйте другой запрос.",
            parse_mode="HTML"
        )
        return
    
    # Показываем результаты
    response = "🔍 <b>Найденные лиды:</b>\n\n"
    for i, lead in enumerate(matching[:10], 1):
        name = lead.get("Название клиники", "-")
        status = lead.get("Статус", "-")
        contact = lead.get("Контактное лицо", "-")
        response += f"{i}. <b>{name}</b>\n   👤 {contact} | 📊 {status}\n\n"
    
    await update.message.reply_text(response, parse_mode="HTML")


async def show_leads_for_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список лидов для выбора (для касания/задачи/карточки)."""
    leads = sheets_service.get_all_leads()
    
    if not leads:
        await update.message.reply_text("❌ Лиды не найдены. Сначала создайте лид.")
        return
    
    # Создаём клавиатуру с лидами
    keyboard = []
    for lead in leads[:20]:  # Максимум 20
        name = lead.get("Название клиники", "Без названия")[:30]
        keyboard.append([KeyboardButton(name)])
    
    keyboard.append([KeyboardButton("❌ Отмена")])
    
    flow = context.user_data.get("flow", "")
    prompt = "Выберите лид:"
    
    if "contact" in flow:
        prompt = "📞 Выберите лида для нового касания:"
    elif "task" in flow:
        prompt = "✅ Выберите лида для новой задачи:"
    elif "card" in flow:
        prompt = "🗂 Выберите лида для просмотра карточки:"
    
    await update.message.reply_text(
        prompt,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="HTML"
    )


async def handle_lead_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора лида из списка."""
    text = update.message.text.strip()
    flow = context.user_data.get("flow", "")
    
    # Находим лид по названию
    leads = sheets_service.get_all_leads()
    selected = None
    for lead in leads:
        if text == lead.get("Название клиники", "")[:30]:
            selected = lead
            break
    
    if not selected:
        await update.message.reply_text("❌ Лид не найден. Попробуйте снова.")
        return
    
    lead_id = selected.get("ID", "")
    
    # Перенаправляем в соответствующий flow
    if "contact" in flow:
        from bot.handlers.contact import start_contact_creation
        await start_contact_creation(update, context, lead_id)
    elif "task" in flow:
        from bot.handlers.task import start_task_creation
        await start_task_creation(update, context, lead_id)
    elif "card" in flow:
        from bot.handlers.card import show_lead_card
        await show_lead_card(update, context, lead_id)
    else:
        await update.message.reply_text("Ошибка flow. Начните заново.")