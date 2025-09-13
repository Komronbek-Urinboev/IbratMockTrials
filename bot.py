import logging
import time
from feature.bot_instance import bot
import config
import handlers.admin
import handlers.events
import handlers.register
import feature.ban
import feature.bot_instance
import feature.REQUIRED_CHANNELS
import database_ev
from database_ev.events_db import init_events_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

if __name__ == "__main__":
    print("Бот запускается...")
    # Инициализируем БД событий (создаст таблицу, если её ещё нет)
    init_events_db()

    print("Бот запущен и работает...")
    time.sleep(1)  # <-- Даем секунду на регистрацию обработчиков

    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=10000)
        except Exception as e:
            logging.error(f"Ошибка в работе бота: {e}")
            time.sleep(5)  # Перезапуск через 5 сек
