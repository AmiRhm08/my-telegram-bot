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

ADMIN_ID = 6120112176
MARYAM_CHAT_ID = 2045238581
TEST_ID = 8101517449

ALLOWED_USERS = {ADMIN_ID, MARYAM_CHAT_ID, TEST_ID}

DB_PATH = "/data/users.db"
SEND_INTERVAL = 3600  # هر ۱ ساعت

# ================== ویس‌های بوس ==================
KISS_VOICE_IDS = [
    "AwACAgQAAxkBAAIHomlXo-sRouDBpOTOnhSqmGzm4O5ZAAJiHQAC8sepUq6tTyaCrU-UOAQ",
    "AwACAgQAAxkBAAIHoWlXo-sgPTbIwYzlZpDENnVu5aPgAAJsHAACSEaBUtd0VP95xXJwOAQ",
    "AwACAgQAAxkBAAIHo2lXo-sdpuOC5w6I9Arw6DSd2S70AAJjHQAC8sepUqvrlfUXoRxgOAQ",
    "AwACAgQAAxkBAAIHpGlXo-uoLJD3gCI4JqD9dYrP8-ozAAJkHQAC8sepUlliwAEbMfd0OAQ",
    "AwACAgQAAxkBAAIHpWlXo-uqxH-jJQbSyMncAAEvFSXPPQACZR0AAvLHqVLe4eMhtHi6LDgE"
]

KISS_VOICE_MEMORY = 3

# ================== لاگ ادمین ==================
LOG_LEVELS = {
    "INFO": True,
    "ACTION": True,
    "DEBUG": True,
}

ADMIN_LOG_COOLDOWN = 10
_last_admin_logs = {}

admin_stats = {
    "start": 0,
    "stop": 0,
    "kiss": 0,
    "errors": 0,
}

def log_to_admin(level, title, m=None, extra=None):
    if not LOG_LEVELS.get(level, False):
        return

    now = time.time()
    key = f"{level}:{title}:{m.chat.id if m else ''}"

    if key in _last_admin_logs and now - _last_admin_logs[key] < ADMIN_LOG_COOLDOWN:
        return

    _last_admin_logs[key] = now

    try:
        msg = f"📌 {title}"

        if m:
            u = m.from_user
            msg += (
                f"\n👤 {u.first_name} (@{u.username if u.username else '—'})"
                f"\n🆔 {m.chat.id}"
            )
            if m.text:
                msg += f"\n پیام: {m.text}"
            else:
                msg += f"\n پیام: [غیر متنی]"

        if extra:
            msg += f"\n {extra}"

        bot.send_message(ADMIN_ID, msg)
    except:
        pass

