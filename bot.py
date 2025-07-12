import sqlite3
import io
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, ContextTypes
)

# إعدادات البوت
TOKEN = "8196646590:AAEMri3y4yNtZWGdtzqH7ftBfMhYf5koxSs"
OWNER_ID = 5193446345
DB_PATH = "messages.db"

# تفعيل سجل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# إنشاء قاعدة البيانات
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            chat_id INTEGER,
            message_id INTEGER,
            user_id INTEGER,
            message_type TEXT,
            text TEXT,
            file_id TEXT,
            date INTEGER,
            PRIMARY KEY (chat_id, message_id)
        )
    """)
    conn.commit()
    conn.close()

# حفظ الرسائل
def save_message_db(message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    chat_id = message.chat.id
    message_id = message.message_id
    user_id = message.from_user.id if message.from_user else 0
    date = int(message.date.timestamp())

    if message.text:
        message_type = "text"; text = message.text; file_id = None
    elif message.photo:
        message_type = "photo"; text = None; file_id = message.photo[-1].file_id
    elif message.video:
        message_type = "video"; text = None; file_id = message.video.file_id
    elif message.voice:
        message_type = "voice"; text = None; file_id = message.voice.file_id
    else:
        message_type = "other"; text = None; file_id = None

    c.execute("""
        INSERT OR REPLACE INTO messages
        (chat_id, message_id, user_id, message_type, text, file_id, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (chat_id, message_id, user_id, message_type, text, file_id, date))
    conn.commit()
    conn.close()

# استرجاع الرسالة
def get_message_db(chat_id, message_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT message_type, text, file_id FROM messages WHERE chat_id=? AND message_id=?", (chat_id, message_id))
    row = c.fetchone()
    conn.close()
    return row

async def send_saved_message(chat_id, message_id, context: ContextTypes.DEFAULT_TYPE):
    msg_data = get_message_db(chat_id, message_id)
    if not msg_data:
        await context.bot.send_message(OWNER_ID, "❌ ما عندي نسخة محفوظة من هذه الرسالة.")
        return

    message_type, text, file_id = msg_data
    if message_type == "text" and text:
        await context.bot.send_message(OWNER_ID, f"📩 نسخة محفوظة:\n\n{text}")
    elif message_type in ("photo", "video", "voice") and file_id:
        file = await context.bot.get_file(file_id)
        bio = io.BytesIO()
        await file.download_to_memory(out=bio)
        bio.seek(0)
        if message_type == "photo":
            await context.bot.send_photo(OWNER_ID, photo=bio, caption="📸 صورة محفوظة")
        elif message_type == "video":
            await context.bot.send_video(OWNER_ID, video=bio, caption="🎥 فيديو محفوظ")
        else:
            await context.bot.send_voice(OWNER_ID, voice=bio, caption="🔈 تسجيل صوتي محفوظ")
    else:
        await context.bot.send_message(OWNER_ID, "⚠ نوع الرسالة غير مدعوم أو لم يُحفظ.")

# أوامر البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 البوت شغال وجاهز لاسترجاع الرسائل المحذوفة!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_message_db(update.message)

async def edited_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.edited_message
    await send_saved_message(msg.chat.id, msg.message_id, context)
    save_message_db(msg)

async def get_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        return await update.message.reply_text("📌 الاستخدام: /get <chat_id> <message_id>")
    chat_id = int(context.args[0])
    message_id = int(context.args[1])
    await send_saved_message(chat_id, message_id, context)

# Webhook بدل polling
if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get", get_command))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, edited_message))

    print("✅ البوت شغال باستخدام Webhook...")

    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url="https://marwanbot.onrender.com/"
    )
