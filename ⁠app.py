import os
import logging
import requests
import asyncio
from flask import Flask
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- سيرفر Flask لمنع إغلاق الاستضافة على Render ---
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "AI Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()
# ------------------------------------------------

logging.basicConfig(level=logging.INFO)

# ضع معرف القناة ومعرف البوت الخاص بك هنا
CHANNEL_USERNAME = "@Abuna9r_Ai" 
BOT_USERNAME = "Abuna9r_Ai_bot"  # معرف البوت الخاص بك بدون @

def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🚀 البدء / Start", callback_data="cmd_start"),
            InlineKeyboardButton("📢 قناة التحديثات 🎁", url="https://t.me/Abuna9r_Ai")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# زر التحويل الخاص الذي يظهر تحت منشور القناة
def get_channel_post_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("💬 تحدث مع الذكاء الاصطناعي خفية", url=f"https://t.me/{BOT_USERNAME}?start=from_channel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def ask_gemini_ai(prompt: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ لم يتم إضافة GEMINI_API_KEY في متغيرات البيئة."
    
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    try:
        res = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        if res.status_code == 200:
            data = res.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return "❌ حدث خطأ في الاستجابة من الذكاء الاصطناعي."
    except Exception as e:
        logging.error(f"Gemini API Error: {e}")
        return "❌ تعذر الاتصال بالذكاء الاصطناعي حالياً."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "أهلاً بك في بوت الذكاء الاصطناعي! 🤖✨\nمحادثتك هنا خاصة ومستقلة تماماً ولا يراها أحد غيرك.\n\nتفضل بكتابة سؤالك:",
        reply_markup=get_main_keyboard()
    )

# دالة نشر منشور في القناة مرفق بزر التحويل الخصي
async def post_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text_to_send = " ".join(context.args)
    if not text_to_send:
        await update.message.reply_text("❌ اكتب النص بعد الأمر، مثال:\n`/post أهلاً بكم! اضغط على الزر للحديث مع الذكاء الاصطناعي بشكل خاص.`", parse_mode="Markdown")
        return

    try:
        await context.bot.send_message(
            chat_id=CHANNEL_USERNAME, 
            text=text_to_send, 
            reply_markup=get_channel_post_keyboard()
        )
        await update.message.reply_text("✅ تم نشر المنشور مع زر المحادثة الخاصة في القناة!")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل النشر في القناة. التأكد من أن البوت مشرف في القناة.\nالخطأ: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    status_msg = await update.message.reply_text("🤖 جاري التفكير والإجابة...")
    
    ai_reply = await asyncio.to_thread(ask_gemini_ai, text)
    await status_msg.edit_text(ai_reply, reply_markup=get_main_keyboard())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "cmd_start":
        await query.message.reply_text("أهلاً بك! اكتب سؤالك هنا وسأجيبك فوراً.", reply_markup=get_main_keyboard())

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("خطأ: لم يتم العثور على BOT_TOKEN!")
        return

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("post", post_to_channel))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
