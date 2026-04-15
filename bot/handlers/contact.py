"""
Обработчик касаний (контактов с лидом).
"""
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from bot.types import INTERACTION_FORMATS
from bot.sheets_service import sheets_service
from bot.ai_service import ai_service


contact_fields = [
    "format",            # Обязательно (выбор)
    "what_happened",     # Обязательно
    "sent_materials",    # Можно пропустить
    "client_questions",  # Можно пропустить
    "answers_given",     # Можно пропустить
    "result",            # Обязательно
    "comment",           # Можно пропустить
]

# Обязательные поля (нельзя пропустить)
required_contact_fields = ["format", "what_happened", "result"]

field_hints = {
    "format": "Формат контакта",
    "what_happened": "Что произошло (кратко)",
    "sent_materials": "Что передали клиенту",
    "client_questions": "Вопросы клиента",
    "answers_given": "Что ответили",
    "result": "Итог взаимодействия",
    "comment": "Комментарий",
}

select_fields = {
    "format": INTERACTION_FORMATS,
}


def get_contact_keyboard(field: str) -> ReplyKeyboardMarkup:
    """Клавиатура для поля касания."""
    keyboard = []
    
    if field not in required_contact_fields:
        keyboard.append([KeyboardButton("⏭ Пропустить")])
    
    keyboard.append([KeyboardButton("💾 Сохранить и далее")])
    keyboard.append([KeyboardButton("❌ Отмена")])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start_contact_creation(update: Update, context: ContextTypes.DEFAULT_TYPE, lead_id: str):
    """Начать создание касания для выбранного лида."""
    context.user_data["contact_lead_id"] = lead_id
    context.user_data["contact_data"] = {}
    context.user_data["contact_step"] = 0
    
    # Получаем инфо о лиде
    lead = sheets_service.find_lead_by_id(lead_id)
    context.user_data["lead_info"] = lead
    
    await update.message.reply_text(
        f"📞 <b>Новое касание</b>\n\n"
        f"Лид: {lead.get('Название клиники', 'Неизвестно')}\n\n"
        f"Выберите формат контакта:",
        reply_markup=get_contact_keyboard("format"),
        parse_mode="HTML"
    )


async def handle_contact_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода данных касания."""
    text = update.message.text.strip()
    contact_data = context.user_data.get("contact_data", {})
    current_step = context.user_data.get("contact_step", 0)
    field = contact_fields[current_step]
    flow = context.user_data.get("flow", "")
    
    # Пропуск
    if text.lower() in ["⏭ пропустить", "пропустить", "skip"]:
        if field in required_contact_fields:
            await update.message.reply_text(
                f"❌ Это обязательное поле. Введите {field_hints.get(field, field)}:",
                reply_markup=get_contact_keyboard(field),
                parse_mode="HTML"
            )
            return
        
        contact_data[field] = ""
        context.user_data["contact_data"] = contact_data
        current_step += 1
        context.user_data["contact_step"] = current_step
        
        if current_step >= len(contact_fields):
            await finish_contact_creation(update, context)
        else:
            await ask_next_contact_field(update, context, contact_fields[current_step])
        return
    
    # Сохранить и далее
    if text == "💾 Сохранить и далее":
        await save_partial_contact(update, context, show_menu=True)
        return
    
    # Отмена
    if text.lower() in ["отмена", "cancel", "❌ отмена"]:
        context.user_data.clear()
        from bot.handlers.menu import show_main_menu
        await show_main_menu(update, context)
        return
    
    # Назад
    if text == "⬅️ Назад":
        if current_step > 0:
            current_step -= 1
            context.user_data["contact_step"] = current_step
            await ask_next_contact_field(update, context, contact_fields[current_step])
        return
    
    # Сохранение
    if field == "format":
        if text not in INTERACTION_FORMATS:
            await update.message.reply_text(
                f"Пожалуйста, выберите из списка:\n" + "\n".join(f"• {f}" for f in INTERACTION_FORMATS),
                reply_markup=get_contact_keyboard(field),
                parse_mode="HTML"
            )
            return
    
    contact_data[field] = text
    context.user_data["contact_data"] = contact_data
    current_step += 1
    context.user_data["contact_step"] = current_step
    
    if current_step >= len(contact_fields):
        await finish_contact_creation(update, context)
    else:
        await ask_next_contact_field(update, context, contact_fields[current_step])


async def ask_next_contact_field(update: Update, context: ContextTypes.DEFAULT_TYPE, field: str):
    """Задать следующий вопрос для касания."""
    hint = field_hints.get(field, field)
    
    if field in select_fields:
        options = select_fields[field]
        await update.message.reply_text(
            f"<b>{hint}</b>\n\n" + "\n".join(f"• {o}" for o in options),
            reply_markup=get_contact_keyboard(field),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            f"<b>{hint}</b>",
            reply_markup=get_contact_keyboard(field),
            parse_mode="HTML"
        )


async def save_partial_contact(update: Update, context: ContextTypes.DEFAULT_TYPE, show_menu: bool = False):
    """Сохранить касание с текущими данными."""
    contact_data = context.user_data.get("contact_data", {})
    lead_id = context.user_data.get("contact_lead_id", "")
    lead_info = context.user_data.get("lead_info", {})
    user = update.message.from_user
    who = user.first_name or user.username or "Менеджер"
    current_step = context.user_data.get("contact_step", 0)
    
    # AI определяет следующий шаг
    try:
        ai_result = await ai_service.determine_contact_next_step(
            contact_data.get("what_happened", "") + " " + contact_data.get("result", ""),
            lead_info
        )
        if ai_result.next_step and not contact_data.get("next_step"):
            contact_data["next_step"] = ai_result.next_step
        if ai_result.result and not contact_data.get("result"):
            contact_data["result"] = ai_result.result
    except Exception as e:
        print(f"AI contact error: {e}")
    
    # Запись в Google Sheets
    try:
        contact_id = sheets_service.add_contact(lead_id, contact_data, who)
        
        clinic_name = lead_info.get("Название клиники", "Клиника")
        
        filled = []
        for f in contact_fields[:current_step+1]:
            val = contact_data.get(f, "")
            if val:
                filled.append(f"• {field_hints.get(f, f)}: {val[:30]}")
        
        response = f"""✅ <b>Касание сохранено!</b>

