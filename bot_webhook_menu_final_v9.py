
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import os, smtplib
from email.mime.text import MIMEText

TOKEN = os.getenv("TOKEN")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "shellexx")

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)

LOGO_URL = "https://pkm-school.ru/wp-content/uploads/2025/04/logoschool-copy112.png"
USER_STATE = {}

TEXT = {
    "start": {
        "multi": "🤖 Вас приветствует Бот Русско-китайской международной школы!\n🤖 欢迎来到俄罗斯-中国国际学校！\n\nВыберите язык / 请选择语言:"
    },
    "ru": {
        "menu": "📋 Главное меню:\n\nВыберите действие:",
        "apply": "📋 Введите ФИО ребёнка:",
        "age": "👶 Выберите возраст ребёнка:",
        "class": "🏫 Выберите класс:",
        "phone": "📱 Введите номер телефона:",
        "question": "📝 У вас есть вопросы?",
        "thank": "✅ Спасибо! Ваша заявка отправлена. Мы скоро свяжемся с вами.",
        "button_apply": "📨 Подать заявку на консультацию"
    },
    "zh": {
        "menu": "📋 主菜单：\n\n请选择操作：",
        "apply": "📋 请输入孩子的姓名：",
        "age": "👶 请选择孩子的年龄：",
        "class": "🏫 请选择年级：",
        "phone": "📱 请输入联系电话：",
        "question": "📝 您还有其他问题吗？",
        "thank": "✅ 感谢您的申请！我们会尽快与您联系。",
        "button_apply": "📨 申请咨询"
    }
}

def get_lang(chat_id):
    return USER_STATE.get(chat_id, {}).get("lang", "ru")

def start(update, context):
    chat_id = update.effective_chat.id
    USER_STATE[chat_id] = {}
    keyboard = [[
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")
    ]]
    bot.send_photo(
        chat_id=chat_id,
        photo=LOGO_URL,
        caption=TEXT["start"]["multi"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_main_menu(chat_id):
    lang = get_lang(chat_id)
    keyboard = [
        [InlineKeyboardButton(TEXT[lang]["button_apply"], callback_data="apply")],
        [
            InlineKeyboardButton("🌐 Сайт", url="https://pkm-school.ru"),
            InlineKeyboardButton("📢 Канал", url="https://t.me/RCISchool")
        ],
        [
            InlineKeyboardButton("💬 WhatsApp", url="https://wa.me/79267035536"),
            InlineKeyboardButton("📘 ВКонтакте", url="https://vk.com/rcischool")
        ]
    ]
    bot.send_photo(
        chat_id=chat_id,
        photo=LOGO_URL,
        caption=TEXT[lang]["menu"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_language(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    lang = query.data.split("_")[1]
    USER_STATE[chat_id]["lang"] = lang
    show_main_menu(chat_id)

def handle_apply(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    USER_STATE[chat_id]["step"] = "name"
    lang = get_lang(chat_id)
    context.bot.send_message(chat_id=chat_id, text=TEXT[lang]["apply"])

def message_handler(update, context):
    chat_id = update.message.chat_id
    msg = update.message.text
    user = USER_STATE.get(chat_id, {})
    lang = get_lang(chat_id)
    step = user.get("step")

    if step == "name":
        user["name"] = msg
        user["step"] = "age"
        keyboard = [
            [InlineKeyboardButton(str(i), callback_data=f"age_{i}") for i in range(5, 10)],
            [InlineKeyboardButton(str(i), callback_data=f"age_{i}") for i in range(10, 15)],
            [InlineKeyboardButton(str(i), callback_data=f"age_{i}") for i in range(15, 18)],
        ]
        context.bot.send_message(chat_id=chat_id, text=TEXT[lang]["age"], reply_markup=InlineKeyboardMarkup(keyboard))
    elif step == "phone":
        user["phone"] = msg
        user["step"] = "question"
        context.bot.send_message(chat_id=chat_id, text=TEXT[lang]["question"])
    elif step == "question":
        user["question"] = msg
        send_email(update.effective_user.username, user)
        context.bot.send_message(chat_id=chat_id, text=TEXT[lang]["thank"])
        show_main_menu(chat_id)

def handle_age(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    age = query.data.split("_")[1]
    USER_STATE[chat_id]["age"] = age
    USER_STATE[chat_id]["step"] = "class"
    lang = get_lang(chat_id)
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"class_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"class_{i}") for i in range(6, 12)]
    ]
    context.bot.send_message(chat_id=chat_id, text=TEXT[lang]["class"], reply_markup=InlineKeyboardMarkup(keyboard))

def handle_class(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    class_val = query.data.split("_")[1]
    USER_STATE[chat_id]["class"] = class_val
    USER_STATE[chat_id]["step"] = "phone"
    lang = get_lang(chat_id)
    context.bot.send_message(chat_id=chat_id, text=TEXT[lang]["phone"])

def send_email(username, data):
    body = f"""Заявка из Telegram:
Имя: {data.get("name")}
Возраст: {data.get("age")}
Класс: {data.get("class")}
Телефон: {data.get("phone")}
Вопрос: {data.get("question")}
Пользователь: @{username}
"""
    try:
        msg = MIMEText(body)
        msg["Subject"] = "Новая заявка на консультацию"
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL

        with smtplib.SMTP("smtp.mail.ru", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

        bot.send_message(chat_id=f"@{ADMIN_USERNAME}", text=body)
    except Exception as e:
        print("Ошибка при отправке письма:", e)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(handle_language, pattern="^lang_"))
dispatcher.add_handler(CallbackQueryHandler(handle_apply, pattern="^apply$"))
dispatcher.add_handler(CallbackQueryHandler(handle_age, pattern="^age_"))
dispatcher.add_handler(CallbackQueryHandler(handle_class, pattern="^class_"))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

@app.route("/")
def index():
    return "Bot is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

bot.delete_webhook()
bot.set_webhook("https://rkmsh-bot.onrender.com/webhook")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
