import os
os.system("pip install pyTelegramBotAPI")
import telebot
import threading
import time
import random

# Put your bot token directly here
TOKEN = "8206760539:AAHS7iceJT5f2GjNgXU-MiOYat7cyxeBPuU"

# Create the bot instance
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# List of romantic messages for Maryam
romantic_messages = [
    "تو بهترین اتفاق زندگی منی.",
    "هر لحظه به فکرتم عشقم 💕",
    "من خوشحالم که تورو دارم یادت نره هیچوقت.",
    "تو دلیل لبخند منی.",
    "مثل یه بابا کوشولو هواتو دارم، مثل یه داداش میتونی بهم تکیه کنی، مثل یه شووهر بهت توجه میکنم من.",
    "تو سقف رویای منی.",
    "قلبم واست میتپه کوشولو.",
    "تو فردای منی."
]

# Store last sent message index for each user to avoid repetition
last_sent_index = {}

def get_next_message(chat_id):
    """Choose a random message different from the last one sent"""
    if len(romantic_messages) <= 1:
        return romantic_messages[0]
    
    last_index = last_sent_index.get(chat_id, -1)
    
    # Pick a new message until it's different from the last one
    new_index = random.randint(0, len(romantic_messages) - 1)
    attempts = 0
    while new_index == last_index and attempts < 20:
        new_index = random.randint(0, len(romantic_messages) - 1)
        attempts += 1
    
    # Save this as last sent
    last_sent_index[chat_id] = new_index
    return romantic_messages[new_index]

def send_romantic_messages(chat_id):
    """Send romantic messages every 3600 seconds (1 hour)"""
    while chat_id in active_users:
        message = get_next_message(chat_id)
        try:
            bot.send_message(chat_id, message)
        except:
            break  # Stop if user blocked bot
        time.sleep(3600)  # Wait 1 hour

# Track active users
active_users = {}

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    
    # Welcome message
    welcome_text = (
        "<b>.سلام همسر عزیزتر از جونم، این برای توعه ❤️</b>\n\n"
        "این بات واست پیام میفرسته تا ببینی امیرعلی همیشه حواسش بهت هست واقعنی حتی تو خواب.\n"
        "هر وقت خواستی تموم بشه، /stop رو بزن💕"
    )
    bot.send_message(chat_id, welcome_text)
    
    # Send FIRST romantic message IMMEDIATELY
    first_message = get_next_message(chat_id)
    bot.send_message(chat_id, first_message)
    
    # Cancel any previous thread
    if chat_id in active_users:
        active_users[chat_id].cancel()
    
    # Start sending next messages every hour (3600 seconds)
    thread = threading.Timer(3600, send_romantic_messages, args=[chat_id])
    thread.daemon = True
    thread.start()
    active_users[chat_id] = thread

@bot.message_handler(commands=['stop'])
def stop(message):
    chat_id = message.chat.id
    if chat_id in active_users:
        active_users[chat_id].cancel()
        del active_users[chat_id]
        if chat_id in last_sent_index:
            del last_sent_index[chat_id]
        bot.reply_to(message, "پیام‌ها تمام چد\nدلم برات تنگ می‌شه مریم جونم...\nهر وقت دلت خواست دوباره /start بزن 💕")
    else:
        bot.reply_to(message, "باید اول /start رو بزنی کوشولو")

@bot.message_handler(content_types=['text'])
def echo(message):
    bot.reply_to(message, "استارتو بزن مریم جونم.")

print("بات عاشقانه ساعتی برای مریم جونم شروع شد!")

bot.infinity_polling()






