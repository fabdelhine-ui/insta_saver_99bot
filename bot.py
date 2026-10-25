import os
import logging
import datetime
import uuid
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# --- 1. إعداد خادم ويب خفيف للبقاء البوت Live على Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. إعداد السجلات ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8825604569:AAFv7EHlnJwZDeaXoGxY7nTrzQso2TeriV8"

# 📢 إعدادات الاشتراك الإجباري
REQUIRED_CHANNEL = "@ins2ta"  # معرف القناة الخاص بك

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

# دالة التحقق من اشتراك المستخدم في القناة
async def check_subscription(user_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        # الحالات التي تعني أن المستخدم مشترك
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        logger.error(f"خطأ في التحقق من الاشتراك: {e}")
        # في حال حدث خطأ تقني (مثل عدم رفع البوت مشرفاً في القناة)، يفضل السماح له مؤقتاً أو التعامل معه بحذر
        return False

# لوحة مفاتيح طلب الاشتراك الإجباري
def get_subscription_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 اشترك في القناة", url="https://t.me/ins2ta")],
        [InlineKeyboardButton("✅ تحققت من الاشتراك", callback_data="check_sub")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu(user_id):
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
    
    # التحقق من الاشتراك الإجباري أولاً
    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        sub_text = (
            "⚠️ **عذراً، يجب عليك الاشتراك في قناة البوت أولاً لكي تتمكن من استخدامه!**\n\n"
            "اشترك في القناة عبر الزر أدناه ثم اضغط على (✅ تحققت من الاشتراك)."
        )
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
                    await context.bot.send_message(
                        chat_id=referrer_id, 
                        text=f"🎉 قام شخص بالانضمام عبر رابطك! حصلت على +{POINTS_PER_REFERRAL} نقاط."
                    )
            except ValueError:
                pass

    points = user_data[user_id]["points"]
    
    welcome_text = (
        f"أهلاً بك في محمل فيديوهات إنستغرام! 📸\n\n"
        f"💰 رصيدك الحالي: {points} نقاط\n"
        f"أرسل لي رابط فيديو من إنستغرام (Reels) وسأقوم بتحميله (تكلفة التحميل: {POINTS_PER_DOWNLOAD} نقاط).\n\n"
        f"🎁 الهدية اليومية: يمكنك الحصول

