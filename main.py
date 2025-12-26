import telebot

TOKEN = "8206760539:YOUR_TOKEN_HERE"

# پروکسی MTProto (از @MTProtoProxies یا @mtpro_xyz_bot بگیر)
proxy_url = "https://t.me/proxy?server=full.siteliveim.co.uk.&port=443&secret=dd104462821249bd7ac519130220c25d09"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# تنظیم پروکسی MTProto
telebot.apihelper.proxy = {'https': proxy_url}

# بقیه کد همون قبلی...
@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    bot.reply_to(message, f"سلام <b>{user_name}</b>! بات با MTProto وصل شد!")

@bot.message_handler(content_types=['text'])
def echo(message):
    bot.reply_to(message, f"گفتی: <code>{message.text}</code>")

print("Bot starting with MTProto proxy...")
bot.infinity_polling()