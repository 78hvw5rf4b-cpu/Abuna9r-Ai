import os
import logging
import asyncio
import threading
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError

# --- سيرفر Flask لإرضاء Render ومنعه من الإغلاق ---
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "AI Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()
# ------------------------------------------------

logging.basicConfig(level=logging.INFO)

CHANNEL_USERNAME = "@Abu_na9r"
CHANNEL_LINK = "https://t.me/Abu_na9r"

def register_user(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    if "all_users" not in context.bot_data:
        context.bot_data["all_users"] = set()
    context.bot_data["all_users"].add(user_id)

async def check_sub(bot, user_id: int) -> bool:
    """التحقق من اشتراك المستخدم في القناة"""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
    except TelegramError as e:
        logging.error(f"Sub check error: {e}")
        return True
    return False

def get_sub_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 اشترك في القناة أولاً", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ تحققت من الاشتراك", callback_data="check_subscription")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🚀 البدء / Start", callback_data="cmd_start"),
            InlineKeyboardButton("📊 الإحصائيات", callback_data="cmd_stats")
        ],
        [
            InlineKeyboardButton("📢 قناة التحديثات 🎁", url=CHANNEL_LINK)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    register_user(context, user_id)

    if not await check_sub(context.bot, user_id):
        await update.message.reply_text(
            f"⚠️ **أهلاً بك في بوت Abuna9r AI!**\n\nعليك الاشتراك في القناة أولاً لاستخدام الذكاء الاصطناعي:\n{CHANNEL_LINK}",
            reply_markup=get_sub_keyboard()
        )
        return

    await update.message.reply_text(
        "🤖 **أهلاً بك في بوت Abuna9r AI!**\n\n"
        "أنا مساعدك الذكي، يمكنك أن تسألني عن أي شيء، كتابة مقالات، حل مشاكل برمجة، أو ترجمة النصوص!\n\n"
        "💬 **أرسل سؤالك أو استفسارك مباشرة الآن...**",
        reply_markup=get_main_keyboard()
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    register_user(context, user_id)

    if query.data == "check_subscription":
        if await check_sub(context.bot, user_id):
            await query.message.edit_text("✅ شكراً لاشتراكك! يمكنك الآن كتابة أي سؤال للذكاء الاصطناعي.", reply_markup=get_main_keyboard())
        else:
            await query.message.reply_text("❌ لم تشترك بعد! اشترك ثم اضغط على الزر مجدداً.", reply_markup=get_sub_keyboard())
    elif query.data == "cmd_start":
        await query.message.reply_text("أهلاً بك مجدداً! تفضل بطرح سؤالك وسأجيبك فوراً.", reply_markup=get_main_keyboard())
    elif query.data == "cmd_stats":
        total_users = len(context.bot_data.get("all_users", set()))
        await query.message.reply_text(f"📊 **إحصائيات مستخدمي الذكاء الاصطناعي:**\n\nعدد المستخدمين: {total_users} شخص", reply_markup=get_main_keyboard())

# --- محرك الذكاء الاصطناعي المجاني المباشر ---
def ask_ai(prompt: str) -> str:
    try:
        url = f"https://api.duckduckgo.com/?q={prompt}&format=json"
        # محرك توليد إجابات سريع ومباشر
        res = requests.get(f"https://text.pollinations.ai/{requests.utils.quote(prompt)}", timeout=20)
        if res.status_code == 200 and res.text.strip():
            return res.text.strip()
    except Exception as e:
        logging.error(f"AI API Error: {e}")
    return "عذراً، تعذر معالجة الطلب حالياً. حاول إعادة كتابة السؤال بشكل آخر."

async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    register_user(context, user_id)

    if not await check_sub(context.bot, user_id):
        await update.message.reply_text("⚠️ اشترك في القناة أولاً لاستخدام الذكاء الاصطناعي!", reply_markup=get_sub_keyboard())
        return

    user_text = update.message.text.strip()
    status_msg = await update.message.reply_text("🧠 جاري التفكير وإعداد الإجابة...")

    try:
        response = await asyncio.to_thread(ask_ai, user_text)
        await status_msg.edit_text(response, reply_markup=get_main_keyboard())
    except Exception as e:
        logging.error(f"Error AI Handling: {e}")
        await status_msg.edit_text("❌ حدث خطأ أثناء الاتصال بالذكاء الاصطناعي.", reply_markup=get_main_keyboard())

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("خطأ: لم يتم العثور على BOT_TOKEN!")
        return

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_message))

    application.run_polling()

if __name__ == "__main__":
    main()
