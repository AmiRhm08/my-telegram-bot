import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import threading
import time
import random
import sqlite3
from datetime import datetime

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
AUTO_SEND_ENABLED = True

# ================== دیتابیس ==================
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS active_users (chat_id INTEGER PRIMARY KEY)")
conn.commit()

def load_active_users():
    cur.execute("SELECT chat_id FROM active_users")
    return {r[0] for r in cur.fetchall()}

def add_active_user(chat_id):
    cur.execute("INSERT OR IGNORE INTO active_users VALUES (?)", (chat_id,))
    conn.commit()

def remove_active_user(chat_id):
    cur.execute("DELETE FROM active_users WHERE chat_id = ?", (chat_id,))
    conn.commit()

active_users = load_active_users()
maryam_waiting = set()
last_sent_index = {}

# ================== لاگ ==================
def log_to_admin(text):
    try:
        bot.send_message(ADMIN_ID, text)
    except:
        pass

daily_stats = {"messages": 0, "starts": 0}

# ================== پیام‌ها ==================
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

def get_next_message(chat_id):
    last = last_sent_index.get(chat_id, -1)
    idx = random.randint(0, len(romantic_messages) - 1)
    while idx == last:
        idx = random.randint(0, len(romantic_messages) - 1)
    last_sent_index[chat_id] = idx
    return romantic_messages[idx]

# ================== کیبورد ==================
LOVE_KEYBOARD = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
LOVE_KEYBOARD.add(
    KeyboardButton("دلم واست تنگولیده."),
    KeyboardButton("دوستت دارم 🤍"),
    KeyboardButton("بوس بوسیییی")
)

# ================== ارسال خودکار ==================
def background_sender():
    while True:
        try:
            if not AUTO_SEND_ENABLED:
                time.sleep(30)
                continue

            for chat_id in list(active_users):
                try:
                    bot.send_message(chat_id, get_next_message(chat_id))
                    time.sleep(1)
                except:
                    pass
            time.sleep(3600)
        except:
            time.sleep(60)

threading.Thread(target=background_sender, daemon=True).start()

# ================== گزارش روزانه ==================
def daily_report():
    while True:
        now = datetime.now()
        if now.hour == 23 and now.minute == 59:
            try:
                bot.send_message(
                    ADMIN_ID,
                    f"🧾 گزارش امروز\n"
                    f"🚀 استارت‌ها: {daily_stats['starts']}\n"
                    f"📩 پیام‌ها: {daily_stats['messages']}"
                )
                daily_stats["starts"] = 0
                daily_stats["messages"] = 0
            except:
                pass
            time.sleep(60)
        time.sleep(20)

threading.Thread(target=daily_report, daemon=True).start()

# ================== دستورات ادمین ==================
@bot.message_handler(commands=["status"])
def status_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    bot.send_message(
        ADMIN_ID,
        f"📊 وضعیت بات\n"
        f"🟢 ارسال خودکار: {'فعال' if AUTO_SEND_ENABLED else 'متوقف'}\n"
        f"👥 کاربران فعال: {len(active_users)}"
    )

@bot.message_handler(commands=["users"])
def users_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    if not active_users:
        bot.send_message(ADMIN_ID, "هیچ کاربر فعالی وجود ندارد.")
        return
    bot.send_message(ADMIN_ID, "👥 کاربران فعال:\n" + "\n".join(str(u) for u in active_users))

@bot.message_handler(commands=["pause"])
def pause_cmd(m):
    global AUTO_SEND_ENABLED
    if m.from_user.id == ADMIN_ID:
        AUTO_SEND_ENABLED = False
        bot.send_message(ADMIN_ID, "⏸ ارسال خودکار متوقف شد.")

@bot.message_handler(commands=["resume"])
def resume_cmd(m):
    global AUTO_SEND_ENABLED
    if m.from_user.id == ADMIN_ID:
        AUTO_SEND_ENABLED = True
        bot.send_message(ADMIN_ID, "▶️ ارسال خودکار فعال شد.")

