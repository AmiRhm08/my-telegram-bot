import os
os.system("pip install pyTelegramBotAPI")
os.system("pip install --upgrade pip")
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import threading
import time
import random
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

last_sent_index = {}
active_users = set()
maryam_waiting = set()

LOVE_KEYBOARD = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
LOVE_KEYBOARD.add(
    KeyboardButton("دلم واست تنگولیده."),
    KeyboardButton("دوستت دارم 🤍"),
    KeyboardButton("بوس بوسیییی")
)

ADMIN_ID = 6120112176
MARYAM_CHAT_ID = 2045238581
TEST_ID = 8101517449
ALLOWED_USERS = {MARYAM_CHAT_ID, ADMIN_ID, TEST_ID}

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

# لوپ ارسال پیام هر ساعت — پایدار و ضدکرش
def background_sender():
    while True:
        try:
            for chat_id in list(active_users):
                try:
                    message = get_next_message(chat_id)
                    bot.send_message(chat_id, message)
                except Exception as e:
                    print(f"خطا در ارسال به {chat_id}: {e}")
                    continue
            
            time.sleep(3600)  # هر ساعت یک پیام
        
        except Exception as e:
            print(f"خطا در لوپ اصلی: {e}")
            time.sleep(60)  # صبر و ادامه

threading.Thread(target=background_sender, daemon=True).start()

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name or "کاربر"
    
    if chat_id not in ALLOWED_USERS:
        bot.send_message(chat_id, "این بات واسه‌ی تو نیست مزاحم نشو.")
        try:
            bot.send_message(ADMIN_ID, f"کسی سعی کرد بات رو استارت بزنه و بلاک شد!\nاسم: {user_name}\nchat_id: {chat_id}")
        except:
            pass
        return
    
    try:
        bot.send_message(ADMIN_ID, f"کاربر مجاز /start زد!\nاسم: {user_name}\nchat_id: {chat_id}")
    except:
        pass
    
    if chat_id == MARYAM_CHAT_ID:
        bot.send_message(chat_id, "آیا تو مریمی؟")
        maryam_waiting.add(chat_id)
        return
    
    welcome_text = (
        "<b>شلام همسر عزیزتر از جونم، این برای توعه.💗</b>\n\n"
        "این بات واست پیام میفرسته تا ببینی امیرعلی همیشه حواسش بهت هست واقعنی حتی تو خوابت.\n"
        "هر وقت خواستی تموم بچه، /stop رو بزن 💜"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=LOVE_KEYBOARD)
    
    first_message = get_next_message(chat_id)
    bot.send_message(chat_id, first_message)
    
    active_users.add(chat_id)

@bot.message_handler(commands=['stop'])
def stop(message):
    chat_id = message.chat.id
    
    if chat_id not in ALLOWED_USERS:
        bot.reply_to(message, "این بات واسه‌ی تو نیست مزاحم نشو.")
        return
    
    active_users.discard(chat_id)
    last_sent_index.pop(chat_id, None)
    maryam_waiting.discard(chat_id)
    
    bot.reply_to(message, "دلم برات تنگ می‌شه مریم جونم.\nهر وقت دلت خواست دوباره /start بزن 😭💘")

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
    
    if chat_id in maryam_waiting:
        special_message = "از آشنایی باهات خوشبختم، سازنده‌م خیلی تعریفتو کرده پیشم و گفته که تو همه‌چیزشی، خیلی عجیب عاشقته سازنده‌م، بهت حسودی میکنم. بهم گفته بهت بگم این باتو ساخته تا یه بخش کوچیکی از علاقه‌ش بهتو ببینی."
        bot.send_message(chat_id, special_message)
        
        welcome_text = (
            "<b>شلام همسر عزیزتر از جونم، این برای توعه.💗</b>\n\n"
            "این بات واست پیام میفرسته تا ببینی امیرعلی همیشه حواسش بهت هست واقعنی حتی تو خوابت.\n"
            "هر وقت خواستی تموم بچه، /stop رو بزن 💜"
        )
        bot.send_message(chat_id, welcome_text, reply_markup=LOVE_KEYBOARD)
        
        time.sleep(3)
        first_message = get_next_message(chat_id)
        bot.send_message(chat_id, first_message)
        
        active_users.add(chat_id)
        maryam_waiting.remove(chat_id)
        return
    
    # فوروارد پیام به ادمین — فقط یوزرنیم یا اسم + پیام + خط فاصله
    try:
        content = message.text or "None"
        if message.from_user.username:
            sender = f"@{message.from_user.username}"
        else:
            sender = message.from_user.first_name or "کاربر"
        
        forward_text = f"{sender}:\n{content}\n---"
        bot.send_message(ADMIN_ID, forward_text)
    except:
        pass
    
    text = message.text.lower() if message.text else ""
    
    if any(phrase in text for phrase in ["بوس", "بوسه", "بوس بوسیییی"]):
        try:
            voice_file_id = "AwACAgQAAxkBAAEZzXVpVMMB1XPD8Kmc-jxLGEXT9SMfGAACZB0AAvLHqVJMkAepzgWEwDgE"
            bot.send_voice(chat_id, voice_file_id)
        except:
            bot.reply_to(message, "بوس بهت عزیزدلم.")
    
    elif "دلم واست تنگولیده" in text:
        romantic_reply = get_next_message(chat_id)
        bot.reply_to(message, f"{romantic_reply}\n\nدل منم هر لحظه برات تنگولیده نینیم.❤️")
    
    elif any(phrase in text for phrase in ["دوستت دارم 🤍", "عشقم", "عاشقتم"]):
        bot.reply_to(message, "همه چیز منییی؛ عاچقتم و دوستت میدالم.")
    
    else:
        bot.reply_to(message, "🤍❤️🩷💚🩵💜❤️‍🔥💞💕❣️💓💘💗💖")

print("بات عاشقانه — هر ساعت یک پیام عاشقانه — شروع شد!")

bot.infinity_polling(interval=3)