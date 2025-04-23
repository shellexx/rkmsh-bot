
import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import logging

# Настройка логов
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)

# Flask-приложение
app = Flask(__name__)

@app.route('/')
def index():
    return '👋 RKMSh Bot работает на Webhook!'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

# Команда /start
def start(update, context):
    update.message.reply_text("👋 Добро пожаловать! Я работаю через Webhook 🚀")

# Команда /ping
def ping(update, context):
    update.message.reply_text("✅ Webhook бот на связи!")

# Настройка dispatcher
from telegram.ext import Dispatcher
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("ping", ping))

# Установка Webhook
bot.delete_webhook()
bot.set_webhook(f"https://rkmsh-bot.onrender.com/webhook")
print("✅ Webhook установлен:", f"https://rkmsh-bot.onrender.com/webhook")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
