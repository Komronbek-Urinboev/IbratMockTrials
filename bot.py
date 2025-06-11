import logging
import time
from feature.bot_instance import bot
import config
import handlers.admin_test
import handlers.events
import handlers.register
import feature.ban
import feature.bot_instance
import feature.events_list
import feature.REQUIRED_CHANNELS
import database

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
if __name__ == "__main__":
    print("Бот запущен и работает...")
    time.sleep(1)  # <-- Даем секунду на регистрацию обработчиков
    try:
        bot.polling(none_stop=True, interval=1, timeout=10000)
    except Exception as e:
        logging.error(f"Ошибка в работе бота: {e}")
        time.sleep(5)  # Перезапуск через 5 сек

