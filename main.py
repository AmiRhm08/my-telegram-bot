import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import threading
import time
import random
import sqlite3

# ================== تنظیمات ==================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN تنظیم نشده")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

ADMIN_ID = 6120112176
MARYAM_CHAT_ID = 2045238581
TEST_ID = 8101517449
ALLOWED_USERS = {MARYAM_CHAT_ID, ADMIN_ID, TEST_ID}

DB_PATH = "/data/users.db"


# ================== دیتابیس ==================
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS active_users (
    chat_id INTEGER PRIMARY KEY
)
""")
conn.commit()

def load_active_users():
    cur.execute("SELECT chat_id FROM active_users")
    return {row[0] for row in cur.fetchall()}

def add_active_user(chat_id):
    cur.execute("INSERT OR IGNORE INTO active_users (chat_id) VALUES (?)", (chat_id,))
    conn.commit()

def remove_active_user(chat_id):
    cur.execute("DELETE FROM active_users WHERE chat_id = ?", (chat_id,))
    conn.commit()

# ================== داده‌ها ==================
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
maryam_waiting = set()

active_users = load_active_users()
print("کاربران لود شدند:", active_users)

# ================== کیبورد ==================
LOVE_KEYBOARD = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
LOVE_KEYBOARD.add(
    KeyboardButton("دلم واست تنگولیده."),
    KeyboardButton("دوستت دارم 🤍"),
    KeyboardButton("بوس بوسیییی")
)

# ================== توابع ==================
def get_next_message(chat_id):
    last = last_sent_index.get(chat_id, -1)
    idx = random.randint(0, len(romantic_messages) - 1)
    while idx == last:
        idx = random.randint(0, len(romantic_messages) - 1)
    last_sent_index[chat_id] = idx
    return romantic_messages[idx]

def background_sender():
    while True:
        try:
            for chat_id in list(active_users):
                try:
                    bot.send_message(chat_id, get_next_message(chat_id))
                except Exception as e:
                    print(f"خطا در ارسال به {chat_id}: {e}")
            time.sleep(3600)  # هر ساعت
        except Exception as e:
            print(f"خطای کلی لوپ: {e}")
            time.sleep(60)

threading.Thread(target=background_sender, daemon=True).start()

# ================== هندلرها ==================
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    name = message.from_user.first_name or "کاربر"

    if chat_id not in ALLOWED_USERS:
        bot.send_message(chat_id, "این بات واسه‌ی تو نیست مزاحم نشو.")
        try:
            bot.send_message(ADMIN_ID, f"کسی استارت زد!\nاسم: {name}\nchat_id: {chat_id}")
        except:
            pass
        return

    if chat_id == MARYAM_CHAT_ID:
        bot.send_message(chat_id, "آیا تو مریمی؟")
        maryam_waiting.add(chat_id)
        return

    bot.send_message(
        chat_id,
        "<b>شلام همسر عزیزتر از جونم، این برای توعه.💗</b>\n\n"
        "این بات واست پیام میفرسته تا ببینی امیرعلی همیشه حواسش بهت هست واقعنی حتی تو خوابت.\n"
        "هر وقت خواستی تموم بچه، /stop رو بزن 💜",
        reply_markup=LOVE_KEYBOARD
    )

    bot.send_message(chat_id, get_next_message(chat_id))
    active_users.add(chat_id)
    add_active_user(chat_id)

@bot.message_handler(commands=["stop"])
def stop(message):
    chat_id = message.chat.id
    active_users.discard(chat_id)
    maryam_waiting.discard(chat_id)
    last_sent_index.pop(chat_id, None)
    remove_active_user(chat_id)
    bot.reply_to(message, "دلم برات تنگ می‌شه مریم جونم.\nهر وقت دلت خواست دوباره /start بزن 😭💘")

@bot.message_handler(commands=['msg'])
def admin_message(message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(
                message,
                "استفاده: /msg <chat_id> متن پیام\nمثال: /msg 987654321 سلام نفس من ❤️"
            )
            return

        target_chat_id = int(parts[1])
        text = parts[2]

        if target_chat_id not in ALLOWED_USERS:
            bot.reply_to(message, "فقط می‌تونی به مریم جونم یا خودت پیام بدی!")
            return

        bot.send_message(
            target_chat_id,
            text + "\n\n— از امیرعلی ❤️"
        )

        bot.reply_to(
            message,
            f"پیام با موفقیت فرستاده شد به chat_id: {target_chat_id}\n\n{text}"
        )

    except ValueError:
        bot.reply_to(message, "chat_id باید عدد باشه!")
    except Exception as e:
        bot.reply_to(message, f"خطا در ارسال: {str(e)}")

@bot.message_handler(func=lambda m: True)
def all_messages(message):
    chat_id = message.chat.id

    if chat_id not in ALLOWED_USERS:
        bot.send_message(chat_id, "این بات واسه‌ی تو نیست مزاحم نشو.")
        return

    if chat_id in maryam_waiting:
        bot.send_message(chat_id,
            "از آشنایی باهات خوشبختم، سازنده‌م خیلی تعریفتو کرده پیشم و گفته که تو همه‌چیزشی، خیلی عجیب عاشقته سازنده‌م، بهت حسودی میکنم. بهم گفته بهت بگم این باتو ساخته تا یه بخش کوچیکی از علاقه‌ش بهتو ببینی."
        )
        time.sleep(2)
        bot.send_message(chat_id, get_next_message(chat_id), reply_markup=LOVE_KEYBOARD)
        active_users.add(chat_id)
        add_active_user(chat_id)
        maryam_waiting.remove(chat_id)
        return

    text = (message.text or "").lower()

    if "بوس" in text:
        try:
            bot.send_voice(chat_id, "AwACAgQAAxkBAAEZzXVpVMMB1XPD8Kmc-jxLGEXT9SMfGAACZB0AAvLHqVJMkAepzgWEwDgE")
        except:
            bot.reply_to(message, "بوس بهت عزیزدلم.")

    elif "دلم واست تنگولیده" in text:
        bot.reply_to(message, f"{get_next_message(chat_id)}\n\nدل منم هر لحظه برات تنگولیده نینیم.❤️")

    elif "دوستت دارم" in text or "عشقم" in text:
        bot.reply_to(message, "همه چیز منییی؛ عاچقتم و دوستت میدالم.")

    else:
        bot.reply_to(message, "🤍❤️🩷💚🩵💜❤️‍🔥💞💕❣️💓💘💗💖")

print("بات عاشقانه با ذخیره کاربر روشن شد ❤️")

bot.delete_webhook(drop_pending_updates=True)
while True:
    try:
        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60,
            skip_pending=True
        )
    except Exception as e:
        print("Polling crashed:", e)
        time.sleep(5)

