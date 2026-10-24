import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# --- 1. إعداد خادم ويب خفيف لمنصة Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    # Render يمرر المنفذ عبر متغير البيئة PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. إعداد سجلات الأخطاء ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8825604569:AAFv7EHlnJwZDeaXoGxY7nTrzQso2TeriV8"
verified_users = set()
SECRET_CODE = "7"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in verified_users:
        verified_users.remove(user_id)
    await update.message.reply_text(
        "أهلاً بك في بوت تحميل إنستغرام!\n"
        "هذا البوت محمي بكلمة مرور. يرجى إرسال رمز الدخول للتمكن من استخدام البوت:"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in verified_users:
        if text == SECRET_CODE:
            verified_users.add(user_id)
            await update.message.reply_text(
                "✅ تم التحقق بنجاح!\n"
                "يمكنك الآن إرسال أي رابط فيديو أو منشور من إنستغرام لتحميله."
            )
        else:
            await update.message.reply_text("❌ الرمز غير صحيح. يرجى إدخال الرمز الصحيح للمتابعة.")
        return

    if "instagram.com" in text:
        await update.message.reply_text("⏳ جاري تحميل المحتوى من إنستغرام، يرجى الانتظار...")
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloaded_video.mp4',
            'quiet': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info)
            
            with open(filename, 'rb') as video_file:
                await update.message.reply_video(video=video_file)
                
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            logger.error(f"خطأ في التحميل: {e}")
            await update.message.reply_text("حدث خطأ أثناء محاولة تحميل الفيديو. تأكد أن الرابط صحيح وعام.")
    else:
        await update.message.reply_text("الرجاء إرسال رابط إنستغرام صالح للتحميل.")

def main():
    # تشغيل خادم Web في الخلفية
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

    # تشغيل البوت
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == "__main__":
    main()
