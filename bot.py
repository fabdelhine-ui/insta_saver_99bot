import os
import logging
import datetime
import uuid
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# --- 1. إعداد خادم ويب خفيف لبقاء البوت Live على Render ---
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
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        logger.error(f"خطأ في التحقق من الاشتراك: {e}")
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
    user
