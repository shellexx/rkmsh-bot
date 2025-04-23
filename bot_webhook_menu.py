
import os
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler
import logging

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)

app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)

LOGO_URL = "https://pkm-school.ru/wp-content/uploads/2025/04/logoschool-copy112.png"
LANGUAGES = {"ru": "🇷🇺 Русский", "zh": "🇨🇳 中文"}
USER_LANG = {}

def start(update, context):
    chat_id = update.effective_chat.id
    USER_LANG[chat_id] = "ru"  # default
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")
        ]
    ]
    bot.send_photo(
        chat_id=chat_id,
        photo=LOGO_URL,
        caption="""🤖 Вас приветствует Бот Русско-китайской международной школы!

Выберите язык:""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_language(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    lang_code = query.data.split("_")[1]
    USER_LANG[chat_id] = lang_code

    text = {
        "ru": "📋 Главное меню:\n\nВыберите действие:",
        "zh": "📋 主菜单：\n\n请选择操作："
    }[lang_code]

    keyboard = [
        [InlineKeyboardButton("📨 Подать заявку", callback_data="apply")],
        [InlineKeyboardButton("📅 Экскурсия", callback_data="excursion")],
        [
            InlineKeyboardButton("📢 Канал", url="https://t.me/RCISchool"),
            InlineKeyboardButton("📘 ВКонтакте", url="https://vk.com/rcischool")
        ],
        [InlineKeyboardButton("🌐 Сайт", url="https://pkm-school.ru")]
    ]

    bot.send_photo(
        chat_id=chat_id,
        photo=LOGO_URL,
        caption=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(handle_language, pattern="^lang_"))

@app.route("/")
def index():
    return "RKMSh Bot Webhook is active."

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

bot.delete_webhook()
bot.set_webhook("https://rkmsh-bot.onrender.com/webhook")
print("✅ Webhook установлен с приветствием и меню.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
