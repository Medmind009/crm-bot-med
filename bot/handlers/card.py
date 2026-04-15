"""
Обработчик карточки лида.
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.sheets_service import sheets_service


async def show_lead_card(update: Update, context: ContextTypes.DEFAULT_TYPE, lead_id: str):
    """Показать карточку лида."""
    # Получаем данные лида
    lead = sheets_service.find_lead_by_id(lead_id)
    
    if not lead:
        await update.message.reply_text("❌ Лид не найден.")
        return
    
    # Получаем касания
    contacts = sheets_service.get_contacts_for_lead(lead_id)
    
    # Получаем задачи
    tasks = sheets_service.get_tasks_for_lead(lead_id)
    open_tasks = [t for t in tasks if t.get("Статус задачи") in ["Новая", "В работе"]]
    
    # Формируем карточку
    name = lead.get("Название клиники", "-")
    status = lead.get("Статус", "Новый")
    responsible = lead.get("Ответственный", "-")
    created = lead.get("Дата создания", "-")
    
    status_emoji = {
        "Новый": "📋",
        "Интерес": "🤔",
        "Переговоры": "💬",
        "Ожидание ответа": "⏳",
        "Предложено": "📤",
        "Сделка": "✅",
        "Отказ": "❌",
        "Неактуально": "🚫",
    }.get(status, "📋")
    
    # Основная информация
    response = f"""🗂 <b>Карточка лида</b>

<b>{name}</b>
📊 Статус: {status_emoji} {status}
👤 Ответственный: {responsible}
📅 Создан: {created}

<b>Контакты:</b>
👤 {lead.get('Контактное лицо', '-')}
📌 {lead.get('Должность', '-')}
📱 {lead.get('Телефон', '-')}
📨 {lead.get('Telegram / WhatsApp', '-')}

<b>Детали:</b>
📍 {lead.get('Адрес', '-')}
🏠 {lead.get('Район', '-')}
📢 Канал: {lead.get('Канал первого контакта', '-')}
📎 Передано: {lead.get('Что передали', '-')}

<b>Текущее:</b>
💬 Реакция: {lead.get('Реакция', '-')}
📌 Шаг: {lead.get('Следующий шаг', '-')}
📅 Дата: {lead.get('Дата следующего касания', '-')}

💬 Комментарий: {lead.get('Комментарий', '-')}"""
    
    # История касаний
    if contacts:
        last_contact = contacts[-1]
        response += f"""

<b>Последнее касание:</b>
📅 {last_contact.get('Дата', '-')}
📞 {last_contact.get('Формат контакта', '-')}
📝 {last_contact.get('Что произошло', '-')}"""
        
        if len(contacts) > 1:
            response += f"\n(всего касаний: {len(contacts)})"
    
    # Задачи
    if open_tasks:
        response += f"\n\n<b>Открытые задачи:</b>\n"
        for task in open_tasks[:3]:
            priority = task.get("Приоритет", "Средний")
            emoji = "🔴" if priority == "Высокий" else "🟡" if priority == "Средний" else "🟢"
            response += f"• {emoji} {task.get('Задача', '-')}\n"
    
    # Кнопки действий
    keyboard = [
        [InlineKeyboardButton("📞 Добавить касание", callback_data=f"add_contact_{lead_id}")],
        [InlineKeyboardButton("✅ Создать задачу", callback_data=f"add_task_{lead_id}")],
        [InlineKeyboardButton("🔎 К списку лидов", callback_data="back_to_leads")],
    ]
    
    await update.message.reply_text(
        response,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def handle_card_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback от карточки лида."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("add_contact_"):
        lead_id = data.replace("add_contact_", "")
        from bot.handlers.contact import start_contact_creation
        await start_contact_creation(update, context, lead_id)
    
    elif data.startswith("add_task_"):
        lead_id = data.replace("add_task_", "")
        from bot.handlers.task import start_task_creation
        await start_task_creation(update, context, lead_id)
    
    elif data == "back_to_leads":
        from bot.handlers.search import show_leads_for_selection
        context.user_data["flow"] = "card_select_lead"
        await show_leads_for_selection(update, context)