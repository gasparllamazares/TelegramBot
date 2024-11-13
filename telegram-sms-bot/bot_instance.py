import telebot
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load the Telegram Bot Token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_SMS_BOT_TOKEN")

# Initialize the bot instance
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