# ================== دیتابیس ==================
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS active_users (
            chat_id INTEGER PRIMARY KEY
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS replies (
            admin_msg_id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            user_msg_id INTEGER
        )
        """)

init_db()

def load_active_users():
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM active_users")
        return {r[0] for r in cur.fetchall()}

def add_active_user(cid):
    with conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO active_users VALUES (?)", (cid,))

def remove_active_user(cid):
    with conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM active_users WHERE chat_id = ?", (cid,))

def get_meta(key, default=None):
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM meta WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else default

def set_meta(key, value):
    with conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            (key, str(value))
        )

def save_reply_map(admin_msg_id, chat_id, user_msg_id):
    with conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO replies VALUES (?, ?, ?)",
            (admin_msg_id, chat_id, user_msg_id)
        )
    set_meta(f"msg_ts:{admin_msg_id}", time.time())

def get_reply_map(admin_msg_id):
    with conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT chat_id, user_msg_id FROM replies WHERE admin_msg_id = ?",
            (admin_msg_id,)
        )
        row = cur.fetchone()
        if row:
            return {"chat_id": row[0], "reply_to": row[1]}
        return None

# ================== پاکسازی خودکار ریپلای‌های قدیمی ==================
CLEANUP_INTERVAL = 24 * 3600  # هر ۲۴ ساعت
REPLY_MAX_AGE = 30 * 24 * 3600  # ۳۰ روز

def cleanup_old_replies():
    while True:
        now_ts = time.time()
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT admin_msg_id FROM replies")
            rows = cur.fetchall()

        removed = 0
        for (admin_msg_id,) in rows:
            try:
                ts = float(get_meta(f"msg_ts:{admin_msg_id}", 0))
                if now_ts - ts > REPLY_MAX_AGE:
                    with conn:
                        cur = conn.cursor()
                        cur.execute("DELETE FROM replies WHERE admin_msg_id = ?", (admin_msg_id,))
                    removed += 1
            except:
                continue

        if removed:
            log_to_admin("INFO", f"🧹 پاکسازی ریپلای‌های قدیمی: {removed} مورد حذف شد")

        time.sleep(CLEANUP_INTERVAL)

threading.Thread(target=cleanup_old_replies, daemon=True).start()

active_users = load_active_users()
waiting_for_maryam = set()

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
    "دوستت دارم تنها ماهِ آسمونِ قلبم:)"
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

    hist = msg_history[cid]
    pool = msg_pool[cid]

    for _ in range(len(pool)):
        msg = pool.pop(0)
        if msg not in hist:
            hist.append(msg)
            return msg
        pool.append(msg)

    msg = pool.pop(0)
    hist.append(msg)
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

    hist = kiss_voice_history[cid]
    pool = kiss_voice_pool[cid]

    for _ in range(len(pool)):
        vid = pool.pop(0)
        if vid not in hist:
            hist.append(vid)
            return vid
        pool.append(vid)

    vid = pool.pop(0)
    hist.append(vid)
    return vid

# ================== تشخیص بوس ==================
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

# ================== ارسال خودکار ==================
def background_sender():
    log_to_admin("INFO", "⏰ ارسال خودکار فعال شد")
    while True:
        last_ts = float(get_meta("last_send_ts", 0))
        now = time.time()
        if now - last_ts < SEND_INTERVAL:
            time.sleep(20)
            continue

        for cid in list(active_users):
            try:
                bot.send_message(cid, get_next_message(cid))
                time.sleep(1)
            except:
                admin_stats["errors"] += 1

        set_meta("last_send_ts", now)
        log_to_admin("INFO", "💌 پیام عاشقانه ارسال شد")

threading.Thread(target=background_sender, daemon=True).start()

# ================== دستور ارسال پیام ادمین ==================
@bot.message_handler(commands=["send"])
def admin_send(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, cid, text = m.text.split(" ", 2)
        bot.send_message(int(cid), text)
        bot.reply_to(m, "✅ ارسال شد")
    except:
        bot.reply_to(m, "❌ فرمت صحیح نیست")

# ================== دریافت ویس ادمین ==================
@bot.message_handler(content_types=["voice"])
def get_voice_id(m):
    if m.from_user.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, f"🎧 file_id:\n{m.voice.file_id}")

# ================== پیام‌ها ==================
@bot.message_handler(func=lambda m: True)
def all_messages(m):
    log_to_admin("DEBUG", "📩 پیام جدید", m)

    cid = m.chat.id
    text_raw = m.text or ""
    text = text_raw.lower()

    # 👑 ریپلای ادمین روی پیام فوروارد شده از کاربر
    if cid == ADMIN_ID and m.reply_to_message:
        data = get_reply_map(m.reply_to_message.message_id)
        if not data:
            bot.reply_to(m, "❌ این پیام به کاربری وصل نیست یا پاک شده")
            return

        try:
            bot.copy_message(
                chat_id=data["chat_id"],
                from_chat_id=ADMIN_ID,
                message_id=m.message_id,
                reply_to_message_id=data["reply_to"]
            )
            log_to_admin("ACTION", "✅ ریپلای ادمین ارسال شد", m)
        except Exception as e:
            log_to_admin("INFO", "❌ خطا در ریپلای ادمین", m, extra=str(e))
        return

    # فوروارد پیام کاربر به ادمین و ذخیره mapping
    if cid != ADMIN_ID:
        try:
            fwd = bot.forward_message(ADMIN_ID, cid, m.message_id)
            save_reply_map(
                admin_msg_id=fwd.message_id,
                chat_id=cid,
                user_msg_id=m.message_id
            )
        except:
            pass

    if cid not in active_users:
        if cid not in waiting_for_maryam:
            waiting_for_maryam.add(cid)
            bot.send_message(cid, "آیا تو مریمی؟")
            return

        if any(x in text for x in ("آره", "اره", "بله", "مریم", "هوم", "هستم")):
            waiting_for_maryam.discard(cid)
            active_users.add(cid)
            add_active_user(cid)

            log_to_admin("ACTION", "✅ تأیید مریمی", m)

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

    if text_raw.strip() == "بوس بوسیییی" or is_kiss(text_raw):
        try:
            vid = get_next_kiss_voice(cid)
            bot.send_voice(cid, vid, reply_to_message_id=m.message_id)
            admin_stats["kiss"] += 1
            log_to_admin("ACTION", "💋 بوس / ماچ", m)
        except:
            admin_stats["errors"] += 1
        return

    if "دلم واست تنگولیده" in text:
        bot.reply_to(m, f"{get_next_message(cid)}\n\nدل منم هر لحظه برات تنگولیده ❤️")
        return

    if "دوستت دارم" in text or "عشقم" in text:
        bot.reply_to(m, "همه چیز منییی؛ عاچقتم ❤️")
        return

    bot.reply_to(m, "🤍❤️🩷💚🩵💜❤️‍🔥💞💕❣️💓💘💗💖")

# ================== polling ==================
bot.delete_webhook(drop_pending_updates=True)

while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
    except:
        time.sleep(5)
