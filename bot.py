import os
import logging
import datetime
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# --- 1. إعداد خادم ويب خفيف للبقاء البوت Live على Render ---
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

# 📢 معرف القناة للاشتراك الإجباري
REQUIRED_CHANNEL = "@ins2ta"

# الإعدادات الاقتصادية للبوت
DEFAULT_FREE_POINTS = 6       # نقاط البداية للمستخدم الجديد
POINTS_PER_DOWNLOAD = 3       # تكلفة خصم النقاط لكل فيديو
DAILY_GIFT_POINTS = 3         # الهدية اليومية
POINTS_PER_REFERRAL = 2       # نقاط الدعوة

# قائمة أكواد البونيس
PROMO_CODES = {
    "VIP100": {"points": 100, "used_by": set(), "max_uses": None},
    "BONUS50": {"points": 50, "used_by": set(), "max_uses": None},
    "MOUNIB2026": {"points": 200, "used_by": set(), "max_uses": None},
    "UNLIMITED99": {"points": 1000000, "used_by": set(), "max_uses": 5}
}

# بيانات المستخدمين
user_data = {}

# دالة التحقق من الاشتراك الإجباري
async def check_subscription(user_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        logger.error(f"خطأ في التحقق من الاشتراك: {e}")
        return False

# أزرار طلب الاشتراك الإجباري
def get_subscription_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 اشترك في القناة", url="https://t.me/ins2ta")],
        [InlineKeyboardButton("✅ تحققت من الاشتراك", callback_data="check_sub")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu(user_id):
    points = user_data.get(user_id, {}).get("points", DEFAULT_FREE_POINTS)
    keyboard = [
        [
            InlineKeyboardButton("💰 رصيدي", callback_data="balance"),
            InlineKeyboardButton("🎁 الهدية اليومية", callback_data="daily_gift")
        ],
        [
            InlineKeyboardButton("📢 القناة الرسمية", url="https://t.me/mounibdch") 
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # فحص الاشتراك الإجباري
    if not await check_subscription(user_id, context):
        sub_text = "⚠️ عذراً، يجب عليك الاشتراك في قناة البوت أولاً لكي تتمكن من استخدامه!\n\nاشترك في القناة عبر الزر أدناه ثم اضغط على (✅ تحققت من الاشتراك)."
        if update.message:
            await update.message.reply_text(sub_text, reply_markup=get_subscription_keyboard())
        elif update.callback_query:
            await update.callback_query.message.edit_text(sub_text, reply_markup=get_subscription_keyboard())
        return

    if user_id not in user_data:
        user_data[user_id] = {"points": DEFAULT_FREE_POINTS, "last_gift": None}
        
        # نظام الدعوات عبر الـ start args
        if context.args:
            try:
                referrer_id = int(context.args[0])
                if referrer_id != user_id and referrer_id in user_data:
                    user_data[referrer_id]["points"] += POINTS_PER_REFERRAL
                    ref_msg = "🎉 قام شخص بالانضمام عبر رابطك! حصلت على +" + str(POINTS_PER_REFERRAL) + " نقاط."
                    await context.bot.send_message(
                        chat_id=referrer_id, 
                        text=ref_msg
                    )
            except ValueError:
                pass

    points = user_data[user_id]["points"]
    
    welcome_text = (
        f"أهلاً بك في محمل فيديوهات إنستغرام! 📸\n\n"
        f"💰 رصيدك الحالي: {points} نقاط\n"
        f"أرسل لي رابط فيديو من إنستغرام (Reels) وسأقوم بتحميله (تكلفة التحميل: {POINTS_PER_DOWNLOAD} نقاط).\n\n"
        f"🎁 الهدية اليومية: يمكنك الحصول على +{DAILY_GIFT_POINTS} نقاط يومياً عبر الأزرار أدناه!\n"
        f"🎟️ الأكواد: أرسل /code اسم_الكود لتفعيل كود البونيس.\n\n"
        f"🔗 رابط الدعوة الخاص بك:\n"
        f"https://t.me/insta_saver_99bot?start={user_id}\n"
        f"شارك هذا الرابط واحصل على +{POINTS_PER_REFERRAL} نقاط لكل شخص ينضم!"
    )

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=get_main_menu(user_id))
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=get_main_menu(user_id))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "check_sub":
        if await check_subscription(user_id, context):
            await query.message.delete()
            update.callback_query = query
            await start(update, context)
        else:
            await query.answer("❌ لم تقم بالاشتراك في القناة بعد!", show_alert=True)
        return

    if not await check_subscription(user_id, context):
        await query.message.edit_text("⚠️ يجب عليك الاشتراك في القناة أولاً لاستخدام البوت!", reply_markup=get_subscription_keyboard())
        return

    if user_id not in user_data:
        user_data[user_id] = {"points": DEFAULT_FREE_POINTS, "last_gift": None}

    if query.data == "balance":
        pts = user_data[user_id]["points"]
        await query.message.reply_text(f"💰 رصيدك الحالي هو: {pts} نقطة.")
        
    elif query.data == "daily_gift":
        now = datetime.date.today()
        if user_data[user_id]["last_gift"] == now:
            await query.message.reply_text("🎁 لقد استلمت هديتك اليومية بالفعل اليوم! عُد غداً لربح المزيد.")
        else:
            user_data[user_id]["points"] += DAILY_GIFT_POINTS
            user_data[user_id]["last_gift"] = now
            new_pts = user_data[user_id]["points"]
            await query.message.reply_text(f"🎉 مبروك! حصلت على هدية يومية {DAILY_GIFT_POINTS} نقاط. رصيدك الآن: {new_pts} نقطة.")

async def redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_subscription(user_id, context):
        await update.message.reply_text("⚠️ يجب عليك الاشتراك في قناة البوت أولاً لتفعيل الأكواد!", reply_markup=get_subscription_keyboard())
        return

    if user_id not in user_data:
        user_data[user_id] = {"points": DEFAULT_FREE_POINTS, "last_gift": None}

    if not context.args:
        await update.message.reply_text("❌ الكود غير صحيح أو انتهت صلاحيته!")
        return

    code_entered = context.args[0].strip().upper()

    if code_entered in PROMO_CODES:
        code_data = PROMO_CODES[code_entered]

        if user_id in code_data["used_by"]:
            await update.message.reply_text("❌ لقد قمت باستخدام هذا الكود من قبل!")
            return

        if code_data["max_uses"] is not None and len(code_data["used_by"]) >= code_data["max_uses"]:
            await update.message.reply_text("❌ الكود غير صحيح أو انتهت صلاحيته!")
            return

        reward_points = code_data["points"]
        user_data[user_id]["points"] += reward_points
        code_data["used_by"].add(user_id)

        await update.message.reply_text(
            f"🎉 مبروك! تم تفعيل كود البونيس بنجاح.\n"
            f"➕ حصلت على +{reward_points} نقطة إضافية!\n"
            f"💰 رصيدك الإجمالي الآن: {user_data[user_id]['points']} نقاط."
        )
    else:
        await update.message.reply_text("❌ الكود غير صحيح أو انتهت صلاحيته!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if not await check_subscription(user_id, context):
        await update.message.reply_text("⚠️ عذراً، لا يمكنك تحميل الفيديوهات قبل الاشتراك في القناة!", reply_markup=get_subscription_keyboard())
        return

    if user_id not in user_data:
        user_data[user_id] = {"points": DEFAULT_FREE_POINTS, "last_gift": None}

    if "instagram.com" in text:
        if user_data[user_id]["points"] < POINTS_PER_DOWNLOAD:
            await update.message.reply_text(f"⚠️ رصيدك غير كافٍ! تحتاج إلى {POINTS_PER_DOWNLOAD} نقاط على الأقل لتحميل الفيديو.")
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

            user_data[user_id]["points"] -= POINTS_PER_DOWNLOAD
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
    application.add_handler(CommandHandler("code", redeem_code))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
