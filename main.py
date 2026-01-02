import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import threading
import time
import random
import sqlite3
import re
from collections import deque

# ================== تنظیمات ==================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN تنظیم نشده")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

ADMIN_ID = 6120112176
MARYAM_CHAT_ID = 2045238581
TEST_ID = 8101517449

ALLOWED_USERS = {
    ADMIN_ID,
    MARYAM_CHAT_ID,
    TEST_ID
}

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
waiting_for_maryam = set()

# ================== لاگ ادمین ==================
def log_to_admin(action, m, extra=None):
    try:
        u = m.from_user
        txt = (
            f"📌 {action}\n"
            f"👤 {u.first_name} (@{u.username if u.username else 'ندارد'})\n"
            f"🆔 {m.chat.id}"
        )
        if m.text:
            txt += f"\n💬 {m.text}"
        if extra:
            txt += f"\nℹ️ {extra}"
        bot.send_message(ADMIN_ID, txt)
    except:
        pass

# ================== بن غیرمجاز ==================
def ban_user(chat_id, m):
    log_to_admin("⛔️ بن کاربر غیرمجاز", m)
    try:
        bot.block_user(chat_id)
    except:
        pass

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
    "منو توییم هرچیم بشه.\nماباهمیم هرچیم بشه.\nمال همیم هرچیم بشه.\nحتی اون آسمون از اون بالا بیاد زمین.",
    "دنیارو نمیخوام اگه تو نباشی.",
    "نگاه تو روشن شبای بی‌چراغم.",
    "یادت نره ما باهمیم:)",
    "قفل چشاتم.",
    "دلم میخوادت.",
    "دوستت دارم تنها ماهِ آسمونِ قلبم:)",
    "میقام تورو بگیلم."
]

# ================== سیستم ضدتکرار ==================
MESSAGE_MEMORY_SIZE = 5
user_message_history = {}
user_message_pool = {}

def get_next_message(chat_id):
    if chat_id not in user_message_history:
        user_message_history[chat_id] = deque(maxlen=MESSAGE_MEMORY_SIZE)

    history = user_message_history[chat_id]

    if chat_id not in user_message_pool or not user_message_pool[chat_id]:
        pool = romantic_messages.copy()
        random.shuffle(pool)
        user_message_pool[chat_id] = pool

    pool = user_message_pool[chat_id]

    for _ in range(len(pool)):
        msg = pool.pop(0)
        if msg not in history:
            history.append(msg)
            return msg
        pool.append(msg)

    msg = pool.pop(0)
    history.append(msg)
    return msg

# ================== تشخیص بوس (قطعی) ==================
def is_kiss_message(text: str) -> bool:
    if not text:
        return False

    patterns = [
        r"^بوس",
        r"بوسه",
        r"بوسی",
        r"[😘😗😙😚💋]"
    ]

    for p in patterns:
        if re.search(p, text):
            return True

    return False

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

# ================== /start ==================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    if m.chat.id not in ALLOWED_USERS:
        ban_user(m.chat.id, m)
        return

    log_to_admin("▶️ /start", m)

    active_users.discard(m.chat.id)
    remove_active_user(m.chat.id)
    waiting_for_maryam.add(m.chat.id)

    bot.send_message(m.chat.id, "آیا تو مریمی؟")

# ================== /stop ==================
@bot.message_handler(commands=["stop"])
def stop_cmd(m):
    if m.chat.id not in ALLOWED_USERS:
        ban_user(m.chat.id, m)
        return

    log_to_admin("⏹ /stop", m)

    active_users.discard(m.chat.id)
    remove_active_user(m.chat.id)
    waiting_for_maryam.discard(m.chat.id)

    bot.send_message(
        m.chat.id,
        "باشه عزیزم.\nهر وقت دوباره دلت خواست، /start رو بزن 💜"
    )

# ================== پیام‌ها ==================
@bot.message_handler(func=lambda m: True)
def all_messages(m):
    chat_id = m.chat.id
    text_raw = m.text or ""
    text = text_raw.lower()

    if chat_id not in ALLOWED_USERS:
        ban_user(chat_id, m)
        return

    # مرحله تأیید مریمی
    if chat_id not in active_users:
        if chat_id not in waiting_for_maryam:
            waiting_for_maryam.add(chat_id)
            log_to_admin("❓ سؤال مریمی", m)
            bot.send_message(chat_id, "آیا تو مریمی؟")
            return

        if any(x in text for x in ["آره", "اره", "بله", "مریم", "هوم", "هستم"]):
            waiting_for_maryam.discard(chat_id)
            active_users.add(chat_id)
            add_active_user(chat_id)

            log_to_admin("✅ تأیید مریمی", m)

            bot.send_message(
                chat_id,
                "از آشنایی باهات خوشبختم، سازنده‌م خیلی تعریفتو کرده پیشم و گفته که تو همه‌چیزشی، "
                "خیلی عجیب عاشقته سازنده‌م، بهت حسودی میکنم. بهم گفته بهت بگم این باتو ساخته "
                "تا یه بخش کوچیکی از علاقه‌ش بهتو ببینی."
            )

            time.sleep(2)

            bot.send_message(
                chat_id,
                "<b>شلام همسر عزیزتر از جونم، این برای توعه.💗</b>\n\n"
                "این بات واست پیام میفرسته تا ببینی امیرعلی همیشه حواسش بهت هست واقعنی حتی تو خوابت.\n"
                "هر وقت خواستی تموم بچه، /stop رو بزن 💜",
                reply_markup=LOVE_KEYBOARD
            )

            bot.send_message(chat_id, get_next_message(chat_id))
            return
        else:
            log_to_admin("❌ پاسخ منفی مریمی", m)
            bot.send_message(chat_id, "آیا تو مریمی؟")
            return

    # رفتار عادی
    log_to_admin("💬 پیام کاربر", m)

    if is_kiss_message(text_raw):
        try:
            bot.send_voice(
                chat_id,
                "AwACAgQAAxkBAAEZzXVpVMMB1XPD8Kmc-jxLGEXT9SMfGAACZB0AAvLHqVJMkAepzgWEwDgE"
            )
            log_to_admin("💋 ویس بوس ارسال شد", m)
        except Exception as e:
            log_to_admin("❌ خطا در ویس بوس", m, str(e))

    elif "دلم واست تنگولیده" in text:
        bot.reply_to(
            m,
            f"{get_next_message(chat_id)}\n\nدل منم هر لحظه برات تنگولیده نینیم.❤️"
        )

    elif "دوستت دارم" in text or "عشقم" in text:
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
