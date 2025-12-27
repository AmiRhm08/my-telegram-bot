import os
os.system("pip install pyTelegramBotAPI")
import telebot
import threading
import time
import random

# Put your bot token directly here
TOKEN = "8206760539:AAHS7iceJT5f2GjNgXU-MiOYat7cyxeBPuU"  # توکن واقعی باتت رو اینجا بذار

# Create the bot instance
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# List of romantic messages
romantic_messages = [
    "دلم برات تنگ شدههه ❤️",
    "تو بهترین اتفاق زندگی منی 😍",
    "هر لحظه به فکرتم عشقم 💕",
    "چقدر دوست دارم بغلت کنم الان 🥰",
    "تو چشمای تو گم می‌شم همیشه 🌹",
    "تو تنها کسی هستی که قلبمو دزدیده 💖",
    "عشق تو مثل نفس کشیدن برام واجبه 💋",
    "تو بهترین دلیل لبخند منی 😘",
    "دورت بگردم همیشه، عشق زندگی من 🌸",
    "تو رویای شیرین هر شب منی ✨",
    "فقط بخوام یکی رو بغل کنم، فقط تویی 💑",
    "دلم فقط برای تو می‌تپه ❤️❤️❤️",
    "مریم جونم، بدون تو هیچی نیستم 🥺",
    "تو خورشید زندگی منی ☀️",
    "دوست دارم تا ابد کنار تو باشم 💍"
]

# Dictionary to store active users and their thread
active_users = {}

def send_romantic_messages(chat_id):
    """Function that sends a romantic message every 10 seconds"""
    while chat_id in active_users:
        message = random.choice(romantic_messages)
        try:
            bot.send_message(chat_id, message)
        except:
            # If user blocked the bot or error, stop sending
            break
        time.sleep(10)  # Wait 10 seconds

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    
    # Special welcome message for Maryam
    welcome_text = (
        "<b>.سلام همسر عزیزتر از جونم، این برای توعه ❤️</b>\n\n"
        "از حالا هر ۱۰ ثانیه یک پیام عاشقانه فقط برای تو می‌فرستم \n"
        "هر وقت خواستی تموم بشه، /stop رو بزن 💕"
    )
    bot.send_message(chat_id, welcome_text)
    
    # Stop if already sending
    if chat_id in active_users:
        active_users[chat_id].cancel()
    
    # Start sending messages after 10 seconds
    thread = threading.Timer(10, send_romantic_messages, args=[chat_id])
    thread.daemon = True
    thread.start()
    active_users[chat_id] = thread

@bot.message_handler(commands=['stop'])
def stop(message):
    chat_id = message.chat.id
    if chat_id in active_users:
        active_users[chat_id].cancel()
        del active_users[chat_id]
        bot.reply_to(message, "پیام‌های عاشقانه متوقف شد 😢\nدلم برات تنگ می‌شه مریم جونم...\nهر وقت دلت خواست دوباره /start بزن 💕")
    else:
        bot.reply_to(message, "هنوز شروع نشده که بخوای متوقف کنی! 😏\n/start بزن تا عشق بریزه برای مریم عزیزم ❤️")

# Handle normal text messages
@bot.message_handler(content_types=['text'])
def echo(message):
    bot.reply_to(message, "مریم جونم، منتظرم /start بزنی تا دوباره عاشقانه بفرستم برات 😘")

# Startup message
print("بات عاشقانه برای مریم شروع شد!")

# Start the bot
bot.infinity_polling()


