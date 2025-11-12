import telebot
import sqlite3
import os
from datetime import datetime
import logging
import requests

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)

# قراءة المتغيرات من البيئة
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
RENDER_URL = os.environ.get('RENDER_URL')  # أضف هذا المتغير في إعدادات Render

if not BOT_TOKEN:
    logging.error("❌ BOT_TOKEN not set")
    exit(1)

if not CHANNEL_ID:
    logging.error("❌ CHANNEL_ID not set")
    exit(1)

if not RENDER_URL:
    logging.error("❌ RENDER_URL not set (مثلاً my-telegram--bot.onrender.com)")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

def init_db():
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id INTEGER PRIMARY KEY, 
                      first_name TEXT,
                      username TEXT,
                      phone TEXT,
                      created_at TIMESTAMP)''')
        conn.commit()
        conn.close()
        logging.info("✅ Database initialized")
    except Exception as e:
        logging.error(f"Database error: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        user = message.from_user
        logging.info(f"📨 Message from {user.id} - {user.first_name}")
        
        save_user_info(user)
        forward_to_channel(message, user)
        
        bot.reply_to(message, "✅ تم استلام رسالتك وسيتم الرد عليها قريباً")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        bot.reply_to(message, "❌ حدث خطأ، حاول مرة أخرى")

def save_user_info(user):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO users 
                     (user_id, first_name, username, phone, created_at) 
                     VALUES (?, ?, ?, ?, ?)''',
                  (user.id, user.first_name, user.username, getattr(user, 'phone_number', None), datetime.now()))
        conn.commit()
        conn.close()
        logging.info(f"✅ Saved user info: {user.id}")
    except Exception as e:
        logging.error(f"Database error: {e}")

def forward_to_channel(message, user):
    try:
        user_info = f"\n\n---\n🔒 معلومات سرية:\n👤 الاسم: {user.first_name}\n🆔 ID: {user.id}"
        if user.username:
            user_info += f"\n📱 username: @{user.username}"
        
        if message.text:
            full_message = message.text + user_info
            bot.send_message(CHANNEL_ID, full_message)
            logging.info("✅ Text forwarded to channel")
        
        elif message.photo:
            caption = (message.caption or "") + user_info
            bot.send_photo(CHANNEL_ID, message.photo[-1].file_id, caption=caption)
            logging.info("✅ Photo forwarded to channel")
        
        elif message.video:
            caption = (message.caption or "") + user_info
            bot.send_video(CHANNEL_ID, message.video.file_id, caption=caption)
            logging.info("✅ Video forwarded to channel")
        
        elif message.document:
            caption = (message.caption or "") + user_info
            bot.send_document(CHANNEL_ID, message.document.file_id, caption=caption)
            logging.info("✅ Document forwarded to channel")
            
    except Exception as e:
        logging.error(f"Forward error: {e}")

# -----------------------------
# التشغيل على Render باستخدام Webhook
# -----------------------------
if __name__ == "__main__":
    logging.info("🤖 Starting bot...")
    init_db()

    # حذف أي Webhook سابق لتجنب التعارض
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")

    # إنشاء Webhook جديد
    webhook_url = f"https://{RENDER_URL}/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    logging.info(f"🌐 Webhook set to {webhook_url}")

    from flask import Flask, request

    app = Flask(__name__)

    @app.route(f"/{BOT_TOKEN}", methods=['POST'])
    def webhook():
        update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
        bot.process_new_updates([update])
        return "OK", 200

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
