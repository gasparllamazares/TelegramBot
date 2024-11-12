import telebot
from database import save_user, get_user_id, delete_user
import os

# Load the bot token from the environment
TELEGRAM_BOT_TOKEN = ""
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Handle /register command
@bot.message_handler(commands=["register"])
def register(message):
    user_id = message.from_user.id
    username = message.from_user.username

    if username:
        # Verificar si el usuario ya está registrado
        existing_user_id = get_user_id(username)
        if existing_user_id:
            bot.reply_to(message, "You are already registered.")
        else:
            save_user(username, user_id)  # Guardar en la base de datos
            bot.reply_to(message, "You have been registered successfully!")
    else:
        bot.reply_to(message, "Please set a username in Telegram to register.")

# Handle /deregister command
@bot.message_handler(commands=["deregister"])
def deregister(message):
    username = message.from_user.username

    if username:
        # Verificar si el usuario está registrado
        existing_user_id = get_user_id(username)
        if existing_user_id:
            delete_user(username)  # Eliminar de la base de datos
            bot.reply_to(message, "You have been deregistered successfully.")
        else:
            bot.reply_to(message, "You are not registered.")
    else:
        bot.reply_to(message, "Please set a username in Telegram to use deregister.")

# Start the bot (polling)
if __name__ == "__main__":
    bot.polling()
