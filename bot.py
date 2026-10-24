import os
import logging
import datetime
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# --- 1. إعداد خادم ويب خفيف لمنصة Render (لبقاء البوت Live) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. إعداد السجلات ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8825604569:AAFv7EHlnJwZDeaXoGxY7nTrzQso2TeriV8"

# بيانات المستخدمين (النقاط، التحقق، وتاريخ آخر هدية يومية)
user_data = {}
verified_users = set()
SECRET_CODE = "7"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in verified_users:
        verified_users.remove(user_id)
        
    if user_id not in user_data:
        user_data[user_id] = {"points": 10, "last_gift": None}  # رصيد ابتدائي 10 نقاط

    await update.message.reply_text(
        "أهلاً بك في بوت تحميل إنستغرام مع نظام النقاط والهدية اليومية!\n"
        "هذا البوت محمي بكلمة مرور. يرجى إرسال رمز الدخول (الرمز 7) للتمكن من استخدام البوت:"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_data:
        user_data[user_id] = {"points": 10, "last_gift": None}

    # الخطوة الأولى: التحقق من رمز البوابة
    if user_id not in verified_users:
        if text == SECRET_CODE:
            verified_users.add(user_id)
            await update.message.reply_text(
                "✅ تم التحقق بنجاح!\n"
                "يمكنك الآن إرسال روابط إنستغرام للتحميل، أو كتابة /gift للحصول على هديتك اليومية، أو /balance لمعرفة نقاطك."
            )
        else:
            await update.message.reply_text("❌ الرمز غير صحيح. يرجى إرسال الرمز الصحيح للمتابعة.")
        return

    # الأوامر الإضافية داخل البوت للمستخدمين المعتمدين
    if text == "/balance":
        pts = user_data[user_id]["points"]
        await update.message.reply_text(f"💰 رصيدك الحالي هو: {pts} نقطة.")
        return

    if text == "/gift":
        now = datetime.date.today()
        if user_data[user_id]["last_gift"] == now:
            await update.message.reply_text("🎁 لقد استلمت هديتك اليومية بالفعل! عُد غداً لربح المزيد.")
        else:
            user_data[user_id]["points"] += 5
            user_data[user_id]["last_gift"] = now
            await update.message.reply_text(f"🎉 مبروك! حصلت على هدية يومية 5 نقاط. رصيدك الآن: {user_data[user_id]['points']} نقطة.")
        return

    # الخطوة الثانية: تحميل فيديوهات إنستغرام
    if "instagram.com" in text:
        if user_data[user_id]["points"] <= 0:
            await update.message.reply_text("⚠️ رصيدك من النقاط نفد! استخدم /gift للحصول على نقاط يومية جديدة.")
            return

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

            # خصم نقطة بعد التحميل الناجح
            user_data[user_id]["points"] -= 1
            remaining = user_data[user_id]["points"]
            await update.message.reply_text(f"✅ تم التحميل بنجاح! الرصيد المتبقي: {remaining} نقطة.")
                
        except Exception as e:
            logger.error(f"خطأ في التحميل: {e}")
            await update.message.reply_text("حدث خطأ أثناء محاولة تحميل الفيديو. تأكد أن الرابط صحيح وعام.")
    else:
        await update.message.reply_text("الرجاء إرسال رابط إنستغرام صالح، أو استخدم الأوامر المتاحة مثل /balance لمعرفة نقاطك أو /gift للهدية اليومية.")

def main():
    # تشغيل خادم الويب في الخلفية
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
