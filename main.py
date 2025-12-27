import os
os.system("pip install pyTelegramBotAPI")

import telebot
import threading
import time
import random

# Put your bot token directly here
TOKEN = "YOUR_TOKEN_HERE"  # توکن واقعی باتت رو اینجا بذار

# Create the bot instance
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# List of romantic messages (you can add more!)
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
    "دلم فقط برای تو می‌تپه ❤️❤️❤️"
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
    user_name = message.from_user.first_name
    chat_id = message.chat.id
    
    welcome_text = (
        f"سلام <b>{user_name}</b> عشقم! 😍❤️\n\n"
        "از حالا هر ۱۰ ثانیه یک پیام عاشقانه برات می‌فرستم!\n"
        "هر وقت خواستی تموم بشه، /stop رو بزن 💕"
    )
    bot.reply_to(message, welcome_text)
    
    # Stop if user already active
    if chat_id in active_users:
        active_users[chat_id].cancel()
    
    # Start new thread for sending messages
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
        bot.reply_to(message, "پیام‌های عاشقانه متوقف شد 😢\nهر وقت دلت تنگ شد دوباره /start بزن 💕")
    else:
        bot.reply_to(message, "هنوز چیزی شروع نشده که بخوای متوقف کنی! 😏\n/start بزن تا عشق بریزه!")

# Optional: handle normal text messages
@bot.message_handler(content_types=['text'])
def echo(message):
    bot.reply_to(message, "عشقم، من فقط منتظرم /start بزنی تا عاشقانه بفرستم برات ❤️\nیا اگر شروع شده، /stop بزن تا آروم بگیرم 😘")

# Startup message
print("بات عاشقانه شروع شد و آماده ارسال عشق است!")

# Start the bot
bot.infinity_polling()

