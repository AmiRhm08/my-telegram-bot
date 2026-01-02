import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import threading
import time
import random
import sqlite3
import re
from collections import deque

# ================== تنظیمات پایه ==================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML", threaded=True)

print("DB_PATH exists:", os.path.exists("/data"))
print("DB file exists:", os.path.exists("/data/users.db"))


ADMIN_ID = 6120112176
MARYAM_CHAT_ID = 2045238581
TEST_ID = 8101517449

ALLOWED_USERS = {ADMIN_ID, MARYAM_CHAT_ID, TEST_ID}

DB_PATH = "/data/users.db"

# ================== ویس‌های بوس (file_id ها) ==================
KISS_VOICE_IDS = [
    "AwACAgQAAxkBAAIHomlXo-sRouDBpOTOnhSqmGzm4O5ZAAJiHQAC8sepUq6tTyaCrU-UOAQ",
    "AwACAgQAAxkBAAIHoWlXo-sgPTbIwYzlZpDENnVu5aPgAAJsHAACSEaBUtd0VP95xXJwOAQ",
    "AwACAgQAAxkBAAIHo2lXo-sdpuOC5w6I9Arw6DSd2S70AAJjHQAC8sepUqvrlfUXoRxgOAQ",
    "AwACAgQAAxkBAAIHpGlXo-uoLJD3gCI4JqD9dYrP8-ozAAJkHQAC8sepUlliwAEbMfd0OAQ",
    "AwACAgQAAxkBAAIHpWlXo-uqxH-jJQbSyMncAAEvFSXPPQACZR0AAvLHqVLe4eMhtHi6LDgE"
]

KISS_VOICE_MEMORY = 3  # چند تای آخر تکرار نشه

# ================== دیتابیس ==================
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS active_users (chat_id INTEGER PRIMARY KEY)")
conn.commit()

def load_active_users():
    cur.execute("SELECT chat_id FROM active_users")
    return {r[0] for r in cur.fetchall()}

def add_active_user(cid):
    cur.execute("INSERT OR IGNORE INTO active_users VALUES (?)", (cid,))
    conn.commit()

def remove_active_user(cid):
    cur.execute("DELETE FROM active_users WHERE chat_id = ?", (cid,))
    conn.commit()

active_users = load_active_users()
waiting_for_maryam = set()

# ================== لاگ ادمین ==================
def log_to_admin(title, m, extra=None):
    try:
        u = m.from_user
        msg = (
            f"📌 {title}\n"
            f"👤 {u.first_name} (@{u.username if u.username else '—'})\n"
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

# ================== پیام‌های عاشقانه ==================
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

# ================== ضدتکرار پیام ==================
MESSAGE_MEMORY = 5
msg_history = {}
msg_pool = {}

def get_next_message(cid):
    if cid not in msg_history:
        msg_history[cid] = deque(maxlen=MESSAGE_MEMORY)

    if cid not in msg_pool or not msg_pool[cid]:
        pool = romantic_messages[:]
        random.shuffle(pool)
        msg_pool[cid] = pool

    history = msg_history[cid]
    pool = msg_pool[cid]

    for _ in range(len(pool)):
        msg = pool.pop(0)
        if msg not in history:
            history.append(msg)
            return msg
        pool.append(msg)

    msg = pool.pop(0)
    history.append(msg)
    return msg

# ================== ضدتکرار ویس بوس ==================
kiss_voice_history = {}
kiss_voice_pool = {}

def get_next_kiss_voice(cid):
    if cid not in kiss_voice_history:
        kiss_voice_history[cid] = deque(maxlen=KISS_VOICE_MEMORY)

    if cid not in kiss_voice_pool or not kiss_voice_pool[cid]:
        pool = KISS_VOICE_IDS[:]
        random.shuffle(pool)
        kiss_voice_pool[cid] = pool

    history = kiss_voice_history[cid]
    pool = kiss_voice_pool[cid]

    for _ in range(len(pool)):
        vid = pool.pop(0)
        if vid not in history:
            history.append(vid)
            return vid
        pool.append(vid)

    vid = pool.pop(0)
    history.append(vid)
    return vid

# ================== تشخیص بوس / ماچ ==================
KISS_PATTERNS = (
    re.compile(r"^بو+س+$"),
    re.compile(r"^ما+چ+$"),
)

def is_kiss(text: str) -> bool:
    if not text:
        return False

    for word in text.strip().split():
        clean = word.strip(".,!?؟،؛:()[]{}\"'")
        for p in KISS_PATTERNS:
            if p.fullmatch(clean):
                return True
    return False

# ================== کیبورد ==================
LOVE_KEYBOARD = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
LOVE_KEYBOARD.add(
    KeyboardButton("دلم واست تنگولیده."),
    KeyboardButton("دوستت دارم 🤍"),
    KeyboardButton("بوس بوسیییی")
)

# ================== ارسال خودکار (فقط یک Thread) ==================
sender_thread_started = False

def background_sender():
    while True:
        for cid in list(active_users):
            try:
                bot.send_message(cid, get_next_message(cid))
                time.sleep(1)
            except:
                pass
        time.sleep(3600)

if not sender_thread_started:
    threading.Thread(target=background_sender, daemon=True).start()
    sender_thread_started = True

# ================== گرفتن file_id ویس (فقط ادمین) ==================
@bot.message_handler(content_types=["voice"])
def get_voice_id(m):
    if m.from_user.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, f"🎧 file_id:\n{m.voice.file_id}")

