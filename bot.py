import telebot
import sqlite3
import os
from datetime import datetime

# قراءة المتغيرات من البيئة
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

if not BOT_TOKEN or not CHANNEL_ID:
    raise ValueError("❌ Please set BOT_TOKEN and CHANNEL_ID in Railway Variables")

bot = telebot.TeleBot(BOT_TOKEN)

# إنشاء قاعدة بيانات
def init_db():
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

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'voice'])
def handle_messages(message):
    try:
        user = message.from_user
        
        # حفظ معلومات المستخدم
        save_user_info(user)
        
        # إرسال الرسالة إلى القناة
        forward_to_channel(message, user)
        
        # الرد على المستخدم
        bot.reply_to(message, "✅ تم استلام رسالتك وسيتم الرد عليها قريباً")
        
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "❌ حدث خطأ، حاول مرة أخرى")

def save_user_info(user):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO users 
                     (user_id, first_name, username, phone, created_at) 
                     VALUES (?, ?, ?, ?, ?)''',
                  (user.id, user.first_name, user.username, user.phone_number, datetime.now()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

def forward_to_channel(message, user):
    try:
        # معلومات المرسل السرية
        user_info = f"\n\n---\n🔒 معلومات سرية:\n👤 الاسم: {user.first_name}\n🆔 ID: {user.id}"
        if user.username:
            user_info += f"\n📱 username: @{user.username}"
        
        # معالجة不同类型的 الرسائل
        if message.text:
            # رسالة نصية
            full_message = message.text + user_info
            bot.send_message(CHANNEL_ID, full_message)
        
        elif message.photo:
            # صورة
            caption = (message.caption or "") + user_info
            bot.send_photo(CHANNEL_ID, message.photo[-1].file_id, caption=caption)
        
        elif message.video:
            # فيديو
            caption = (message.caption or "") + user_info
            bot.send_video(CHANNEL_ID, message.video.file_id, caption=caption)
        
        elif message.document:
            # ملف
            caption = (message.caption or "") + user_info
            bot.send_document(CHANNEL_ID, message.document.file_id, caption=caption)
        
        elif message.voice:
            # رسالة صوتية
            bot.send_voice(CHANNEL_ID, message.voice.file_id, caption=user_info)
            
    except Exception as e:
        print(f"Forward error: {e}")

# التشغيل
if __name__ == "__main__":
    init_db()
    print("🤖 Bot is running...")
    bot.polling(none_stop=True)
