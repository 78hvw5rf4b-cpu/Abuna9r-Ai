import os
import logging
import requests
import asyncio
from flask import Flask
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import time
import requests
from flask import Flask
from google import genai
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- سيرفر Flask لمنع إغلاق الاستضافة على Render ---
# --- سيرفر Flask لضمان التشغيل 24/7 ---
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "AI Bot is running!"
    return "AI Bot is alive 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

def self_ping():
    time.sleep(10)
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    while True:
        try:
            if render_url:
                requests.get(render_url, timeout=10)
            else:
                requests.get("http://127.0.0.1:10000", timeout=10)
        except Exception:
            pass
        time.sleep(300)

threading.Thread(target=run_web, daemon=True).start()
# ------------------------------------------------
threading.Thread(target=self_ping, daemon=True).start()
# ----------------------------------------

logging.basicConfig(level=logging.INFO)

# ضع معرف القناة ومعرف البوت الخاص بك هنا
CHANNEL_USERNAME = "@Abuna9r_Ai" 
BOT_USERNAME = "Abuna9r_Ai_bot"  # معرف البوت الخاص بك بدون @
# تهيئة عميل جوجل الذكي
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

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
# قاموس لحفظ جلسات المحادثة لكل مستخدم (عشان البوت يتذكر كلامك)
user_chats = {}

def get_user_chat(user_id):
    if user_id not in user_chats:
        # إنشاء جلسة دردشة جديدة متواصلة لكل مستخدم باستخدام نموذج gemini-2.0-flash
        user_chats[user_id] = client.chats.create(model="gemini-2.0-flash")
    return user_chats[user_id]

async def post_init(application: Application):
    commands = [
        BotCommand("start", "بدء المحادثة"),
        BotCommand("new", "مسح الذاكرة وبدء محادثة جديدة"),
        BotCommand("stats", "إحصائيات البوت"),
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
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # مسح الجلسة القديمة عند البدء
    if user_id in user_chats:
        del user_chats[user_id]

    await update.message.reply_text(
        "أهلاً بك في بوت الذكاء الاصطناعي! 🤖✨\nمحادثتك هنا خاصة ومستقلة تماماً ولا يراها أحد غيرك.\n\nتفضل بكتابة سؤالك:",
        reply_markup=get_main_keyboard()
        "أهلاً بك! 🤖\n"
        "أنا مساعدك الذكي الشبيه بـ ChatGPT.\n"
        "تفضل اطرح أي سؤال أو اسألني عن أي شيء، وسأتذكر سياق حديثنا!\n\n"
        "💡 ملاحظة: إذا أردت مسح الذاكرة وبدء موضوع جديد، استخدم الأمر /new"
    )

# دالة نشر منشور في القناة مرفق بزر التحويل الخصي
async def post_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text_to_send = " ".join(context.args)
    if not text_to_send:
        await update.message.reply_text("❌ اكتب النص بعد الأمر، مثال:\n`/post أهلاً بكم! اضغط على الزر للحديث مع الذكاء الاصطناعي بشكل خاص.`", parse_mode="Markdown")
        return
async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in user_chats:
        del user_chats[user_id]
    await update.message.reply_text("🧹 تم مسح الذاكرة بنجاح! نبدأ موضوع جديد، تفضل.")

    try:
        await context.bot.send_message(
            chat_id=CHANNEL_USERNAME, 
            text=text_to_send, 
            reply_markup=get_channel_post_keyboard()
        )
        await update.message.reply_text("✅ تم نشر المنشور مع زر المحادثة الخاصة في القناة!")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل النشر في القناة. التأكد من أن البوت مشرف في القناة.\nالخطأ: {e}")
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    active_sessions = len(user_chats)
    await update.message.reply_text(f"📊 عدد المحادثات النشطة حالياً في الذاكرة: {active_sessions}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    status_msg = await update.message.reply_text("🤖 جاري التفكير والإجابة...")
    
    ai_reply = await asyncio.to_thread(ask_gemini_ai, text)
    await status_msg.edit_text(ai_reply, reply_markup=get_main_keyboard())
    user_id = update.effective_user.id
    user_message = update.message.text

    if not user_message:
        return

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    # إرسال رسالة "جاري التفكير..."
    msg = await update.message.reply_text("🧠 جاري الصياغة...")

    if query.data == "cmd_start":
        await query.message.reply_text("أهلاً بك! اكتب سؤالك هنا وسأجيبك فوراً.", reply_markup=get_main_keyboard())
    try:
        # الحصول على جلسة المحادثة الخاصة بالمستخدم (تحتفظ بالذاكرة)
        chat = get_user_chat(user_id)

        # إرسال الرسالة والحصول على الرد مع أخذ المحادثات السابقة بعين الاعتبار
        response = await asyncio.to_thread(chat.send_message, user_message)
        answer = response.text

        # تقسيم الرسالة إذا كانت طويلة جداً لتجنب حدود تليجرام
        if len(answer) > 4000:
            chunks = [answer[i:i+4000] for i in range(0, len(answer), 4000)]
            await msg.edit_text(chunks[0])
            for chunk in chunks[1:]:
                await update.message.reply_text(chunk)
        else:
            await msg.edit_text(answer)

    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        await msg.edit_text(f"❌ حدث خطأ أثناء الاتصال بالذكاء الاصطناعي:\n`{str(e)}`", parse_mode="Markdown")

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("خطأ: لم يتم العثور على BOT_TOKEN!")
        return

    application = Application.builder().token(token).build()
    application = Application.builder().token(token).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("post", post_to_channel))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(CommandHandler("new", new_chat))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()
