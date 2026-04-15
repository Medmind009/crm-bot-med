# 🚀 Подключение Google Таблицы к CRM-боту

## Шаг 1: Создать Service Account

1. Открой **Google Cloud Console**: https://console.cloud.google.com/

2. Создай новый проект:
   - Название: `crm-bot` (или любое)

3. Включи API:
   - APIs & Services → Library
   - Найди и включи: **Google Sheets API**
   - Найди и включи: **Google Drive API**

4. Создай credentials:
   - APIs & Services → Credentials
   - Create Credentials → **Service Account**
   - Имя: `crm-bot`
   - Описание: CRM Bot for sales
   - Нажми Create → Continue → Done

5. Создай ключ:
   - Нажми на созданный service account (email вида `crm-bot@...iam.gserviceaccount.com`)
   - Keys → Add Key → Create new key
   - Тип: **JSON**
   - Скачай файл

---

## Шаг 2: Поделиться таблицей

1. Открой твою Google Таблицу:
   https://docs.google.com/spreadsheets/d/1b7V6KHEPxcpthohDORDgK4X33OwcVxjcEdz_PSUOHbY

2. Нажми **Поделиться** (кнопка вверху справа)

3. Введи email service account:
   ```
   crm-bot@НАЗВАНИЕ_ПРОЕКТА.iam.gserviceaccount.com
   ```
   (-email из скачанного JSON файла)

4. Нажми **Отправить**

---

## Шаг 3: Настроить бота

1. Переименуй скачанный файл в `google-credentials.json`

2. Положи в папку `/workspace/project/`

3. Готово! Бот будет писать в таблицу.

---

## 📋 Структура таблицы

Убедись, что в таблице есть листы:

| Лист | Колонки |
|------|---------|
| **Лиды** | Дата, Клиника, Контакт, Должность, ЛПР, Телефон, Реакция, Шаг, Дата, Статус, Ответственный, Комментарий |
| **Касания** | Дата, Кто, Формат, Реакция, Материалы, Вопросы, Ответы, Итог, Шаг, Клиника |
| **Задачи** | Клиника, Задача, Дата, Дедлайн, Ответственный, Статус, Приоритет |

---

## ⚠️ Важно

Service account должен иметь права на редактирование таблицы! После шага 2 проверь, что таблица открывается сервис-аккаунтом.