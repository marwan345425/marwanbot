from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import logging
import os

OWNER_ID = 5193446345  # رقمك الشخصي
TOKEN = "8196646590:AAEMri3y4yNtZWGdtzqH7ftBfMhYf5koxSs"  # توكن البوت
WEBHOOK_URL = "https://marwanbot.onrender.com/"  # رابط الويب هوك

logging.basicConfig(level=logging.INFO)

async def handle_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    user = msg.from_user
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "بدون معرف"

    text = f"📨 رسالة خاصة من {name} ({username}):\n\n"

    if msg.text:
        text += msg.text
        await context.bot.send_message(OWNER_ID, text)

    elif msg.photo:
        caption = msg.caption if msg.caption else "📷 صورة بدون تعليق"
        await context.bot.send_photo(OWNER_ID, photo=msg.photo[-1].file_id, caption=text + caption)

    elif msg.video:
        caption = msg.caption if msg.caption else "🎥 فيديو بدون تعليق"
        await context.bot.send_video(OWNER_ID, video=msg.video.file_id, caption=text + caption)

    elif msg.voice:
        await context.bot.send_voice(OWNER_ID, voice=msg.voice.file_id, caption=text + "🔈 تسجيل صوتي")

    else:
        await context.bot.send_message(OWNER_ID, text + "📎 تم استقبال نوع رسالة غير مدعوم حالياً.")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.ChatType.PRIVATE, handle_private))

if __name__ == "__main__":
    print("✅ البوت يشتغل ويستقبل رسائل الخاص...")
    PORT = int(os.environ.get('PORT', 10000))
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )
