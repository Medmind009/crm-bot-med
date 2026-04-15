"""
Тестовый модуль для проверки парсинга AI.
"""
import asyncio
import json
from services.ai_service import ai_service
from bot_logic.prompts import build_user_prompt


# Тестовый отчет из Make.com
TEST_REPORT = """Клиника: Стоматология Дент-Люкс. Общался сегодня с главным врачом по имени Мария Ивановна. ЛПР: да, она принимает решения. Телефон для связи: +7 999 123-45-67. Реакция отличная, проявлен большой интерес к оборудованию всех стран. Передал им наш новый каталог и прайс-лист. Договорились, что следующий шаг — это презентация в зуме. Дату следующего касания перенесем на 15 апреля. Комментарий: очень перспективный клиент, нужно дожимать."""


async def test_ai_parsing():
    """Тест парсинга отчета."""
    print("Testing AI parsing...")
    print(f"Report: {TEST_REPORT[:100]}...")
    print()
    
    try:
        result = await ai_service.parse_report(
            chat_id="322305352",
            username="Denis_nsk001",
            name="Денис",
            report_text=TEST_REPORT
        )
        
        print("Parsed result:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_ai_parsing())