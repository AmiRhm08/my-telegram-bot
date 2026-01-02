import os
import time
import random
import sqlite3
import threading
import re
from collections import deque

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ================== تنظیمات پایه ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)

ADMIN_ID = 6120112176
MARYAM_CHAT_ID = 2045238581
TEST_ID = 8101517449
ALLOWED_USERS = {ADMIN_ID, MARYAM_CHAT_ID, TEST_ID}

DB_PATH = "/data/users.db"
SEND_INTERVAL = 3600  # پیام عاشقانه هر ۱ ساعت

# ================== ویس‌های بوس ==================
KISS_VOICE_IDS = [
    "AwACAgQAAxkBAAIHomlXo-sRouDBpOTOnhSqmGzm4O5ZAAJiHQAC8sepUq6tTyaCrU-UOAQ",
    "AwACAgQAAxkBAAIHoWlXo-sgPTbIwYzlZpDENnVu5aPgAAJsHAACSEaBUtd0VP95xXJwOAQ",
    "AwACAgQAAxkBAAIHo2lXo-sdpuOC5w6I9Arw6DSd2S70AAJjHQAC8sepUqvrlfUXoRxgOAQ",
    "AwACAgQAAxkBAAIHpGlXo-uoLJD3gCI4JqD9dYrP8-ozAAJkHQAC8sepUlliwAEbMfd0OAQ",
    "AwACAgQAAxkBAAIHpWlXo-uqxH-jJQbSyMncAAEvFSXPPQACZR0AAvLHqVLe4eMhtHi6LDgE"
]

KISS_VOICE_MEMORY = 3

# ================== دیتابیس ==================
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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

def get_meta(key, default=0):
    cur.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = cur.fetchone()
    return float(row[0]) if row else default

def set_meta(key, value):
    cur.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
        (key, str(value))
    )
    conn.commit()

active_users = load_active_users()
waiting_for_maryam = set()

# ================== پیام‌های عاشقانه (متن‌های اصلی تو) ==================
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

# ================== حافظه مکالمه شبه-AI ==================
CHAT_MEMORY_SIZE = 10
chat_memory = {}

def remember(cid, text):
    if cid not in chat_memory:
        chat_memory[cid] = deque(maxlen=CHAT_MEMORY_SIZE)
    chat_memory[cid].append(text)

def last_message(cid):
    if cid in chat_memory and chat_memory[cid]:
        return chat_memory[cid][-1]
    return ""

# ================== مغز هوشمند رایگان ==================
def smart_reply(cid, text):
    prev = last_message(cid)

    sad_words = ["خسته", "حالم خوب نیست", "ناراحتم", "دلم گرفته", "گریه"]
    why_words = ["چرا", "چی شده"]
    happy_words = ["خوبم", "خوشحالم", "عالی", "اوکی"]

    if any(w in text for w in sad_words):
        return random.choice([
            "بیا بغلت کنم… دلم نمیاد حالت بد باشه 🤍",
            "کنارت هستم، هرچی تو دلت هست بگو 😔",
            "نذار غمتو تنهایی بکشی، من اینجام ❤️"
        ])

    if text.strip() in why_words and any(w in prev for w in sad_words):
        return random.choice([
            "چون وقتی حالت بده، دلم می‌لرزه…",
            "چون تو برام مهمی، نمی‌تونم بی‌تفاوت باشم 🤍",
            "چون دوست داشتن یعنی همین، کنار هم بودن"
        ])

    if any(w in text for w in happy_words):
        return random.choice([
            "لبخندت قشنگ‌ترین اتفاق دنیاست 😊",
            "وقتی حالت خوبه، دل منم قرصه ❤️",
            "خوشحالیت حال منو هم خوب می‌کنه"
        ])

    return random.choice([
        "حرفت برام مهمه، ادامه بده…",
        "دارم گوش می‌دم 🤍",
        "بگو عشقم، من کنارتم"
    ])

# ================== تشخیص بوس / ماچ ==================
KISS_PATTERNS = (
    re.compile(r"^بو+س+$"),
    re.compile(r"^ما+چ+$"),
)

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

def is_kiss(text):
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

# ================== ارسال خودکار پایدار ==================
def background_sender():
    while True:
        last_ts = get_meta("last_send_ts", 0)
        now = time.time()
        if now - last_ts < SEND_INTERVAL:
            time.sleep(20)
            continue
        for cid in list(active_users):
            try:
                bot.send_message(cid, get_next_message(cid))
                time.sleep(1)
            except:
                pass
        set_meta("last_send_ts", now)

threading.Thread(target=background_sender, daemon=True).start()

# ================== /start ==================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    if m.chat.id not in ALLOWED_USERS:
        return
    active_users.discard(m.chat.id)
    remove_active_user(m.chat.id)
    waiting_for_maryam.add(m.chat.id)
    bot.send_message(m.chat.id, "آیا تو مریمی؟")

# ================== /stop ==================
@bot.message_handler(commands=["stop"])
def stop_cmd(m):
    if m.chat.id not in ALLOWED_USERS:
        return
    active_users.discard(m.chat.id)
    remove_active_user(m.chat.id)
    waiting_for_maryam.discard(m.chat.id)
    bot.send_message(m.chat.id, "باشه عزیزم.\nهر وقت دلت خواست /start رو بزن 💜")

# ================== پیام‌ها ==================
@bot.message_handler(func=lambda m: True)
def all_messages(m):
    cid = m.chat.id
    text = m.text or ""

    if cid not in ALLOWED_USERS:
        return

    remember(cid, text)

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
                "از آشنایی باهات خوشبختم، سازنده‌م خیلی تعریفتو کرده پیشم و گفته که تو همه‌چیزشی، خیلی عجیب عاشقته سازنده‌م، بهت حسودی میکنم. بهم گفته بهت بگم این باتو ساخته تا یه بخش کوچیکی از علاقه‌ش بهتو ببینی."
            )
            bot.send_message(
                cid,
                "<b>شلام همسر عزیزتر از جونم، این برای توعه.💗</b>\n\n"
                "این بات واست پیام میفرسته تا ببینی امیرعلی همیشه حواسش بهت هست واقعنی حتی تو خوابت.\n"
                "هر وقت خواستی تموم بچه، /stop رو بزن 💜",
                reply_markup=LOVE_KEYBOARD
            )
            bot.send_message(cid, get_next_message(cid))
            return
        else:
            bot.send_message(cid, "آیا تو مریمی؟")
            return

    if text.strip() == "بوس بوسیییی" or is_kiss(text):
        if KISS_VOICE_IDS:
            vid = get_next_kiss_voice(cid)
            bot.send_voice(cid, vid, reply_to_message_id=m.message_id)
        return

    if text.strip() == "دلم واست تنگولیده":
        bot.reply_to(m, f"{get_next_message(cid)}\n\nدل منم هر لحظه برات تنگولیده نینیم.❤️")
        return

    if text.strip() == "دوستت دارم":
        bot.reply_to(m, "همه چیز منییی؛ عاچقتم و دوستت میدالم.")
        return

    reply = smart_reply(cid, text)
    bot.reply_to(m, reply)

# ================== polling ==================
bot.delete_webhook(drop_pending_updates=True)
bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
