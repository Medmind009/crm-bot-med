# CRM Бот для медицинских продаж

Telegram-бот для приёма отчётов менеджеров с AI-парсингом и записью в Google Таблицы.

## 🚀 Быстрый старт (MVP)

### Вариант 1: Render.com (Бесплатно)

1. **Создай аккаунт** на [render.com](https://render.com)

2. **Создай Web Service**:
   - New → Web Service
   - Подключи GitHub репозиторий или загрузи ZIP

3. **Настройки**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m bot`
   - Environment Variables добавь:
     ```
     TELEGRAM_TOKEN=твой_токен
     OPENROUTER_API_KEY=твой_ключ
     GOOGLE_SPREADSHEET_ID=твой_id_таблицы
     ```

4. **Загрузи google-credentials.json** в Settings → Environment Variables

---

### Вариант 2: Railway (Бесплатно)

1. **Создай аккаунт** на [railway.app](https://railway.app)

2. **Создай проект**:
   - New Project → Deploy from GitHub repo
   - Или: New Project → Empty Project → GitHub repo

3. **Настройки**:
   - Добавь переменные окружения (Variables)
   - Загрузи `google-credentials.json` как переменную или через File

4. **Deploy** — нажми кнопку Deploy

---

### Вариант 3: VPS (от 100₽/мес)

```bash
# Подключись к серверу
ssh user@your-server

# Установи Python и зависимости
sudo apt update
sudo apt install python3 python3-pip git
git clone https://github.com/твой_репозиторий.git
cd твой_проект
pip install -r requirements.txt

# Создай .env файл
nano .env
# Вставь переменные окружения

# Запусти бота (через screen или systemd)
nohup python -m bot > bot.log 2>&1 &
```

---

## 📋 Подготовка файлов для деплоя

### Обязательные файлы:
```
/workspace/project/
├── bot/                    # Код бота
│   ├── __init__.py
│   ├── __main__.py
│   ├── ai_service.py
│   ├── sheets_service.py
│   ├── types.py
│   └── handlers/
├── requirements.txt        # Зависимости
├── google-credentials.json # Ключи Google (не в git!)
├── Procfile               # Для Render
└── .env                   # Переменные (не в git!)
```

### Файлы для GitHub:
```
.gitignore:
.env
google-credentials.json
*.log
__pycache__/
```

---

## 🔧 Настройка Google Sheets

1. Создай проект в [Google Cloud Console](https://console.cloud.google.com)
2. Включи Google Sheets API и Google Drive API
3. Создай Service Account
4. Скачай `credentials.json`
5. Открой доступ к таблице: Поделиться → Email сервисного аккаунта

---

## 📝 Переменные окружения

| Переменная | Обязательно | Описание |
|------------|-------------|----------|
| TELEGRAM_TOKEN | ✅ | Токен от @BotFather |
| OPENROUTER_API_KEY | ✅ | Ключ от openrouter.ai |
| GOOGLE_SPREADSHEET_ID | ✅ | ID таблицы из URL |
| GOOGLE_CREDENTIALS | Опционально | google-credentials.json |

---

## 🤖 Команды бота

- `/start` — Главное меню
- `/menu` — Показать меню
- `/help` — Справка

---

## 📂 Структура таблицы

Ожидаемые листы в Google Таблице:
- **Лиды** — клиники
- **Касания** — взаимодействия
- **Задачи** — задачи менеджеров

---

## 🐛 Troubleshooting

**Бот не запускается:**
- Проверь логи: `tail -f bot.log`
- Проверь токен бота
- Проверь API ключи

**Ошибка Google Sheets:**
- Проверь что credentials.json на сервере
- Проверь доступ сервисного аккаунта к таблице

**Конфликт polling:**
- Убедись что запущен только один экземпляр бота