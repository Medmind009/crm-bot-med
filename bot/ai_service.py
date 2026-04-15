"""
AI сервис для CRM-бота.
Единый источник для определения статусов, задач, шагов.
"""
import json
import logging
import httpx
from typing import Optional
from bot.types import (
    LEAD_STATUS_MAP, TASK_PRIORITY_MAP, 
    LeadStatus, TaskPriority, TaskStatus,
    AILeadResult, AITaskResult, AIContactResult
)

logger = logging.getLogger(__name__)

# Конфиг (из переменных окружения)
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "google/gemini-2.0-flash-001"


class AIService:
    """Единый AI сервис для CRM."""
    
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.model = OPENROUTER_MODEL
    
    async def determine_lead_status(self, text: str, context: dict) -> AILeadResult:
        """Определить статус лида на основе текста и контекста."""
        prompt = f"""Проанализируй отчёт менеджера и определи статус лида.

Контекст:
- Клиника: {context.get('clinic_name', 'неизвестно')}
- Контакт: {context.get('contact_name', 'неизвестно')}
- Реакция клиента: {context.get('reaction', 'неизвестно')}
- Что передали: {context.get('sent_materials', 'неизвестно')}

Отчёт менеджера:
{text}

Верни JSON:
{{
  "status": "статус из списка: Новый, Интерес, Переговоры, Ожидание ответа, Предложено, Неактуально, Отказ, Сделка",
  "next_step": "следующий логический шаг",
  "next_step_date": "YYYY-MM-DD или пусто",
  "confidence": 0.0-1.0
}}

Верни только JSON."""
        
        try:
            result = await self._call_ai(prompt)
            return AILeadResult(
                status=result.get("status", "Новый"),
                next_step=result.get("next_step", ""),
                next_step_date=result.get("next_step_date", ""),
                confidence=result.get("confidence", 0.5)
            )
        except Exception as e:
            logger.error(f"AI lead status error: {e}")
            return AILeadResult(status="Новый")
    
    async def generate_task(self, context: str, lead_info: dict) -> AITaskResult:
        """Сгенерировать задачу на основе контекста."""
        prompt = f"""На основе контекста сформулируй задачу для менеджера.

Информация о лиде:
- Клиника: {lead_info.get('clinic_name', '')}
- Контакт: {lead_info.get('contact_name', '')}
- Статус: {lead_info.get('status', '')}

Контекст от менеджера:
{context}

Верни JSON:
{{
  "title": "формулировка задачи",
  "priority": "Низкий, Средний или Высокий",
  "status": "Новая"
}}

Верни только JSON."""
        
        try:
            result = await self._call_ai(prompt)
            return AITaskResult(
                title=result.get("title", "Связаться с клиентом"),
                priority=result.get("priority", "Средний"),
                status=result.get("status", "Новая")
            )
        except Exception as e:
            logger.error(f"AI task generation error: {e}")
            return AITaskResult(title="Связаться с клиентом")
    
    async def determine_contact_next_step(self, contact_text: str, lead_info: dict) -> AIContactResult:
        """Определить следующий шаг после касания."""
        prompt = f"""Проанализируй касание и определи следующий шаг.

Лид:
- Клиника: {lead_info.get('clinic_name', '')}
- Текущий статус: {lead_info.get('status', '')}

Касание:
{contact_text}

Верни JSON:
{{
  "next_step": "следующий шаг",
  "result": "итог взаимодействия кратко"
}}

Верни только JSON."""
        
        try:
            result = await self._call_ai(prompt)
            return AIContactResult(
                next_step=result.get("next_step", ""),
                result=result.get("result", "")
            )
        except Exception as e:
            logger.error(f"AI contact step error: {e}")
            return AIContactResult()
    
    async def parse_lead_free_text(self, text: str, user_name: str) -> dict:
        """Парсить свободный текст в данные лида (fallback)."""
        prompt = f"""Извлеки данные о лиде из текста.

Текст от менеджера:
{text}

Верни JSON со всеми известными полями:
{{
  "clinic_name": "",
  "contact_name": "",
  "position": "",
  "phone": "",
  "telegram": "",
  "channel": "Telegram",
  "sent_materials": "",
  "reaction": "",
  "comment": "",
  "responsible": "{user_name}"
}}

Верни только JSON."""
        
        try:
            result = await self._call_ai(prompt)
            return result
        except Exception as e:
            logger.error(f"AI parse error: {e}")
            return {"clinic_name": text[:50], "responsible": user_name}
    
    async def _call_ai(self, prompt: str) -> dict:
        """Вызов OpenRouter API."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Ты — CRM AI-ассистент. Отвечай только JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)


# Глобальный сервис
ai_service = AIService()