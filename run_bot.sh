#!/bin/bash
# CRM Бот - Python Telegram Bot
cd "$(dirname "$0")"

# Убедимся что python-telegram-bot установлен
pip install python-telegram-bot -q 2>/dev/null

# Запускаем бота
cd /workspace/project
python -m bot