🏥 Клиника: {clinic_name}
🆔 ID касания: {contact_id}

Заполнено ({current_step+1}/{len(contact_fields)}):
{chr(10).join(filled) if filled else 'Пока нет данных'}

Чтобы добавить данные - создайте новое касание для этого лида."""
        
        await update.message.reply_text(response, parse_mode="HTML")
        
        if show_menu:
            context.user_data.clear()
            from bot.handlers.menu import show_main_menu
            await show_main_menu(update, context)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def finish_contact_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение создания касания."""
    contact_data = context.user_data.get("contact_data", {})
    lead_id = context.user_data.get("contact_lead_id", "")
    lead_info = context.user_data.get("lead_info", {})
    user = update.message.from_user
    who = user.first_name or user.username or "Менеджер"
    
    # AI определяет следующий шаг
    try:
        ai_result = await ai_service.determine_contact_next_step(
            contact_data.get("what_happened", "") + " " + contact_data.get("result", ""),
            lead_info
        )
        if ai_result.next_step and not contact_data.get("next_step"):
            contact_data["next_step"] = ai_result.next_step
        if ai_result.result and not contact_data.get("result"):
            contact_data["result"] = ai_result.result
    except Exception as e:
        print(f"AI contact error: {e}")
    
    # Запись в Google Sheets
    try:
        contact_id = sheets_service.add_contact(lead_id, contact_data, who)
        
        # Обновляем лид
        update_data = {}
        if contact_data.get("result"):
            update_data["reaction"] = contact_data["result"]
        if contact_data.get("next_step"):
            update_data["next_step"] = contact_data["next_step"]
        
        if update_data:
            sheets_service.update_lead(lead_id, update_data)
        
        clinic_name = lead_info.get("Название клиники", "Клиника")
        
        response = f"""✅ <b>Касание добавлено!</b>

🏥 Клиника: {clinic_name}
📞 Формат: {contact_data.get('format', '-')}
📝 Итог: {contact_data.get('result', '-')}

📌 Следующий шаг: {contact_data.get('next_step', '-')}

🆔 ID касания: {contact_id}"""
        
        await update.message.reply_text(response, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    
    context.user_data.clear()
    from bot.handlers.menu import show_main_menu
    await show_main_menu(update, context)