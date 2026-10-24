import os
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)

# التوكن الخاص ببوتك
TOKEN = "8825604569:AAEchttq-ix36kFL9Qt4GlnDS3hDUBnxFn0"

# قناتك الرسمية للتحقق من الاشتراك الإجباري
CHANNEL_USERNAME = "@mounibdch" 
CHANNEL_LINK = "https://t.me/mounibdch"

# قاعدة بيانات مؤقتة للنقاط
user_points = {}
DEFAULT_FREE_POINTS = 3  # النقاط المجانية عند البدء
POINTS_PER_REFERRAL = 2  # النقاط الممنوحة عند دعوة صديق

# الأكواد الترويجية (يمكنك إضافة أو تعديل الأكواد هنا)
PROMO_CODES = {
    "VIP100": {"points": 100, "used_by": set()},
    "BONUS50": {"points": 50, "used_by": set()},
    "MOUNIB2026": {"points": 200, "used_by": set()}
}

async def is_subscribed(bot, user_id: int) -> bool:
    """التحقق مما إذا كان المستخدم عضواً في قناتك"""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        logging.error(f"Check subscription error: {e}")
        return False

async def send_sub_request(update: Update):
    """إرسال رسالة طلب الانضمام لقناتك"""
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_points:
        user_points[user_id] = DEFAULT_FREE_POINTS
        
        # نظام الإحالة ودعوة الأصدقاء
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
        f"🎁 **استخدام الكود:** لاستخدام كود الهدية أرسل الأمر:\n`/code اسم_الكود`\n\n"
        f"🔗 **رابط الدعوة الخاص بك:**\n`{ref_link}`\n"
        f"شارك هذا الرابط مع أصدقائك واحصل على +{POINTS_PER_REFERRAL} نقاط لكل شخص ينضم!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    points = user_points.get(user_id, DEFAULT_FREE_POINTS)
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    text = (
        f"📊 **رصيدك الحالي:** {points} نقطة\n\n"
        f"🎁 **أدخل كود الهدية:**\nأرسل `/code اسم_الكود` للحصول على نقاط مجانية!\n\n"
        f"🔗 **رابط الدعوة الخاص بك:**\n`{ref_link}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_subscribed(context.bot, user_id):
        await send_sub_request(update)
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ **يرجى كتابة الكود بعد الأمر!**\nمثال: `/code VIP100`", 
            parse_mode="Markdown"
        )
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

async def check_sub_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await is_subscribed(context.bot, user_id):
        await query.message.delete()
        await query.message.reply_text("✅ تم التأكد من اشتراكك بنجاح! يمكنك الآن استخدام البوت.")
    else:
        await query.message.reply_text("❌ لم تشترك في القناة بعد! يرجى الاشتراك أولاً ثم الضغط على زر التحقق.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id

    if not await is_subscribed(context.bot, user_id):
        await send_sub_request(update)
        return

    current_points = user_points.get(user_id, DEFAULT_FREE_POINTS)
    if current_points <= 0:
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        await update.message.reply_text(
            f"❌ **عذراً، نفدت نقاطك!**\n\n"
            f"استخدم كود هدية عبر الأمر `/code الكود` أو شارك رابط الدعوة للحصول على نقاط:\n`{ref_link}`",
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
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("code", redeem_code))
    app.add_handler(CallbackQueryHandler(check_sub_button, pattern="^check_sub$"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    app.run_polling()
