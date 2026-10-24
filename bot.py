import os
import logging
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

logging.basicConfig(level=logging.INFO)

TOKEN = "8825604569:AAEchttq-ix36kFL9Qt4GlnDS3hDUBnxFn0"



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! 📸\nأرسل لي رابط فيديو من إنستغرام (Reels) وسأقوم بتحميله لك فوراً.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()
    if not url.startswith("http"):
        return

    if "instagram.com" in url and "?" in url:
        url = url.split("?")[0]

    status_msg = await update.message.reply_text("⏳ جاري تحميل الفيديو، يرجى الانتظار...")

    output_filename = f"insta_{update.message.chat_id}.mp4"

    # استخدام صيغة جاهزة ومباشرة لتجنب مشاكل الدمج والمهلة الزمنية
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        if os.path.exists(output_filename):
            with open(output_filename, "rb") as f:
                await update.message.reply_video(video=f)
            os.remove(output_filename)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ لم نتمكن من إيجاد الفيديو، تأكد أن الحساب ليس خاصاً (Private).")
            
    except Exception as e:
        logging.error(f"Insta Download Error: {e}")
        if os.path.exists(output_filename):
            os.remove(output_filename)
        await status_msg.edit_text("❌ حدث خطأ أثناء التحميل. تأكد من صحة الرابط وأنه حساب عام.")

if __name__ == "__main__":
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .connect_timeout(60)
        .read_timeout(60)
        .write_timeout(60)
        .build()
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    app.run_polling()
