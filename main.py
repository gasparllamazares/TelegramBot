from telebot import TeleBot
import os
from dotenv import load_dotenv

load_dotenv()

api_token = os.getenv('TELEGRAM_BOT_TOKEN')

bot = TeleBot(token=api_token)