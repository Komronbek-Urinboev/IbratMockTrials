#bot_instance.py
import telebot
from ibrat_mock_bot.config import TOKEN

API_TOKEN = TOKEN
bot = telebot.TeleBot(API_TOKEN)

print("Bot_instance module loaded successfully.")