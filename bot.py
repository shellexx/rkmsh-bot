
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    CallbackQueryHandler, ConversationHandler, CallbackContext
)
from datetime import datetime
import pytz
import re

# === НАСТРОЙКИ ===

TOKEN = os.getenv("TOKEN")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

MAIL_SERVER = "smtp.mail.ru"
MAIL_PORT = 587
LOGO_URL = "https://pkm-school.ru/wp-content/uploads/2025/04/logoschool-copy112.png"

moscow_tz = pytz.timezone("Europe/Moscow")

NAME, DOB, CONTACT, CLASS, MESSAGE = range(5)

def show_main_menu(chat_id, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📨 Подать заявку", callback_data='apply')],
        [InlineKeyboardButton("📢 Telegram-канал", url='https://t.me/RCISchool')],
        [InlineKeyboardButton("📘 ВКонтакте", url='https://vk.com/rcischool')],
        [InlineKeyboardButton("🌐 Перейти на сайт", url='https://pkm-school.ru')],
        [InlineKeyboardButton("📱 WhatsApp", url='https://wa.me/79267035536')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_photo(
        chat_id=chat_id,
        photo=LOGO_URL,
        caption="""
🤖 *Вас приветствует Бот РКМШ!*

Здесь вы можете:
• Подать заявку на поступление 📩
• Узнать, как проходят занятия 📚
• Найти полезные контакты ☎️

📥 Готовы начать? Жмите кнопку ниже!
"""
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def start(update: Update, context: CallbackContext):
    show_main_menu(update.message.chat_id, context)

def handle_callback(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.message.reply_text("📋 Введите *ФИО* ребёнка:", parse_mode="Markdown")
    return NAME

def name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text("🗓 Укажите *дату рождения* (ДД.ММ.ГГГГ):", parse_mode="Markdown")
    return DOB

def dob(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data['dob'] = datetime.strptime(update.message.text, "%d.%m.%Y")
        update.message.reply_text("📞 Напишите *контактный номер телефона* в формате +7XXXXXXXXXX:", parse_mode="Markdown")
        return CONTACT
    except ValueError:
        update.message.reply_text("⚠️ Неверный формат даты. Повторите (ДД.ММ.ГГГГ):")
        return DOB

def contact(update: Update, context: CallbackContext) -> int:
    phone = update.message.text
    if not re.match(r"^\+7\d{10}$", phone):
        update.message.reply_text("⚠️ Пожалуйста, введите номер в формате +7XXXXXXXXXX.")
        return CONTACT
    context.user_data['contact'] = phone
    update.message.reply_text("🏫 В какой *класс* хотите поступить?", parse_mode="Markdown")
    return CLASS

def school_class(update: Update, context: CallbackContext) -> int:
    context.user_data['class'] = update.message.text
    update.message.reply_text("✍️ Есть ли у вас *дополнительные вопросы*?", parse_mode="Markdown")
    return MESSAGE

def message(update: Update, context: CallbackContext) -> int:
    context.user_data['message'] = update.message.text
    data = context.user_data

    email_body = f"""
    🎓 ЗАЯВКА В РКМШ

    👤 ФИО: {data['name']}
    📆 Дата рождения: {data['dob'].strftime('%d.%m.%Y')}
    📞 Телефон: {data['contact']}
    🏫 Класс: {data['class']}
    📝 Дополнительно: {data['message']}
    """

    send_email(email_body)
    update.message.reply_text("✅ Заявка отправлена! Возвращаемся в главное меню...")
    show_main_menu(update.message.chat_id, context)
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("❌ Заявка отменена.")
    show_main_menu(update.message.chat_id, context)
    return ConversationHandler.END

def send_email(content: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"РКМШ | Новая заявка — {datetime.now(moscow_tz).strftime('%d.%m.%Y %H:%M')}"
        msg.attach(MIMEText(content, 'plain'))
        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("📧 Заявка отправлена.")
    except Exception as e:
        print(f"❌ Ошибка при отправке письма: {e}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_callback, pattern="^apply$")],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, name)],
            DOB: [MessageHandler(Filters.text & ~Filters.command, dob)],
            CONTACT: [MessageHandler(Filters.text & ~Filters.command, contact)],
            CLASS: [MessageHandler(Filters.text & ~Filters.command, school_class)],
            MESSAGE: [MessageHandler(Filters.text & ~Filters.command, message)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
