
import os
from telegram import Bot
from telegram.ext import Updater, CommandHandler

def start(update, context):
    update.message.reply_text("👋 Бот работает. Выбор языка скоро появится!")

def main():
    token = os.getenv("TOKEN")
    if not token:
        print("❌ TOKEN переменная окружения не установлена!")
        return

    try:
        bot = Bot(token)
        me = bot.get_me()
        print(f"✅ Подключено к Telegram как: @{me.username} (ID: {me.id})")
    except Exception as e:
        print(f"❌ Ошибка при подключении к Telegram: {e}")
        return

    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))

    print("🚀 Запуск polling...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
