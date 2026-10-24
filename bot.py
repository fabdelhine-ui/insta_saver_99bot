import os
import logging
import datetime
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
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

# بيانات المستخدمين
user_data = {}

def get_main_menu(user_id):
    points = user_data.get(user_id, {}).get("points", 3)
    keyboard = [
        [
            InlineKeyboardButton("💰 رصيدي", callback_data="balance"),
            InlineKeyboardButton("🎁 الهدية اليومية", callback_data="daily_gift")
        ],
        [
            InlineKeyboardButton("📢 القناة الرسمية", url="https://t.me/your_channel") # استبدل برابط قناتك
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {"points": 3, "last_gift": None}

    points = user_data[user_id]["points"]
    
    welcome_text = (
        f"أهلاً بك في محمل فيديوهات إنستغرام! 📸\n\n"
        f"💰 رصيدك الحالي: {points} نقاط\n"
        f"أرسل لي رابط فيديو من إنستغرام (Reels) وسأقوم بتحميله (تكلفة التحميل: 1 نقطة).\n\n"
        f"🎁 الهدية اليومية: يمكنك الحصول على +10 نقاط يومياً عبر الأزرار أدناه!\n"
        f"🔗 رابط الدعوة الخاص بك:\n"
        f"https://t.me/insta_saver_99bot?start={user_id}\n"
        f"شارك هذا الرابط واحصل على +2 نقطة لكل شخص ينضم!"
    )

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=get_main_menu(user_id))
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=get_main_menu(user_id))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {"points": 3, "last_gift": None}

    if query.data == "balance":
        pts = user_data[user_id]["points"]
        await query.message.reply_text(f"💰 رصيدك الحالي هو: {pts} نقطة.")
        
    elif query.data == "daily_gift":
        now = datetime.date.today()
        if user_data[user_id]["last_gift"] == now:
            await query.message.reply_text("🎁 لقد استلمت هديتك اليومية بالفعل اليوم! عُد غداً لربح المزيد.")
        else:
            user_data[user_id]["points"] += 10
            user_data[user_id]["last_gift"] = now
            new_pts = user_data[user_id]["points"]
            await query.message.reply_text(f"🎉 مبروك! حصلت على هدية يومية 10 نقاط. رصيدك الآن: {new_pts} نقطة.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_data:
        user_data[user_id] = {"points": 3, "last_gift": None}

    if "instagram.com" in text:
        if user_data[user_id]["points"] <= 0:
            await update.message.reply_text("⚠️ رصيدك من النقاط نفد! استخدم الهدية اليومية أو دعوة الأصدقاء لجمع النقاط.")
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

            user_data[user_id]["points"] -= 1
            remaining = user_data[user_id]["points"]
            await update.message.reply_text(f"✅ تم التحميل بنجاح! الرصيد المتبقي: {remaining} نقطة.", reply_markup=get_main_menu(user_id))
                
        except Exception as e:
            logger.error(f"خطأ في التحميل: {e}")
            await update.message.reply_text("حدث خطأ أثناء محاولة تحميل الفيديو. تأكد أن الرابط صحيح وعام.")
    else:
        await update.message.reply_text("الرجاء إرسال رابط إنستغرام صالح للتحميل، أو استخدام القائمة أدناه.", reply_markup=get_main_menu(user_id))

def main():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
