
# 🎓 RKM School Telegram Bot

Многоязычный Telegram-бот для частной русско-китайской международной школы **РКМШ**.

## 🧠 Возможности

- 🌐 Выбор языка (русский 🇷🇺 и китайский 🇨🇳)
- 🧒 Подача заявки на поступление
- 📊 Уведомления администратору Telegram (@shellexx)
- 🗓 Выбор возраста (5–18 лет)
- 🏫 Классы от 1 до 11
- 📅 Запись на экскурсии по четвергам
- 📬 Отправка заявки на почту
- 🖼 Главное меню с кнопками: Telegram, ВКонтакте, WhatsApp, сайт

## 🚀 Развёртывание на Render

1. Создайте репозиторий на GitHub
2. Загрузите `bot_lang.py`, `requirements.txt`, `render.yaml`
3. На Render:
   - Connect GitHub → Выберите репозиторий
   - Build command: `pip install -r requirements.txt`
   - Start command: `python bot_lang.py`
4. Установите переменные окружения:

```
TOKEN=YOUR_BOT_TOKEN
SENDER_EMAIL=sender-school@mail.ru
SENDER_PASSWORD=SMTP_PASSWORD
RECEIVER_EMAIL=pkms@pkm-school.ru
ADMIN_USERNAME=shellexx
```

## 🤝 Контакты

Сделано с ❤️ для РКМШ.
