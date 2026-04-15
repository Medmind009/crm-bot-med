"""
Обработчик касаний (контактов с лидом).
"""
from telegram import Update
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

field_hints = {
    "format": "Формат контакта",
    "what_happened": "Что произошло (кратко)",
    "sent_materials": "Что передали клиенту (или 'пропустить')",
    "client_questions": "Вопросы клиента (или 'пропустить')",
    "answers_given": "Что ответили (или 'пропустить')",
    "result": "Итог взаимодействия",
    "comment": "Комментарий (или 'пропустить')",
}

select_fields = {
    "format": INTERACTION_FORMATS,
}


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
        parse_mode="HTML"
    )


async def handle_contact_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода данных касания."""
    text = update.message.text.strip()
    contact_data = context.user_data.get("contact_data", {})
    current_step = context.user_data.get("contact_step", 0)
    flow = context.user_data.get("flow", "")
    
    # Пропуск
    if text.lower() in ["пропустить", "skip", "-"]:
        field = contact_fields[current_step]
        contact_data[field] = ""
        context.user_data["contact_data"] = contact_data
        current_step += 1
        context.user_data["contact_step"] = current_step
        
        if current_step >= len(contact_fields):
            await finish_contact_creation(update, context)
        else:
            await ask_next_contact_field(update, context, contact_fields[current_step])
        return
    
    # Отмена
    if text.lower() in ["отмена", "cancel"]:
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
    field = contact_fields[current_step]
    
    if field == "format":
        if text not in INTERACTION_FORMATS:
            await update.message.reply_text(
                "Пожалуйста, выберите из списка:\n" + "\n".join(f"• {f}" for f in INTERACTION_FORMATS)
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
            f"{hint}\n\n" + "\n".join(f"• {o}" for o in options)
        )
    else:
        await update.message.reply_text(
            f"{hint}\n\nНажмите 'Пропустить' чтобы пропустить.",
            parse_mode="HTML"
        )


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