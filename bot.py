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
last_daily_claim = {}  # { user_id: datetime } لحفظ وقت آخر هدية يومية

DEFAULT_FREE_POINTS = 3   # النقاط المجانية عند البدء
POINTS_PER_REFERRAL = 2   # النقاط عند دعوة صديق
DAILY_BONUS_POINTS = 10   # عدد نقاط الهدية اليومية

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
    """أزرار تحكم شفافة واحترافية"""
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

    welcome_text = (
        f"أهلاً بك في محمل فيديوهات إنستغرام! 📸\n\n"
        f"💰 رصيدك الحالي: **{user_points[user_id]} نقاط**\n"
        f"أرسل لي رابط فيديو من إنستغرام (Reels) وسأقوم بتحميله (تكلفة التحميل: 1 نقطة).\n\n"
        f"🎁 **الهدية اليومية:** يمكنك الحصول على +{DAILY_BONUS_POINTS} نقاط يومياً عبر الأزرار أدناه!\n"
        f"🎟️ **الأكواد:** أرسل `/code اسم_الكود` لتفعيل الكود الترويجي.\n\n"
        f"🔗 **رابط الدعوة الخاص بك:**\n`{ref_link}`\n"
        f"شارك هذا الرابط واحصل على +{POINTS_PER_REFERRAL} نقاط لكل شخص ينضم!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# ==========================================
# 🎁 دالة الهدية اليومية (Daily Bonus)
# ==========================================
async def claim_daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    user_id = update.effective_user.id

    if not await is_subscribed(context.bot, user_id):
        await send_sub_request(update)
        return

    now = datetime.now()
    last_claim = last_daily_claim.get(user_id)

    if last_claim and (now - last_claim) < timedelta(hours=24):
        time_left = timedelta(hours=24) - (now - last_claim)
        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        msg = f"⏳ لقد أخذت هديتك اليومية بالفعل!\nيرجى العودة بعد **{hours} ساعة و {minutes} دقيقة**."
        
        if query:
            await query.answer(msg, show_alert=True)
        else:
            await update.message.reply_text(msg, parse_mode="Markdown")
        return

    # منح الهدية اليومية
    last_daily_claim[user_id] = now
    user_points[user_id] = user_points.get(user_id, DEFAULT_FREE_POINTS) + DAILY_BONUS_POINTS
    
    success_msg = f"🎉 مبروك! حصلت على هديتك اليومية وهي **+{DAILY_BONUS_POINTS} نقاط**.\n💰 رصيدك الآن: **{user_points[user_id]} نقاط**."
    
    if query:
        await query.answer("🎉 تم استلام الهدية اليومية بنجاح!", show_alert=True)
        await query.message.reply_text(success_msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(success_msg, parse_mode="Markdown")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    points = user_points.get(user_id, DEFAULT_FREE_POINTS)
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    text = (
        f"📊 **رصيدك الحالي:** {points} نقطة\n\n"
        f"🎁 **الهدية اليومية:** اضغط الزر أدناه كل 24 ساعة.\n"
        f"🎟️ **استبدال كود:** أرسل `/code الكود`\n\n"
        f"🔗 **رابط الدعوة الخاص بك:**\n`{ref_link}`"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

async def redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_subscribed(context.bot, user_id):
        await send_sub_request(update)
        return

    if not context.args:
        await update.message.reply_text("⚠️ **يرجى كتابة الكود بعد الأمر!**\nمثال: `/code VIP100`", parse_mode="Markdown")
        return

    code_entered = context.args[0].strip().upper()

    if code_entered in PROMO_CODES:
        code_data = PROMO_CODES[code_entered]
        if user_id in code_data["used_by"]:
            await update.message.reply_text("❌ لقد قمت باستخدام هذا الكود من قبل!")
            return

        reward_points = code_data["points"]
        user_points[user_id] = user_points.get(user_id, DEFAULT_FREE_POINTS) + reward_points
        code_data["used_by"].add(user_id)

        await update.message.reply_text(
            f"🎉 **مبروك!** تم تفعيل الكود بنجاح.\n"
            f"➕ حصلت على **+{reward_points}** نقطة إضافية!\n"
            f"💰 رصيدك الإجمالي الآن: **{user_points[user_id]}** نقاط.",
            parse_mode="Markdown"
        )
