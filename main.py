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

# 🔴 بعد از گرفتن file_id اینو پر کن
KISS_VOICE_ID = ""   # مثال: "AwACAgQAAxkBAA..."

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
        msg = (
            f"📌 {action}\n"
            f"👤 {u.first_name} (@{u.username if u.username else 'ندارد'})\n"
            f"🆔 {m.chat.id}"
        )
        if m.text:
            msg += f"\n💬 {m.text}"
        if extra:
            msg += f"\nℹ️ {extra}"
        bot.send_message(ADMIN_ID, msg)
    except:
        pass

# ================== بن غیرمجاز ==================
def ban_user(m):
    log_to_admin("⛔️ بن کاربر غیرمجاز", m)
    try:
        bot.block_user(m.chat.id)
    except:
        pass

# ================== پیام‌ها ==================
romantic_messages = [
    "مریم جونم، تو بهترین اتفاق زندگی منی. ❤️",
    "هر لحظه به فکرتم عشقم. 💕",
    "من خوشحالم که تورو دارم مریم، یادت نره هیچوقت.",
    "مریم، تو دلیل لبخند منی.",
    "مریم جونم، تو سقف رویای منی.",
    "قلبم واست میتپه مریم کوشولو.❤️",
    "تو قشنگی مثل شکلایی که ابرا میسازن.",
    "دنیارو نمیخوام اگه تو نباشی.",
    "نگاه تو روشن شبای بی‌چراغم.",
    "قفل چشاتم.",
    "دلم میخوادت.",
    "دوستت دارم تنها ماهِ آسمونِ قلبم:)",
]

# ================== ضدتکرار ==================
MESSAGE_MEMORY_SIZE = 5
user_history = {}
user_pool = {}

def get_next_message(chat_id):
    if chat_id not in user_history:
        user_history[chat_id] = deque(maxlen=MESSAGE_MEMORY_SIZE)

    if chat_id not in user_pool or not user_pool[chat_id]:
        pool = romantic_messages.copy()
        random.shuffle(pool)
        user_pool[chat_id] = pool

    history = user_history[chat_id]
    pool = user_pool[chat_id]

    for _ in range(len(pool)):
        msg = pool.pop(0)
        if msg not in history:
            history.append(msg)
            return msg
        pool.append(msg)

    msg = pool.pop(0)
    history.append(msg)
    return msg

# ================== تشخیص بوس ==================
def is_kiss(text: str) -> bool:
    if not text:
        return False
    return bool(re.search(r"(بوس|بوسی|بوسه|😘|😗|😙|😚|💋)", text))

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

            for cid in list(active_users):
                try:
                    bot.send_message(cid, get_next_message(cid))
                    time.sleep(1)
                except:
                    pass

            time.sleep(3600)
        except:
            time.sleep(60)

threading.Thread(target=background_sender, daemon=True).start()

# ================== گرفتن file_id ویس (فقط ادمین) ==================
@bot.message_handler(content_types=['voice'])
def get_voice_id(m):
    if m.from_user.id == ADMIN_ID:
        bot.send_message(
            ADMIN_ID,
            f"🎧 file_id ویس:\n{m.voice.file_id}"
        )

# ================== /start ==================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    if m.chat.id not in ALLOWED_USERS:
        ban_user(m)
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
        ban_user(m)
        return

    log_to_admin("⏹ /stop", m)

    active_users.discard(m.chat.id)
    remove_active_user(m.chat.id)
    waiting_for_maryam.discard(m.chat.id)

    bot.send_message(m.chat.id, "باشه عزیزم.\nهر وقت دلت خواست /start رو بزن 💜")

# ================== پیام‌ها ==================
@bot.message_handler(func=lambda m: True)
def all_messages(m):
    cid = m.chat.id
    text_raw = m.text or ""
    text = text_raw.lower()

    if cid not in ALLOWED_USERS:
        ban_user(m)
        return

    # مرحله مریمی
    if cid not in active_users:
        if cid not in waiting_for_maryam:
            waiting_for_maryam.add(cid)
            bot.send_message(cid, "آیا تو مریمی؟")
            return

        if any(x in text for x in ["آره", "اره", "بله", "مریم", "هوم", "هستم"]):
            waiting_for_maryam.discard(cid)
            active_users.add(cid)
            add_active_user(cid)

            bot.send_message(
                cid,
                "از آشنایی باهات خوشبختم، سازنده‌م خیلی تعریفتو کرده پیشم و گفته که تو همه‌چیزشی، "
                "خیلی عجیب عاشقته سازنده‌م."
            )

            time.sleep(2)

            bot.send_message(
                cid,
                "<b>شلام همسر عزیزتر از جونم، این برای توعه.💗</b>\n\n"
                "این بات واست پیام میفرسته تا ببینی امیرعلی همیشه حواسش بهت هست.\n"
                "هر وقت خواستی /stop رو بزن 💜",
                reply_markup=LOVE_KEYBOARD
            )

            bot.send_message(cid, get_next_message(cid))
            return
        else:
            bot.send_message(cid, "آیا تو مریمی؟")
            return

    # ================== پاسخ‌های متنی ==================

    # 💋 بوس دقیقاً اینجاست
    if text_raw.strip() == "بوس بوسیییی" or is_kiss(text_raw):
        if not KISS_VOICE_ID:
            bot.reply_to(m, "اول باید ویس بوس رو تنظیم کنی 😅")
            return
        try:
            bot.send_voice(cid, KISS_VOICE_ID)
            log_to_admin("💋 بوس", m)
        except Exception as e:
            log_to_admin("❌ خطا در بوس", m, str(e))
        return

    elif "دلم واست تنگولیده" in text:
        bot.reply_to(m, f"{get_next_message(cid)}\n\nدل منم هر لحظه برات تنگولیده ❤️")

    elif "دوستت دارم" in text or "عشقم" in text:
        bot.reply_to(m, "همه چیز منییی؛ عاچقتم ❤️")

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
