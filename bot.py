import os
import logging
import yt_dlp
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)

# التوكن الخاص ببوتك
TOKEN = "8825604569:AAHLkYHHpjMjonlIDEYfRUF_utVYoxL8IVw"

# قناتك الرسمية
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
        return True

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

    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    welcome_text = (
        "أهلاً بك في محمل فيديوهات إنستغرام! 📸\n\n"
        f"💰 رصيدك الحالي: **{user_points[user_id]} نقاط**\n"
        "أرسل لي رابط فيديو من إنستغرام (Reels) وسأقوم بتحميله (تكلفة التحميل: 1 نقطة).\n\n"
        f"🎁 **الهدية اليومية:** يمكنك الحصول على +{DAILY_BONUS_POINTS} نقاط يومياً عبر الأزرار أدناه!\n"
        "🎟️ **الأكواد:** أرسل /code اسم_الكود لتفعيل الكود الترويجي.\n\n"
        "🔗 **رابط الدعوة الخاص بك:**\n"
        f"{ref_link}\n"
        f"شارك هذا الرابط واحصل على +{POINTS_PER_REFERRAL} نقاط لكل شخص ينضم!"
    )

    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

async def claim_daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    user_id = update.effective_user.id

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
        "🎁 **الهدية اليومية:** اضغط الزر أدناه كل 24 ساعة.\n"
        "🎟️ **استبدال كود:** أرسل /code الكود\n\n"
        "🔗 **رابط الدعوة الخاص بك:**\n"
        f"{ref_link}"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

async def redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("⚠️ **يرجى كتابة الكود بعد الأمر!**\nمثال: /code VIP100", parse_mode="Markdown")
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
    else:
        await update.message.reply_text("❌ الكود غير صحيح أو انتهت صلاحيته!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "claim_daily":
        await claim_daily_bonus(update, context)
    elif data == "get_balance":
        await balance_command(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id

    current_points = user_points.get(user_id, DEFAULT_FREE_POINTS)
    if current_points <= 0:
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        await update.message.reply_text(
            "❌ **عذراً، نفدت نقاطك!**\n\n"
            "خذ الهدية اليومية عبر أزرار التحكم أو استخدم كود هدية /code الكود للحصول على نقاط:\n"
            f"{ref_link}",
            parse_mode="Markdown"
        )
        return

    url = update.message.text.strip()
    if not url.startswith("http"):
        return

    if "instagram.com" in url and "?" in url:
        url = url.split("?")[0]

    status_msg = await update.message.reply_text("⏳ جاري تحميل الفيديو، يرجى الانتظار...")
    output_filename = f"insta_{user_id}.mp4"

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
            
            user_points[user_id] -= 1
            await update.message.reply_text(f"✅ تم التحميل بنجاح! الرصيد المتبقي: {user_points[user_id]} نقاط.")
            
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
    app.add_handler(CommandHandler("daily", claim_daily_bonus))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("code", redeem_code))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    app.run_polling()
