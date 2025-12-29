import os
os.system("pip install pyTelegramBotAPI")
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import threading
import time
import random
from datetime import date, timedelta
import datetime

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
    "مریم، تو فردای منی.",
    "تو قشنگی مثل شکلایی که ابرا میسازن.",
    "منو توییم هرچیم بشه.\n ماباهمیم هرچیم بشه.\n مال همیم هرچیم بشه.\n حتی اون آسمون از اون بالا بیاد زمین.",
    "دنیارو نمیخوام اگه تو نباشی.",
    "فکرشم نکن، خسته شم ازت.\nفکرشم نکن دست بکشم ازت.\nفکرشم نکن تورو نبینمت یه‌روز.\nمن به عشق دیدنت نفس میکشم فقط.",
    "نگاه تو روشن شبای بی‌چراغم.",
    "مریم و امیرعلی قراره یه خونه داشته باشن که فقط مال اون دو تا باشه:)",
    "یادت نره ما باهمیم:)",
    "قفل چشاتم.",
    "چشمات بوسیدنیه، گردنت بوسیدنیه، دستات بوسیدنیه، عطر تنت بوسیدنیه، نفسات بوسیدنیه، مهربونیِ تهِ قلبت بوسیدنیه، موهات بوسیدنیه. کلا تو بوسیدنی‌ترین موجودِ این کره خاکی‌ای.",
    "من سر تو حسود نیستم ، سرتو یه خودخواه روانی سادیسمی از خود راضیم که می‌خوام فقط مال من باشی.",
    "دلم میخوادت.",
    "اگه حس کردی هرجایی داری کم میاری یا هرچی، زودی بدو بیا پیشم چون من پشتتم.",
    "تورو از همه‌ی همه‌ی دنیا بیشتر دوستت دالم نفس بابایی.",
    "دوستت دارم تنها ماهِ آسمونِ قلبم:)",
    "باهم این سختیا رو تحمل میکنیم عزیزم، دنیا بغل های زیادی رو بهمون بدهکاره.",
    "میقام تورو بگیلم."
    
]

# امروز ۲۹ دسامبر ۲۰۲۵ = روز ۲۷۱
FIXED_START_DATE = date(2025, 12, 29) - timedelta(days=270)

last_sent_index = {}
active_users = {}
daily_message_sent = {}

LOVE_KEYBOARD = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
LOVE_KEYBOARD.add(
    KeyboardButton("دلم واست تنگولیده."),
    KeyboardButton("دوستت دارم 🤍"),
    KeyboardButton("بوس بوسیییی")
)

ADMIN_ID = 6120112176  # آیدی خودت (ادمین)
MARYAM_CHAT_ID = 2045238581  # آیدی مریم جونم

ALLOWED_USERS = {MARYAM_CHAT_ID, ADMIN_ID}  # فقط این دو نفر دسترسی کامل دارن

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
        current_time = datetime.datetime.now()
        current_date = date.today()
        days_in_love = (current_date - FIXED_START_DATE).days + 1
        
        today_sent = daily_message_sent.get(chat_id, None) == current_date
        
        if current_time.hour == 23 and current_time.minute == 31 and not today_sent:
            day_message = f"امروز روز <b>{days_in_love}</b> ام ماست نفس من.❤️\nشب بخیر عشقم، خوابای قشنگ ببینی 😘"
            try:
                bot.send_message(chat_id, day_message)
                daily_message_sent[chat_id] = current_date
            except:
                pass
        else:
            message = get_next_message(chat_id)
            try:
                bot.send_message(chat_id, message)
            except:
                pass
        
        time.sleep(3600)

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name or "کاربر"
    
    # اگر نه مریم باشه و نه ادمین → بلاک کن
    if chat_id not in ALLOWED_USERS:
        bot.send_message(chat_id, "این بات واسه‌ی تو نیست مزاحم نشو.")
        try:
            bot.send_message(ADMIN_ID, f"کسی سعی کرد بات رو استارت بزنه و بلاک شد!\nاسم: {user_name}\nchat_id: {chat_id}")
        except:
            pass
        return
    
    # برای مریم و ادمین (تو) — دسترسی کامل
    try:
        bot.send_message(ADMIN_ID, f"کاربر مجاز /start زد!\nاسم: {user_name}\nchat_id: {chat_id}")
    except:
        pass
    
    welcome_text = (
        "<b>شلام همسر عزیزتر از جونم، این برای توعه.💗</b>\n\n"
        "این بات واست پیام میفرسته تا ببینی امیرعلی همیشه حواسش بهت هست واقعنی حتی تو خوابت.\n"
        "هر وقت خواستی تموم بچه، /stop رو بزن 💜"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=LOVE_KEYBOARD)
    
    first_message = get_next_message(chat_id)
    bot.send_message(chat_id, first_message)
    
    if chat_id in active_users:
        active_users[chat_id].cancel()
    
    thread = threading.Timer(10, send_romantic_messages, args=[chat_id])
    thread.daemon = True
    thread.start()
    active_users[chat_id] = thread

