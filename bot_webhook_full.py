
import os
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from datetime import datetime, timedelta
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TOKEN = os.getenv("TOKEN")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "shellexx")

LOGO_URL = "https://pkm-school.ru/wp-content/uploads/2025/04/logoschool-copy112.png"
moscow_tz = pytz.timezone("Europe/Moscow")

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)

USERS = {}

LANGUAGES = {
    "ru": {
        "start": "Выберите язык / 请选择语言:",
        "main_menu": "👋 Добро пожаловать в РКМШ!",
        "form": "📋 Введите ФИО ребёнка:",
        "age": "👶 Выберите возраст ребёнка:",
        "class": "🏫 В какой класс хотите поступить?",
        "phone": "📱 Введите контактный номер телефона:",
        "extra": "📝 Есть ли у вас дополнительные вопросы?",
        "done": "✅ Заявка отправлена!",
        "excursion": "📅 Выберите удобный четверг для экскурсии:",
        "thank": "Спасибо! Мы свяжемся с вами.",
        "unknown": "Неизвестная команда."
    },
    "zh": {
        "start": "请选择语言 / Выберите язык:",
        "main_menu": "👋 欢迎来到俄罗斯-中国国际学校！",
        "form": "📋 请输入孩子的姓名：",
        "age": "👶 请选择孩子的年龄：",
        "class": "🏫 您想报读哪个年级？",
        "phone": "📱 输入联系电话：",
        "extra": "📝 还有其他问题吗？",
        "done": "✅ 报名申请已提交！",
        "excursion": "📅 请选择一个星期四参加参观：",
        "thank": "谢谢！我们会尽快联系您。",
        "unknown": "未知命令。"
    }
}

def t(context, key):
    lang = USERS.get(context._chat_id_and_data[0], {}).get("lang", "ru")
    return LANGUAGES.get(lang, LANGUAGES["ru"]).get(key, key)

def start(update, context):
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")]
    ]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=LANGUAGES["ru"]["start"],
                             reply_markup=InlineKeyboardMarkup(keyboard))

def handle_language(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    lang_code = query.data.split("_")[1]
    USERS[chat_id] = {"lang": lang_code, "step": "form"}
    context.bot.send_message(chat_id=chat_id, text=t(context, "form"))

def message_handler(update, context):
    chat_id = update.message.chat_id
    user = USERS.get(chat_id, {})
    msg = update.message.text
    step = user.get("step")

    if step == "form":
        user["name"] = msg
        user["step"] = "age"
        keyboard = [[InlineKeyboardButton(str(i), callback_data=f"age_{i}")] for i in range(5, 19)]
        context.bot.send_message(chat_id=chat_id, text=t(context, "age"),
                                 reply_markup=InlineKeyboardMarkup(keyboard))
    elif step == "class":
        user["class"] = msg
        user["step"] = "phone"
        context.bot.send_message(chat_id=chat_id, text=t(context, "phone"))
    elif step == "phone":
        user["phone"] = msg
        user["step"] = "extra"
        context.bot.send_message(chat_id=chat_id, text=t(context, "extra"))
    elif step == "extra":
        user["extra"] = msg
        user["step"] = "done"
        USERS[chat_id] = user
        send_email(context, update.effective_user.username or "неизвестный", user)
        context.bot.send_message(chat_id=chat_id, text=t(context, "done"))
        context.bot.send_message(chat_id=chat_id, text=t(context, "thank"))
    elif step == "excursion":
        user["excursion_date"] = msg
        context.bot.send_message(chat_id=chat_id, text=t(context, "thank"))
    else:
        context.bot.send_message(chat_id=chat_id, text=t(context, "unknown"))

def handle_age(update, context):
    query = update.callback_query
    age = query.data.split("_")[1]
    chat_id = query.message.chat_id
    USERS[chat_id]["age"] = age
    USERS[chat_id]["step"] = "class"
    query.answer()
    context.bot.send_message(chat_id=chat_id, text=t(context, "class"))

def start_excursion(update, context):
    chat_id = update.message.chat_id
    USERS[chat_id] = {"step": "excursion", "lang": "ru"}
    today = datetime.now(moscow_tz)
    thursdays = []
    for i in range(1, 30):
        day = today + timedelta(days=i)
        if day.weekday() == 3:
            thursdays.append(day.strftime("%d.%m.%Y"))
    keyboard = [[InlineKeyboardButton(d, callback_data=f"exc_{d}")] for d in thursdays[:5]]
    context.bot.send_message(chat_id=chat_id, text=t(context, "excursion"),
                             reply_markup=InlineKeyboardMarkup(keyboard))

def handle_excursion_date(update, context):
    query = update.callback_query
    date = query.data.split("_")[1]
    chat_id = query.message.chat_id
    USERS[chat_id]["excursion_date"] = date
    USERS[chat_id]["step"] = "done"
    query.answer()
    context.bot.send_message(chat_id=chat_id, text=t(context, "thank"))

def send_email(context, username, data):
    body = f"""📥 Новая заявка из Telegram:
Имя: {data.get('name')}
Возраст: {data.get('age')}
Класс: {data.get('class')}
Телефон: {data.get('phone')}
Вопрос: {data.get('extra')}
Пользователь: @{username}
"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"Заявка в РКМШ от @{username}"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP("smtp.mail.ru", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()

        bot.send_message(chat_id=f"@{ADMIN_USERNAME}", text=body)
    except Exception as e:
        print("Ошибка отправки письма:", e)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("excursion", start_excursion))
dispatcher.add_handler(CallbackQueryHandler(handle_language, pattern="^lang_"))
dispatcher.add_handler(CallbackQueryHandler(handle_age, pattern="^age_"))
dispatcher.add_handler(CallbackQueryHandler(handle_excursion_date, pattern="^exc_"))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

@app.route('/')
def index():
    return "👋 RKMSh Webhook Бот активен!"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Установка Webhook
bot.delete_webhook()
bot.set_webhook("https://rkmsh-bot.onrender.com/webhook")
print("✅ Webhook установлен: https://rkmsh-bot.onrender.com/webhook")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
