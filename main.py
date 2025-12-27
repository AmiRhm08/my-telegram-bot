import os
os.system("pip install pyTelegramBotAPI")
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import threading
import time
import random
from datetime import date, timedelta

TOKEN = "8206760539:AAHS7iceJT5f2GjNgXU-MiOYat7cyxeBPuU"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

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

FIXED_START_DATE = date(2025, 12, 27) - timedelta(days=268)

last_sent_index = {}

def get_next_message(chat_id):
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
    while chat_id in active_users:
        days_in_love = (date.today() - FIXED_START_DATE).days + 1
        message = get_next_message(chat_id)
        full_message = f"{message}\n\nامروز روز <b>{days_in_love}</b> ام ماست نفس من.❤️"
        
        try:
            bot.send_message(chat_id, full_message)
        except:
            break
        time.sleep(3600)

active_users = {}

def create_love_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("دلم واست تنگولیده."),
        KeyboardButton("دوستت دارم 🤍"),
        KeyboardButton("بوس بوسیییی")
    )
    return markup

ADMIN_ID = 6120112176

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name or "کاربر"
    
    try:
        bot.send_message(ADMIN_ID, f"کاربر /start زد!\nاسم: {user_name}\nchat_id: {chat_id}")
    except:
        pass
    
    welcome_text = (
        "<b>شلام همسر عزیزتر از جونم، این برای توعه.💗</b>\n\n"
        "این بات واست پیام میفرسته تا ببینی امیرعلی همیشه حواسش بهت هست واقعنی حتی تو خوابت.\n"
        "هر وقت خواستی تموم بچه، /stop رو بزن 💜"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=create_love_keyboard())
    
    days_in_love = (date.today() - FIXED_START_DATE).days + 1
    first_message = get_next_message(chat_id)
    full_first = f"{first_message}\n\nامروز روز <b>{days_in_love}</b> ام ماست نفس من.🤍🤍🤍"
    bot.send_message(chat_id, full_first)
    
    if chat_id in active_users:
        active_users[chat_id].cancel()
    
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

# --- قابلیت ادمین: ارسال پیام به chat_id خاص ---
@bot.message_handler(commands=['msg'])
def admin_message(message):
    if message.from_user.id != ADMIN_ID:
        return  # فقط تو می‌تونی استفاده کنی
    
    try:
        # فرمت: /msg <chat_id> متن پیام
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "استفاده: /msg <chat_id> متن پیام\nمثال: /msg 987654321 سلام نفس من ❤️")
            return
        
        target_chat_id = int(parts[1])
        text = parts[2]
        
        bot.send_message(target_chat_id, text + "\n\n— از امیرعلی ❤️")
        bot.reply_to(message, f"پیام با موفقیت فرستاده شد به chat_id: {target_chat_id}\n\n{text}")
    
    except ValueError:
        bot.reply_to(message, "chat_id باید عدد باشه!")
    except Exception as e:
        bot.reply_to(message, f"خطا در ارسال: {str(e)}")

# --- هندل همه پیام‌ها ---
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    username = message.from_user.username or "بدون یوزرنیم"
    first_name = message.from_user.first_name or "نامشخص"
    display_name = f"@{username}" if message.from_user.username else first_name
    
    try:
        content = message.text or "None"
        bot.send_message(ADMIN_ID, f"{display_name} (chat_id: {chat_id}):\n{content}")
    except:
        pass
    
    text = message.text.lower() if message.text else ""
    
    if any(phrase in text for phrase in ["دلم واست تنگولیده"]):
        bot.reply_to(message, "هر لحظه دلم واست تنگیده مریمم.")
    elif any(phrase in text for phrase in ["دوستت دارم 🤍", "عشقم", "عاشقتم"]):
        bot.reply_to(message, "همه چیز منییی؛ عاچقتم و دوستت میدالم.")
    elif any(phrase in text for phrase in ["بوس", "بوسه", "بوس بوسیییی"]):
        bot.reply_to(message, "بوس بهت عزیزدلم.")
    else:
        bot.reply_to(message, "🤍❤️🩷💚🩵💜❤️‍🔥💞💕❣️💓💘💗💖")
# --- گرفتن ری‌اکشن‌های کاربر روی پیام بات ---
@bot.message_reaction()
def handle_reaction(reaction):
    chat_id = reaction.chat.id
    user = reaction.user
    if user is None:
        return  # گاهی کاربر ناشناسه
    
    user_name = user.first_name or "کاربر"
    username = f"@{user.username}" if user.username else ""
    display_name = f"{username} ({user_name})".strip()
    
    new_reactions = reaction.new_reaction
    if not new_reactions:
        return
    
    # گرفتن ایموجی‌های ری‌اکشن (ممکنه چندتا باشه)
    emojis = []
    for r in new_reactions:
        if r.type == "emoji":
            emojis.append(r.emoji)
    
    if not emojis:
        return
    
    # گرفتن متن پیام بات که ری‌اکشن روش گذاشته شده (اگر ممکن باشه)
    try:
        msg = bot.get_messages(chat_id, reaction.message_id)
        message_text = msg.text or msg.caption or "[عکس/استیکر/ویس]"
    except:
        message_text = "[پیام پیدا نشد]"
    
    # ارسال نوتیفیکیشن به ادمین (تو)
    try:
        reaction_text = " ".join(emojis)
        bot.send_message(ADMIN_ID, f"مریم جونم ری‌اکشن گذاشت: {reaction_text}\n"
                                  f"روی پیام: {message_text}\n"
                                  f"کاربر: {display_name} (chat_id: {chat_id})")
    except:
        pass
        
print("بات عاشقانه کامل برای مریم جونم شروع شد!")

bot.infinity_polling()














