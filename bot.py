import os
import logging
import yt_dlp
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)

# التوكن الخاص ببوتك
TOKEN = "8825604569:AAEchttq-ix36kFL9Qt4GlnDS3hDUBnxFn0"

# قناتك الرسمية للتحقق من الاشتراك الإجباري
CHANNEL_USERNAME = "@mounibdch" 
CHANNEL_LINK = "https://t.me/mounibdch"

# قاعدة البيانات المؤقتة
user_points = {}
last_daily_claim = {}

DEFAULT_FREE_POINTS = 3
POINTS_PER_REFERRAL = 2
DAILY_BONUS_POINTS = 10

PROMO_CODES = {
    "VIP100": {"points": 100, "used_by": set()},
    "BONUS50": {"points": 50, "used_by": set()},
    "MOUNIB2026": {"points": 200, "used_by": set()}
}

async def is_subscribed(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        logging.error(f"Check subscription error: {e}")
        return False

async def send_sub_request(update: Update):
    keyboard = [
        [InlineKeyboardButton("📢 اشترك في قناة البوت أولاً", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ تحقّق من الاشتراك", callback_data="check_sub")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "⚠️ لاستخدام البوت، يجب عليك الانضمام إلى قناتنا الرسمية أولاً!"
    
    if update.message:
        await update.message.reply_text(msg, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg, reply_markup=reply_markup)

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎁 الهدية اليومية", callback_data="claim_daily"), InlineKeyboardButton("💰 رصيدي", callback_data="get_balance")],
        [InlineKeyboardButton("📢 القناة الرسمية", url=CHANNEL_LINK)]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_points:
        user_points[user_id] = DEFAULT_FREE_POINTS
        
        if context.args:
            try:
                referrer_id = int(context.args[0])
                if referrer_id != user_id and referrer_id in user_points:
                    user_points[referrer_id] += POINTS_PER_REFERRAL
                    await context.bot.send_message(
                        chat_id=referrer_id, 
                        text=f"🎉 قام شخص بالانضمام عبر رابطك! حصلت على +{POINTS_PER_REFERRAL} نقاط."
                    )
            except ValueError:
                pass

    if not await is_subscribed(context.bot, user_id):
        await send_sub_request(update)
        return

    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    welcome_text = f"""أهلاً بك في محمل فيديوهات إنستغرام! 📸

💰 رصيدك الحالي: **{user_points[user_id]} نقاط**
أرسل لي رابط فيديو من إنستغرام (Reels) وسأقوم بتحميله (تكلفة التحميل: 1 نقطة).

🎁 **الهدية اليومية:** يمكنك الحصول على +{DAILY_BONUS_POINTS} نقاط يومياً عبر الأزرار أدناه!
🎟️ **الأكواد:** أرسل /
