import logging
import sqlite3
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد اللوق
logging.basicConfig(level=logging.INFO)

# بيانات البوت
BOT_TOKEN = "8196646590:AAEMri3y4yNtZWGdtzqH7ftBfMhYf5koxSs"
OWNER_ID = 5193446345
DB_FILE = "messages.db"

# إنشاء قاعدة البيانات
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER,
            chat_id INTEGER,
            content TEXT,
            message_type TEXT,
            UNIQUE(message_id, chat_id)
        )
    ''')
    conn.commit()
    conn.close()

# حفظ الرسائل
def save_message(message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if message.text:
        content = message.text
        msg_type = "text"
    elif message.photo:
        content = message.photo[-1].file_id
        msg_type = "photo"
    elif message.video:
        content = message.video.file_id
        msg_type = "video"
    elif message.voice:
        content = message.voice.file_id
        msg_type = "voice"
    else:
        content = "[نوع غير مدعوم]"
        msg_type = "other"

    c.execute("""
        INSERT OR REPLACE INTO messages (message_id, chat_id, content, message_type)
        VALUES (?, ?, ?, ?)
    """, (message.message_id, message.chat.id, content, msg_type))

    conn.commit()
    conn.close()

# معالجة الرسائل الجديدة
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        save_message(update.message)

# معالجة التعديلات
async def handle_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    edited = update.edited_message
    if not edited:
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT content FROM messages WHERE message_id=? AND chat_id=?", (edited.message_id, edited.chat.id))
    result = c.fetchone()
    conn.close()

    if result:
        old_content = result[0]
        new_content = edited.text or "[غير نصي]"
        message = f"✏ تم تعديل رسالة:\n\n*القديم:* {old_content}\n*الجديد:* {new_content}"
        await context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode="Markdown")
        save_message(edited)

# أمر البدء
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت شغال ويقوم بحفظ الرسائل الخاصة.")

# تشغيل البوت بـ webhook
if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, handle_edit))

    print("🤖 البوت يعمل الآن...")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://marwanbot.onrender.com/{BOT_TOKEN}"
    )
