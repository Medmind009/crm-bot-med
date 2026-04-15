"""
Обработчик создания лида (вопрос → ответ).
"""
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
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

# Поля которые НЕЛЬЗЯ пропускать (обязательные)
required_fields = ["clinic_name", "channel"]

# Подсказки для полей
field_hints = {
    "clinic_name": "Название клиники",
    "district": "Район",
    "address": "Адрес",
    "contact_name": "Контактное лицо",
    "position": "Должность",
    "decision_maker": "ЛПР?",
    "phone": "Телефон",
    "email": "Email",
    "telegram": "Telegram/WhatsApp",
    "channel": "Канал первого контакта",
    "sent_materials": "Что передали клиенту",
    "reaction": "Реакция клиента",
    "next_step": "Следующий шаг",
    "comment": "Комментарий",
}

# Поля где нужно показать кнопки выбора
select_fields = {
    "channel": CONTACT_CHANNELS,
    "decision_maker": ["Да", "Нет", "Неизвестно"],
}


def get_field_keyboard(field: str) -> ReplyKeyboardMarkup:
    """Клавиатура для поля с Пропустить/Сохранить."""
    keyboard = []
    
    # Пропустить только если поле не обязательное
    if field not in required_fields:
        keyboard.append([KeyboardButton("⏭ Пропустить")])
    
    # Всегда показываем Сохранить
    keyboard.append([KeyboardButton("💾 Сохранить и далее")])
    keyboard.append([KeyboardButton("❌ Отмена")])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start_lead_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать создание лида."""
    context.user_data["lead_data"] = {}
    context.user_data["lead_step"] = 0
    context.user_data["lead_saved"] = False  # Флаг что лид уже сохранён
    
    # Для первого поля показываем клавиатуру
    await update.message.reply_text(
        "📝 <b>Создание нового лида</b>\n\n"
        "Введите название клиники:",
        reply_markup=get_field_keyboard("clinic_name"),
        parse_mode="HTML"
    )


async def handle_lead_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода данных лида."""
    text = update.message.text.strip()
    lead_data = context.user_data.get("lead_data", {})
    current_step = context.user_data.get("lead_step", 0)
    field = lead_fields[current_step]
    
    # Обработка команд
    if text.lower() in ["⏭ пропустить", "пропустить", "skip"]:
        # Пропуск поля (только для необязательных)
        if field in required_fields:
            await update.message.reply_text(
                f"❌ Это обязательное поле. Введите {field_hints.get(field, field)}:",
                reply_markup=get_field_keyboard(field),
                parse_mode="HTML"
            )
            return
        
        lead_data[field] = ""
        context.user_data["lead_data"] = lead_data
        current_step += 1
        context.user_data["lead_step"] = current_step
        
        if current_step >= len(lead_fields):
            await finish_lead_creation(update, context)
        else:
            await ask_next_field(update, context, lead_fields[current_step])
        return
    
    if text == "💾 Сохранить и далее":
        # Сохраняем текущий прогресс и показываем итог
        await save_partial_lead(update, context, show_menu=True)
        return
    
    if text.lower() in ["отмена", "cancel", "❌ отмена"]:
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
    # Специальная обработка для канала
    if field == "channel":
        if text not in CONTACT_CHANNELS:
            await update.message.reply_text(
                f"Пожалуйста, выберите из списка:\n" + "\n".join(f"• {c}" for c in CONTACT_CHANNELS),
                reply_markup=get_field_keyboard(field),
                parse_mode="HTML"
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
    """Задать следующий вопрос с кнопками."""
    hint = field_hints.get(field, field)
    
    # Проверяем есть ли варианты выбора
    if field in select_fields:
        options = select_fields[field]
        options_text = "Выберите:\n" + "\n".join(f"• {o}" for o in options)
        await update.message.reply_text(
            f"<b>{hint}</b>\n\n{options_text}",
            reply_markup=get_field_keyboard(field),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            f"<b>{hint}</b>",
            reply_markup=get_field_keyboard(field),
            parse_mode="HTML"
        )


async def save_partial_lead(update: Update, context: ContextTypes.DEFAULT_TYPE, show_menu: bool = False):
    """Сохранить лид с текущими данными (можно продолжить позже)."""
    lead_data = context.user_data.get("lead_data", {})
    user = update.message.from_user
    responsible = user.first_name or user.username or "Менеджер"
    current_step = context.user_data.get("lead_step", 0)
    
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
        context.user_data["lead_saved"] = True
        context.user_data["lead_id"] = lead_id
        
        # Формируем ответ
        status_emoji = {
            "Новый": "📋", "Интерес": "🤔", "Переговоры": "💬",
            "Ожидание ответа": "⏳", "Предложено": "📤", "Сделка": "✅",
            "Отказ": "❌", "Неактуально": "🚫",
        }.get(lead_data.get("status", "Новый"), "📋")
        
        # Показываем что уже заполнено
        filled = []
        for f in lead_fields[:current_step+1]:
            val = lead_data.get(f, "")
            if val:
                filled.append(f"• {field_hints.get(f, f)}: {val[:30]}")
        
        response = f"""✅ <b>Лид сохранён!</b> (можно редактировать позже)

🏥 <b>{lead_data.get('clinic_name', '-')}</b>
📊 Статус: {status_emoji} {lead_data.get('status', 'Новый')}
🆔 ID: {lead_id}

Заполнено ({current_step+1}/{len(lead_fields)}):
{chr(10).join(filled) if filled else 'Пока нет данных'}

Чтобы продолжить заполнение - вернитесь в меню и выберите "🗂 Карточка лида" → найдите этот лид → "Редактировать" """

        await update.message.reply_text(response, parse_mode="HTML")
        
        if show_menu:
            context.user_data.clear()
            from bot.handlers.menu import show_main_menu
            await show_main_menu(update, context)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при сохранении: {e}")


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