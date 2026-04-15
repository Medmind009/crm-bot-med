"""
AI-сервис для парсинга отчетов.
"""
import json
import logging
from typing import Dict, Any, Optional
import httpx
from bot_logic.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
    normalize_status,
    normalize_priority
)
from config.settings import config

logger = logging.getLogger(__name__)


class AIService:
    """Сервис для работы с AI."""
    
    def __init__(self):
        self.api_key = config.openrouter_api_key or config.google_ai_api_key
        self.model = config.openrouter_model
    
    async def parse_report(
        self,
        chat_id: str,
        username: str,
        name: str,
        report_text: str
    ) -> Dict[str, Any]:
        """Парсить отчет о продаже."""
        user_prompt = build_user_prompt(chat_id, username, name, report_text)
        
        # Выбираем API
        if config.openrouter_api_key:
            return await self._parse_with_openrouter(user_prompt)
        elif config.google_ai_api_key:
            return await self._parse_with_google_ai(user_prompt)
        else:
            raise ValueError("Не настроен API ключ для AI")
    
    async def _parse_with_openrouter(self, user_prompt: str) -> Dict[str, Any]:
        """Парсить через OpenRouter API."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://crm-bot.example.com",
            "X-Title": "CRM Sales Bot"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            return self._parse_json_response(content)
    
    async def _parse_with_google_ai(self, user_prompt: str) -> Dict[str, Any]:
        """Парсить через Google AI API."""
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Формируем содержимое
        contents = [
            {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
            {"role": "model", "parts": [{"text": "Ок, понял. Жду текст отчета."}]},
            {"role": "user", "parts": [{"text": user_prompt}]}
        ]
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "text/plain"
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{url}?key={self.api_key}",
                json=payload,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            
            return self._parse_json_response(content)
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Парсить JSON из ответа AI."""
        # Убираем markdown если есть
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Парсим JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {content[:200]}")
            raise ValueError(f"Invalid JSON from AI: {e}")
        
        # Нормализуем статусы
        if "lead_status" in data:
            data["lead_status"] = normalize_status(data["lead_status"])
        if "task_priority" in data:
            data["task_priority"] = normalize_priority(data["task_priority"])
        
        return data


# Глобальный сервис
ai_service = AIService()