@bot.message_handler(commands=['stop'])
def stop(message):
    chat_id = message.chat.id
    
    if chat_id not in ALLOWED_USERS:
        bot.reply_to(message, "این بات واسه‌ی تو نیست مزاحم نشو.")
        return
    
    if chat_id in active_users:
        active_users[chat_id].cancel()
        del active_users[chat_id]
        if chat_id in last_sent_index:
            del last_sent_index[chat_id]
        if chat_id in daily_message_sent:
            del daily_message_sent[chat_id]
        bot.reply_to(message, "nدلم برات تنگ می‌شه مریم جونم.\nهر وقت دلت خواست دوباره /start بزن 😭💘", reply_markup=telebot.types.ReplyKeyboardRemove())
    else:
        bot.reply_to(message, "باید اول /start رو بزنی کوشولو")

@bot.message_handler(commands=['msg'])
def admin_message(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "استفاده: /msg <chat_id> متن پیام\nمثال: /msg 987654321 سلام نفس من ❤️")
            return
        
        target_chat_id = int(parts[1])
        text = parts[2]
        
        # فقط به کاربران مجاز (مریم یا خودت) پیام بفرست
        if target_chat_id not in ALLOWED_USERS:
            bot.reply_to(message, "فقط می‌تونی به مریم جونم یا خودت پیام بدی!")
            return
        
        bot.send_message(target_chat_id, text + "\n\n— از امیرعلی ❤️")
        bot.reply_to(message, f"پیام با موفقیت فرستاده شد به chat_id: {target_chat_id}\n\n{text}")
    
    except ValueError:
        bot.reply_to(message, "chat_id باید عدد باشه!")
    except Exception as e:
        bot.reply_to(message, f"خطا در ارسال: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    
    if chat_id not in ALLOWED_USERS:
        bot.send_message(chat_id, "این بات واسه‌ی تو نیست مزاحم نشو.")
        return
    
    username = message.from_user.username or "بدون یوزرنیم"
    first_name = message.from_user.first_name or "نامشخص"
    display_name = f"@{username}" if message.from_user.username else first_name
    
    try:
        content = message.text or "None"
        bot.send_message(ADMIN_ID, f"{display_name} (chat_id: {chat_id}):\n{content}")
    except:
        pass
    
    text = message.text.lower() if message.text else ""
    
    # دکمه یا متن "بوس بوسیییی" یا "بوس" → ویس بوس بفرست
    if any(phrase in text for phrase in ["بوس", "بوسه", "بوس بوسیییی"]):
        try:
            # <<<--- file_id ویس بوس خودت رو اینجا بذار
            voice_file_id = "AwACAgQAAxkBAAEZwd9pUigjHTi30H-dGJgPzuQHlOMojAACtRoAAk2bkFKfS-ri4Y6g9DYE"  # مثلاً CQACAgQAAxkBAAIB...
            bot.send_voice(chat_id, voice_file_id)
        except:
            bot.reply_to(message, "بوس بهت عزیزدلم.")  # اگر ویس نشد، متن بفرست
    
    # دکمه "دلم واست تنگولیده."
    elif "دلم واست تنگولیده" in text:
        romantic_reply = get_next_message(chat_id)
        bot.reply_to(message, f"{romantic_reply}\n\nدل منم هر لحظه برات تنگولیده نینیم.❤️")
    
    # دکمه "دوستت دارم 🤍"
    elif any(phrase in text for phrase in ["دوستت دارم 🤍", "عشقم", "عاشقتم"]):
        bot.reply_to(message, "همه چیز منییی؛ عاچقتم و دوستت میدالم.")
    
    # پیام پیش‌فرض
    else:
        bot.reply_to(message, "🤍❤️🩷💚🩵💜❤️‍🔥💞💕❣️💓💘💗💖")
print("بات خصوصی — فقط برای مریم جونم و ادمین — شروع شد!")

bot.infinity_polling()



