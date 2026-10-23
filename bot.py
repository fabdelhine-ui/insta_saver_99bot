import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# إعداد السجل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# الكود السري المطلوب من المستخدم هو 7
SECRET_CODE = "7" 

# قاموس بسيط لحفظ المستخدمين الذين قاموا بتفعيل الكود
verified_users = set()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # إزالة تفعيل المستخدم عند بدء التشغيل ليضطر لإدخال الكود
    if user_id in verified_users:
        verified_users.remove(user_id)
        
    await update.message.reply_text(
        "مرحباً بك في بوت تحميل فيديوهات إنستغرام! 📥\n\n"
        "للاستفادة من خدمات البوت وتحميل الفيديوهات، يرجى إرسال الكود السري (7) أولاً.\n"
        "💡 (يمكنك الحصول على الكود من قناتنا الرسمية، أو إرسال أي رابط وسأطلب منك الكود)."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # إذا كان النص هو الكود السري (7)
    if text == SECRET_CODE:
        verified_users.add(user_id)
        await update.message.reply_text("✅ تم تفعيل الكود بنجاح! يمكنك الآن إرسال أي رابط فيديو من إنستغرام وسأقوم بتحميله فوراً.")
        return

    # إذا أرسل المستخدم رابط إنستغرام
    if "instagram.com" in text:
        # التحقق هل المستخدم مفعل أم لا
        if user_id not in verified_users:
            await update.message.reply_text(
                f"🔒 عذراً، يجب عليك إدخال الكود السري أولاً لكي أتمكن من تحميل الفيديوهات.\n\n"
                f"أدخل الكود الصحيح الآن للمتابعة:"
            )
            return

        # إذا كان المستخدم مفعلاً، نبدأ بالتحميل
        await update.message.reply_text("⏳ جاري تحميل الفيديو، يرجى الانتظار...")
        
        output_filename = f"video_{user_id}.mp4"
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_filename,
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])
            
            with open(output_filename, 'rb') as video_file:
                await update.message.reply_video(video=video_file)
            
            os.remove(output_filename)
        except Exception as e:
            await update.message.reply_text("❌ حدث خطأ أثناء تحميل الفيديو. تأكد أن الرابط صحيح وعام.")
    else:
        # إذا أرسل كلاماً عشوائياً ليس رابطاً وليس الكود
        if user_id not in verified_users:
            await update.message.reply_text("❌ الكود غير صحيح. يرجى إرسال الكود الصحيح أو رابط إنستغرام صالح.")
        else:
            await update.message.reply_text("الرجاء إرسال رابط إنستغرام صالح لتحميله.")

def main():
    TOKEN = os.getenv("8825604569:AAG6Ehv_XzG57gMvyFhTE7pHcooIORNAnZw")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
