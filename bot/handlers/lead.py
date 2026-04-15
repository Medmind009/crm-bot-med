"""
Обработчик создания лида (вопрос → ответ).
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.types import CONTACT_CHANNELS, LeadStatus
from bot.sheets_service import sheets_service
from bot.ai_service import ai_service

# Порядок полей для заполнения
lead_fields = [
    "clinic_name",      # Обязательно
    "district",         # Можно пропустить
    "address",          # Можно пропустить
    "contact_name",     # Можно пропустить
    "position",         # Можно пропустить
    "decision_maker",   # Можно пропустить
    "phone",            # Можно пропустить
    "email",            # Можно пропустить
    "telegram",         # Можно пропустить
    "channel",          # Обязательно (выбор из списка)
    "sent_materials",   # Можно пропустить
    "reaction",         # Можно пропустить
    "next_step",        # Можно пропустить
    "comment",          # Можно пропустить
]

# Подсказки для полей
field_hints = {
    "clinic_name": "Название клиники (обязательно)",
    "district": "Район (или 'пропустить')",
    "address": "Адрес (или 'пропустить')",
    "contact_name": "Контактное лицо (или 'пропустить')",
    "position": "Должность (или 'пропустить')",
    "decision_maker": "ЛПР? (да/нет, или 'пропустить')",
    "phone": "Телефон (или 'пропустить')",
    "email": "Email (или 'пропустить')",
    "telegram": "Telegram/WhatsApp (или 'пропустить')",
    "channel": "Канал первого контакта",
    "sent_materials": "Что передали клиенту (или 'пропустить')",
    "reaction": "Реакция клиента (или 'пропустить')",
    "next_step": "Следующий шаг (или 'пропустить')",
    "comment": "Комментарий (или 'пропустить')",
}

# Поля где нужно показать кнопки выбора
select_fields = {
    "channel": CONTACT_CHANNELS,
    "decision_maker": ["Да", "Нет", "Неизвестно"],
}


async def start_lead_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать создание лида."""
    context.user_data["lead_data"] = {}
    context.user_data["lead_step"] = 0
    await update.message.reply_text(
        "📝 <b>Создание нового лида</b>\n\n"
        "Введите название клиники:",
        parse_mode="HTML"
    )


async def handle_lead_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода данных лида."""
    text = update.message.text.strip()
    lead_data = context.user_data.get("lead_data", {})
    current_step = context.user_data.get("lead_step", 0)
    
    # Обработка команд
    if text.lower() in ["пропустить", "skip", "-"]:
        # Пропуск поля
        field = lead_fields[current_step]
        lead_data[field] = ""
        context.user_data["lead_data"] = lead_data
        current_step += 1
        context.user_data["lead_step"] = current_step
        
        if current_step >= len(lead_fields):
            await finish_lead_creation(update, context)
        else:
            await ask_next_field(update, context, lead_fields[current_step])
        return
    
    if text.lower() in ["отмена", "cancel"]:
        context.user_data.clear()
        from bot.handlers.menu import show_main_menu
        await show_main_menu(update, context)
        return
    
    # Обработка "Назад"
    if text == "⬅️ Назад":
        if current_step > 0:
            current_step -= 1
            context.user_data["lead_step"] = current_step
            await ask_next_field(update, context, lead_fields[current_step])
        return
    
    # Сохранение значения
    field = lead_fields[current_step]
    
    # Специальная обработка для канала
    if field == "channel":
        # Проверяем что выбрано из списка
        if text not in CONTACT_CHANNELS:
            await update.message.reply_text(
                f"Пожалуйста, выберите из списка:\n" + "\n".join(f"• {c}" for c in CONTACT_CHANNELS)
            )
            return
    
    lead_data[field] = text
    context.user_data["lead_data"] = lead_data
    current_step += 1
    context.user_data["lead_step"] = current_step
    
    if current_step >= len(lead_fields):
        await finish_lead_creation(update, context)
    else:
        await ask_next_field(update, context, lead_fields[current_step])


async def ask_next_field(update: Update, context: ContextTypes.DEFAULT_TYPE, field: str):
    """Задать следующий вопрос."""
    hint = field_hints.get(field, field)
    
    # Проверяем есть ли варианты выбора
    if field in select_fields:
        options = select_fields[field]
        options_text = "Выберите:\n" + "\n".join(f"• {o}" for o in options)
        await update.message.reply_text(
            f"{hint}\n\n{options_text}",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            f"{hint}\n\nНажмите 'Пропустить' чтобы пропустить это поле.",
            parse_mode="HTML"
        )


async def finish_lead_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение создания лида."""
    lead_data = context.user_data.get("lead_data", {})
    user = update.message.from_user
    responsible = user.first_name or user.username or "Менеджер"
    
    # AI определяет статус
    try:
        context_for_ai = {
            "clinic_name": lead_data.get("clinic_name", ""),
            "contact_name": lead_data.get("contact_name", ""),
            "reaction": lead_data.get("reaction", ""),
            "sent_materials": lead_data.get("sent_materials", ""),
        }
        ai_result = await ai_service.determine_lead_status(
            f"Клиника: {lead_data.get('clinic_name')}, Реакция: {lead_data.get('reaction')}",
            context_for_ai
        )
        lead_data["status"] = ai_result.status
        if ai_result.next_step and not lead_data.get("next_step"):
            lead_data["next_step"] = ai_result.next_step
        if ai_result.next_step_date and not lead_data.get("next_step_date"):
            lead_data["next_step_date"] = ai_result.next_step_date
    except Exception as e:
        print(f"AI error: {e}")
        lead_data["status"] = "Новый"
    
    # Запись в Google Sheets
    try:
        lead_id = sheets_service.add_lead(lead_data, responsible)
        lead_data["id"] = lead_id
        
        # Формируем ответ пользователю
        status_emoji = {
            "Новый": "📋",
            "Интерес": "🤔",
            "Переговоры": "💬",
            "Ожидание ответа": "⏳",
            "Предложено": "📤",
            "Сделка": "✅",
            "Отказ": "❌",
            "Неактуально": "🚫",
        }.get(lead_data.get("status", "Новый"), "📋")
        
        response = f"""✅ <b>Лид создан!</b>

🏥 <b>{lead_data.get('clinic_name', '-')}</b>
👤 {lead_data.get('contact_name', '-')}
📊 Статус: {status_emoji} {lead_data.get('status', 'Новый')}

📱 Телефон: {lead_data.get('phone', '-')}
📱 Telegram: {lead_data.get('telegram', '-')}
📍 Адрес: {lead_data.get('address', '-')}

📌 Следующий шаг: {lead_data.get('next_step', '-')}
📅 Дата: {lead_data.get('next_step_date', '-')}

🆔 ID: {lead_id}"""
        
        await update.message.reply_text(response, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при сохранении: {e}",
            parse_mode="HTML"
        )
    
    # Очищаем и показываем меню
    context.user_data.clear()
    from bot.handlers.menu import show_main_menu
    await show_main_menu(update, context)