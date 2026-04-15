"""
Обработчик задач.
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.sheets_service import sheets_service
from bot.ai_service import ai_service


task_fields = [
    "context",           # Обязательно (контекст от менеджера)
    "deadline",          # Можно пропустить
    "comment",           # Можно пропустить
]

field_hints = {
    "context": "Опишите ситуацию/контекст для создания задачи",
    "deadline": "Дедлайн (YYYY-MM-DD) или 'пропустить'",
    "comment": "Комментарий (или 'пропустить')",
}


async def start_task_creation(update: Update, context: ContextTypes.DEFAULT_TYPE, lead_id: str):
    """Начать создание задачи для лида."""
    context.user_data["task_lead_id"] = lead_id
    context.user_data["task_data"] = {}
    context.user_data["task_step"] = 0
    
    lead = sheets_service.find_lead_by_id(lead_id)
    context.user_data["lead_info"] = lead
    
    await update.message.reply_text(
        f"✅ <b>Новая задача</b>\n\n"
        f"Лид: {lead.get('Название клиники', 'Неизвестно')}\n\n"
        f"{field_hints['context']}\n\n"
        f"Не нужно формулировать задачу — просто опишите ситуацию, а AI сформирует задачу.",
        parse_mode="HTML"
    )


async def handle_task_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода данных задачи."""
    text = update.message.text.strip()
    task_data = context.user_data.get("task_data", {})
    current_step = context.user_data.get("task_step", 0)
    
    # Пропуск
    if text.lower() in ["пропустить", "skip", "-"]:
        field = task_fields[current_step]
        task_data[field] = ""
        context.user_data["task_data"] = task_data
        current_step += 1
        context.user_data["task_step"] = current_step
        
        if current_step >= len(task_fields):
            await finish_task_creation(update, context)
        else:
            await ask_next_task_field(update, context, task_fields[current_step])
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
            context.user_data["task_step"] = current_step
            await ask_next_task_field(update, context, task_fields[current_step])
        return
    
    # Сохранение
    field = task_fields[current_step]
    task_data[field] = text
    context.user_data["task_data"] = task_data
    current_step += 1
    context.user_data["task_step"] = current_step
    
    if current_step >= len(task_fields):
        await finish_task_creation(update, context)
    else:
        await ask_next_task_field(update, context, task_fields[current_step])


async def ask_next_task_field(update: Update, context: ContextTypes.DEFAULT_TYPE, field: str):
    """Задать следующий вопрос."""
    hint = field_hints.get(field, field)
    await update.message.reply_text(
        f"{hint}\n\nНажмите 'Пропустить' чтобы пропустить.",
        parse_mode="HTML"
    )


async def finish_task_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение создания задачи."""
    task_data = context.user_data.get("task_data", {})
    lead_id = context.user_data.get("task_lead_id", "")
    lead_info = context.user_data.get("lead_info", {})
    user = update.message.from_user
    responsible = user.first_name or user.username or "Менеджер"
    
    # AI генерирует задачу
    try:
        ai_result = await ai_service.generate_task(
            task_data.get("context", ""),
            lead_info
        )
        task_data["title"] = ai_result.title
        task_data["priority"] = ai_result.priority
        task_data["status"] = ai_result.status
    except Exception as e:
        print(f"AI task error: {e}")
        task_data["title"] = "Связаться с клиентом"
        task_data["priority"] = "Средний"
        task_data["status"] = "Новая"
    
    # Запись в Google Sheets
    try:
        clinic = lead_info.get("Название клиники", "Клиника")
        task_id = sheets_service.add_task(lead_id, clinic, task_data, responsible)
        
        priority_emoji = {
            "Высокий": "🔴",
            "Средний": "🟡",
            "Низкий": "🟢",
        }.get(task_data.get("priority", "Средний"), "🟡")
        
        response = f"""✅ <b>Задача создана!</b>

🏥 Клиника: {clinic}
📝 Задача: {task_data.get('title', '-')}
⚡ Приоритет: {priority_emoji} {task_data.get('priority', 'Средний')}

📅 Дедлайн: {task_data.get('deadline', '-')}
💬 Комментарий: {task_data.get('comment', '-')}

🆔 ID задачи: {task_id}"""
        
        await update.message.reply_text(response, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    
    context.user_data.clear()
    from bot.handlers.menu import show_main_menu
    await show_main_menu(update, context)