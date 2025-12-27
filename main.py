import os
os.system("pip install pyTelegramBotAPI")
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import threading
import time
import random
from datetime import date, timedelta

# Put your bot token directly here
TOKEN = "8206760539:AAHS7iceJT5f2GjNgXU-MiOYat7cyxeBPuU"

# Create the bot instance
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# List of romantic messages with Maryam's name (دقیقاً متن‌های خودت)
romantic_messages = [
    "مریم جونم، تو بهترین اتفاق زندگی منی. ❤️",
    "هر لحظه به فکرتم عشقم. 💕",
    "من خوشحالم که تورو دارم مریم، یادت نره هیچوقت.",
    "مریم، تو دلیل لبخند منی.",
    "مریم کوشولو، مثل یه بابا هواتو دارم، مثل داداش می‌تونی بهم تکیه کنی، مثل شوهر بهت توجه می‌کنم.",
    "مریم جونم، تو سقف رویای منی.",
    "قلبم واست میتپه مریم کوشولو.❤️",
    "مریم، تو فردای منی."
]

# Fixed start date: today (Dec 27, 2025) = day 269
FIXED_START_DATE = date(2025, 12, 27) - timedelta(days=268)

# Store last sent message index for each user (anti-repetition)
last_sent_index = {}

def get_next_message(chat_id):
    """Choose a random message different from the last one"""
    if len(romantic_messages) <= 1:
        return romantic_messages[0]
    
    last_index = last_sent_index.get(chat_id, -1)
    new_index = random.randint(0, len(romantic_messages) - 1)
    attempts = 0
    while new_index == last_index and attempts < 20:
        new_index = random.randint(0, len(romantic_messages) - 1)
        attempts += 1
    
    last_sent_index[chat_id] = new_index
    return romantic_messages[new_index]

def send_romantic_messages(chat_id):
    """Send message every hour with day counter"""
    while chat_id in active_users:
        days_in_love = (date.today() - FIXED_START_DATE).days + 1
        
        message = get_next_message(chat_id)
        full_message = f"{message}\n\nامروز روز <b>{days_in_love}</b> ام ماست نفس من.❤️"
        
        try:
            bot.send_message(chat_id, full_message)
        except:
            break
        time.sleep(3600)  # 1 hour

# Track active users
active_users = {}

# Create romantic keyboard (دکمه‌های خودت)
def create_love_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("دلم واست تنگولیده."),
        KeyboardButton("دوستت دارم 🤍"),
        KeyboardButton("بوس بوسیییی")
    )
    return markup

# --- ادمین ID (خودت) ---
ADMIN_ID = 6120112176  # ID تلگرامت (از @userinfobot گرفتی)

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name or "کاربر"
    
    # به ادمین (خودت) خبر بده که مریم /start زده + chat_id
    try:
        bot.send_message(ADMIN_ID, f"مریم جونم /start زد!\nاسم: {user_name}\nchat_id: {chat_id}")
    except:
        pass
    
    welcome_text = (
        "<b>شلام همسر عزیزتر از جونم، این برای توعه.💗</b>\n\n"
        "این بات واست پیام میفرسته تا ببینی امیرعلی همیشه حواسش بهت هست واقعنی حتی تو خوابت.\n"
        "هر وقت خواستی تموم بچه، /stop رو بزن 💜"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=create_love_keyboard())
    
    # اولین پیام عاشقانه فوری
    days_in_love = (date.today() - FIXED_START_DATE).days + 1
    first_message = get_next_message(chat_id)
    full_first = f"{first_message}\n\nامروز روز <b>{days_in_love}</b> ام ماست نفس من.🤍🤍🤍"
    bot.send_message(chat_id, full_first)
    
    # لغو ترد قبلی اگر وجود داشت
    if chat_id in active_users:
        active_users[chat_id].cancel()
    
    # شروع ارسال ساعتی
    thread = threading.Timer(3600, send_romantic_messages, args=[chat_id])
    thread.daemon = True
    thread.start()
    active_users[chat_id] = thread

@bot.message_handler(commands=['stop'])
def stop(message):
    chat_id = message.chat.id
    if chat_id in active_users:
        active_users[chat_id].cancel()
        del active_users[chat_id]
        if chat_id in last_sent_index:
            del last_sent_index[chat_id]
        bot.reply_to(message, "nدلم برات تنگ می‌شه مریم جونم.\nهر وقت دلت خواست دوباره /start بزن 😭💘", reply_markup=telebot.types.ReplyKeyboardRemove())
    else:
        bot.reply_to(message, "باید اول /start رو بزنی کوشولو")

# --- قابلیت ادمین: ارسال پیام به مریم ---
@bot.message_handler(commands=['msg'])
def admin_message(message):
    if message.from_user.id != ADMIN_ID:
        return  # فقط تو می‌تونی استفاده کنی
    
    try:
        text = message.text.split(maxsplit=1)[1]
        if not text:
            bot.reply_to(message, "بعد از /msg یه پیام بنویس 😅")
            return
        
        # ارسال به همه کاربران فعال (در عمل فقط مریم جونم)
        for cid in list(active_users.keys()):
            bot.send_message(cid, text + "\n\n— از امیرعلی ❤️")
        
        bot.reply_to(message, f"پیام فرستاده شد به مریم جونم:\n\n{text}")
    
    except IndexError:
        bot.reply_to(message, "استفاده: /msg متن پیام")
    except Exception as e:
        bot.reply_to(message, f"خطا: {str(e)}")

# --- هندل همه پیام‌ها (شامل ارسال به ادمین) ---
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name or "کاربر"
    text = message.text.lower() if message.text else ""
    
    # ارسال همه پیام‌های مریم به ادمین (خودت)
    try:
        content = message.text or '[استیکر/عکس/ویس]'
        bot.send_message(ADMIN_ID, f"پیام جدید از مریم جونم (chat_id: {chat_id}):\n{content}")
    except:
        pass
    
    # پاسخ به دکمه‌ها و کلمات خاص
    if any(phrase in text for phrase in ["دلم واست تنگولیده"]):
        bot.reply_to(message, "هر لحظه دلم واست تنگیده مریمم.")
    elif any(phrase in text for phrase in ["دوستت دارم 🤍", "عشقم", "عاشقتم"]):
        bot.reply_to(message, "همه چیز منییی؛ عاچقتم و دوستت میدالم.")
    elif any(phrase in text for phrase in ["بوس", "بوسه", "بوس بوسیییی"]):
        bot.reply_to(message, "بوس بهت عزیزدلم.")
    else:
        bot.reply_to(message, "🤍❤️🩷💚🩵💜❤️‍🔥💞💕❣️💓💘💗💖")

print("بات عاشقانه کامل برای مریم جونم شروع شد!")

bot.infinity_polling()












