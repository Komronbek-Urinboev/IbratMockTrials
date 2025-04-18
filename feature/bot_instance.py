# bot_instance.py
import telebot
from config import TOKEN

API_TOKEN = TOKEN
bot = telebot.TeleBot(API_TOKEN)

print("Bot_instance module loaded successfully.")
