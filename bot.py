import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# إعداد السجلات لمتابعة حالة البوت والأخطاء
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# وضع التوكن المباشر الخاص بك هنا
BOT_TOKEN = "8825604569:AAG6Ehv_XzG57gMvyFhTE7pHcooIORNaNzW"

# مجموعة لتخزين المستخدمين الذين قاموا بإدخال الرمز الصحيح بنجاح
verified_users = set()

# الرمز السري المطلوب للوصول (البوابة)
SECRET_CODE = "7"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة البدء، ترحب بالمستخدم وتطلب منه إدخال رمز التحقق."""
    user_id = update.effective_user.id
    # إزالة المستخدم من القائمة المؤكدة عند البدء من جديد لضمان الحماية
    if user_id in verified_users:
        verified_users.remove(user_id)
        
    await update.message.reply_text(
        "أهلاً بك في بوت تحميل إنستغرام!\n"
        "هذا البوت محمي بكلمة مرور. يرجى إرسال رمز الدخول للتمكن من استخدام البوت:"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع الرسائل الواردة (إما الرمز السري أو روابط إنستغرام)."""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # الخطوة الأولى: التحقق مما إذا كان المستخدم لم يقم بإدخال الرمز بعد
    if user_id not in verified_users:
        if text == SECRET_CODE:
            verified_users.add(user_id)
            await update.message.reply_text(
                "✅ تم التحقق بنجاح!\n"
                "يمكنك الآن إرسال أي رابط فيديو أو منشور من إنستغرام لتحميله."
            )
        else:
            await update.message.reply_text(
                "❌ الرمز غير صحيح. يرجى إدخال الرمز الصحيح للمتابعة."
            )
        return

    # الخطوة الثانية: إذا كان المستخدم مؤكداً، نبدأ بتحميل رابط إنستغرام
    if "instagram.com" in text:
        await update.message.reply_text("⏳ جاري تحميل المحتوى من إنستغرام، يرجى الانتظار...")
        
        # إعدادات yt-dlp للتحميل
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloaded_video.mp4',
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info)
            
            # إرسال الفيديو للمستخدم
            with open(filename, 'rb') as video_file:
                await update.message.reply_video(video=video_file)
                
            # حذف الملف المحلي بعد الإرسال لتوفير المساحة
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            logger.error(f"خطأ في التحميل: {e}")
            await update.message.reply_text("حدث خطأ أثناء محاولة تحميل الفيديو. تأكد أن الرابط صحيح وعام.")
    else:
        await update.message.reply_text("الرجاء إرسال رابط إنستغرام صالح للتحميل.")

def main():
    """تشغيل البوت باستخدام التوكن المباشر."""
    application = Application.builder().token(BOT_TOKEN).build()

    # إضافة الأوامر ومعالجات الرسائل
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # تشغيل البوت
    application.run_polling()

if __name__ == "__main__":
    main()