# ================== /start ==================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    if m.chat.id not in ALLOWED_USERS:
        ban_user(m)
        return

    log_to_admin("/start", m)

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

    log_to_admin("/stop", m)

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

        if any(x in text for x in ("آره", "اره", "بله", "مریم", "هوم", "هستم")):
            waiting_for_maryam.discard(cid)
            active_users.add(cid)
            add_active_user(cid)

            bot.send_message(
                cid,
                "از آشنایی باهات خوشبختم، سازنده‌م خیلی تعریفتو کرده پیشم و گفته که تو همه‌چیزشی."
            )

            bot.send_message(
                cid,
                "<b>شلام همسر عزیزتر از جونم، این برای توعه.💗</b>\n\n"
                "هر وقت خواستی /stop رو بزن 💜",
                reply_markup=LOVE_KEYBOARD
            )

            bot.send_message(cid, get_next_message(cid))
            return
        else:
            bot.send_message(cid, "آیا تو مریمی؟")
            return

    # ================== پاسخ‌های متنی ==================

    # 💋 بوس / ماچ (ویس رندوم + ضدتکرار)
    if text_raw.strip() == "بوس بوسیییی" or is_kiss(text_raw):
        if not KISS_VOICE_IDS:
            bot.reply_to(m, "اول باید ویس بوس‌ها رو تنظیم کنی 😅")
            return
        try:
            vid = get_next_kiss_voice(cid)
            bot.send_voice(
                cid,
                vid,
                reply_to_message_id=m.message_id
            )
            log_to_admin("💋 بوس / ماچ (ویس رندوم)", m)
        except Exception as e:
            log_to_admin("❌ خطا در بوس", m, str(e))
        return

    if "دلم واست تنگولیده" in text:
        bot.reply_to(m, f"{get_next_message(cid)}\n\nدل منم هر لحظه برات تنگولیده ❤️")
        return

    if "دوستت دارم" in text or "عشقم" in text:
        bot.reply_to(m, "همه چیز منییی؛ عاچقتم ❤️")
        return

    bot.reply_to(m, "🤍❤️🩷💚🩵💜❤️‍🔥💞💕❣️💓💘💗💖")

# ================== polling پایدار ==================
bot.delete_webhook(drop_pending_updates=True)

while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
    except Exception as e:
        print("Polling crashed:", e)
        time.sleep(5)