@bot.message_handler(commands=["backup"])
def backup_cmd(m):
    if m.from_user.id == ADMIN_ID:
        bot.send_document(ADMIN_ID, open(DB_PATH, "rb"))

@bot.message_handler(commands=["msg"])
def admin_msg(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, cid, text = m.text.split(maxsplit=2)
        bot.send_message(int(cid), text + "\n\n— از امیرعلی ❤️")
    except:
        bot.reply_to(m, "فرمت: /msg chat_id متن")

# ================== استارت / استاپ ==================
@bot.message_handler(commands=["start"])
def start(m):
    daily_stats["starts"] += 1
    user = m.from_user
    cid = m.chat.id

    log_to_admin(f"🚀 /start\n👤 {user.first_name}\n🆔 {cid}")

    if cid not in ALLOWED_USERS:
        bot.send_message(cid, "این بات واسه‌ی تو نیست مزاحم نشو.")
        return

    if cid == MARYAM_CHAT_ID:
        bot.send_message(cid, "آیا تو مریمی؟")
        maryam_waiting.add(cid)
        return

    bot.send_message(
        cid,
        "<b>شلام همسر عزیزتر از جونم، این برای توعه.💗</b>\n\n"
        "این بات واست پیام میفرسته تا ببینی امیرعلی همیشه حواسش بهت هست واقعنی حتی تو خوابت.\n"
        "هر وقت خواستی تموم بچه، /stop رو بزن 💜",
        reply_markup=LOVE_KEYBOARD
    )
    bot.send_message(cid, get_next_message(cid))
    active_users.add(cid)
    add_active_user(cid)

@bot.message_handler(commands=["stop"])
def stop(m):
    cid = m.chat.id
    active_users.discard(cid)
    remove_active_user(cid)
    bot.reply_to(m, "دلم برات تنگ می‌شه مریم جونم.\nهر وقت دلت خواست دوباره /start بزن 😭💘")

# ================== پیام‌ها ==================
@bot.message_handler(func=lambda m: True)
def all_messages(m):
    daily_stats["messages"] += 1
    cid = m.chat.id
    text = m.text or "[غیر متنی]"

    log_to_admin(f"📩 پیام\n🆔 {cid}\n💬 {text}")

    if cid not in ALLOWED_USERS:
        bot.send_message(cid, "این بات واسه‌ی تو نیست مزاحم نشو.")
        return

    if cid in maryam_waiting:
        bot.send_message(cid,
            "از آشنایی باهات خوشبختم، سازنده‌م خیلی تعریفتو کرده پیشم و گفته که تو همه‌چیزشی، خیلی عجیب عاشقته سازنده‌م، بهت حسودی میکنم. بهم گفته بهت بگم این باتو ساخته تا یه بخش کوچیکی از علاقه‌ش بهتو ببینی."
        )
        bot.send_message(cid, get_next_message(cid), reply_markup=LOVE_KEYBOARD)
        active_users.add(cid)
        add_active_user(cid)
        maryam_waiting.remove(cid)
        return

    t = text.lower()
    if "بوس" in t:
        try:
            bot.send_voice(cid, "AwACAgQAAxkBAAEZzXVpVMMB1XPD8Kmc-jxLGEXT9SMfGAACZB0AAvLHqVJMkAepzgWEwDgE")
        except:
            bot.reply_to(m, "بوس بهت عزیزدلم.")
    elif "دلم واست تنگولیده" in t:
        bot.reply_to(m, f"{get_next_message(cid)}\n\nدل منم هر لحظه برات تنگولیده نینیم.❤️")
    elif "دوستت دارم" in t or "عشقم" in t:
        bot.reply_to(m, "همه چیز منییی؛ عاچقتم و دوستت میدالم.")
    else:
        bot.reply_to(m, "🤍❤️🩷💚🩵💜❤️‍🔥💞💕❣️💓💘💗💖")

# ================== polling پایدار ==================
bot.delete_webhook(drop_pending_updates=True)

while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
    except Exception as e:
        print("Polling crashed:", e)
        time.sleep(5)
