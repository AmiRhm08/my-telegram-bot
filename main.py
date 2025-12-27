import telebot

# Put your bot token directly here (from @BotFather)
TOKEN = "8206760539:AAHS7iceJT5f2GjNgXU-MiOYat7cyxeBPuU"  # مثال: 8206760539:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Create the bot instance with HTML formatting support
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

@bot.message_handler(commands=['start'])
def start(message):
    # Get user's first name for personalized greeting
    user_name = message.from_user.first_name
    
    welcome_text = (
        f"سلام <b>{user_name}</b> عزیز! \n\n"
        "من بات توام!\n"
        "هر متنی که بفرستی، برات تکرارش می‌کنم.\n\n"
        "برای راهنما /help رو بزن."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def help_command(message):
    # Help message with instructions
    help_text = (
        "<b>راهنما:</b>\n\n"
        "• هر متنی که بفرستی → من تکرارش می‌کنم\n"
        "• /start → شروع دوباره\n"
        "• /help → نمایش این پیام\n\n"
        "باتت همیشه آنلاینه!"
    )
    bot.reply_to(message, help_text)

# Echo all text messages with user's name
@bot.message_handler(content_types=['text'])
def echo(message):
    user_name = message.from_user.first_name
    response = f"<b>{user_name}</b> گفتی:\n\n<code>{message.text}</code>"
    bot.reply_to(message, response)

# Startup message for logs
print("Bot started successfully with direct token!")

# Start listening for messages
bot.infinity_polling()
