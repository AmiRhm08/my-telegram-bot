import os
import time
import random
import sqlite3
import threading
import re
from collections import deque

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from openai import OpenAI

# ================== تنظیمات پایه ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY تنظیم نشده")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)
ai_client = OpenAI(api_key=OPENAI_API_KEY)

ADMIN_ID = 6120112176
MARYAM_CHAT_ID = 2045238581
TEST_ID = 8101517449
ALLOWED_USERS = {ADMIN_ID, MARYAM_CHAT_ID, TEST_ID}

DB_PATH = "/data/users.db"
SEND_INTERVAL = 3600  # هر ۱ ساعت

# ================== ویس‌های بوس ==================
# file_idها رو اینجا بذار
KISS_VOICE_IDS = [
    # "AwACAgQAAxkBAA...",
    # "AwACAgQAAxkBAA...",
]
KISS_VOICE_MEMORY = 3  # چند تای آخر تکرار نشه

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

def get_meta(key, default=None):
    cur.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = cur.fetchone()
    return row[0] if row else default

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

# ================== تشخیص بوس / ماچ (کلمه‌ای + کشیده) ==================
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

# ================== ارسال خودکار پایدار (Persisted) ==================
def background_sender():
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
                pass

        set_meta("last_send_ts", now)

threading.Thread(target=background_sender, daemon=True).start()

# ================== گرفتن file_id ویس (فقط ادمین) ==================
@bot.message_handler(content_types=["voice"])
def get_voice_id(m):
    if m.from_user.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, f"🎧 file_id:\n{m.voice.file_id}")

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

# ================== AI: حافظه مکالمه (۱۰ پیام) ==================
AI_MEMORY_SIZE = 10
ai_memory = {}  # chat_id -> deque

SYSTEM_PROMPT = (
    "تو یک بات عاشقانه، صمیمی و وفاداری. "
    "لحن تو گرم، آرام، احساسی و کاملاً انسانی است. "
    "از لحن خشک یا رسمی استفاده نکن. "
    "خیلی کوتاه یا خیلی طولانی جواب نده. "
    "مهربان، امن و قابل اعتماد باش."
)

def ai_reply(chat_id: int, user_text: str) -> str:
    if chat_id not in ai_memory:
        ai_memory[chat_id] = deque(maxlen=AI_MEMORY_SIZE)

    memory = ai_memory[chat_id]
    memory.append({"role": "user", "content": user_text})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(memory)

    try:
        resp = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8,
            max_tokens=140
        )
        reply = resp.choices[0].message.content.strip()
        memory.append({"role": "assistant", "content": reply})
        return reply
    except:
        return "الان یه لحظه ذهنم شلوغه… ولی کنارتم 🤍"

# ================== پیام‌ها ==================
@bot.message_handler(func=lambda m: True)
def all_messages(m):
    cid = m.chat.id
    text_raw = m.text or ""
    text = text_raw.lower()

    if cid not in ALLOWED_USERS:
        return

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

    # 💋 بوس / ماچ (ویس رندوم + ریپلای)
    if text_raw.strip() == "بوس بوسیییی" or is_kiss(text_raw):
        if KISS_VOICE_IDS:
            vid = get_next_kiss_voice(cid)
            bot.send_voice(cid, vid, reply_to_message_id=m.message_id)
        return

    # پاسخ‌های دستی
    if "دلم واست تنگولیده" in text:
        bot.reply_to(m, f"{get_next_message(cid)}\n\nدل منم هر لحظه برات تنگولیده نینیم.❤️")
        return

    if "دوستت دارم" in text or "عشقم" in text:
        bot.reply_to(m, "همه چیز منییی؛ عاچقتم و دوستت میدالم.")
        return

    # پاسخ هوشمند AI
    ai_text = ai_reply(cid, text_raw)
    bot.reply_to(m, ai_text)

# ================== polling ==================
bot.delete_webhook(drop_pending_updates=True)
bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
