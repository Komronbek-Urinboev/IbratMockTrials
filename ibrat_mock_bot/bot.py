import logging
import time
from feature.bot_instance import *

import config
import ibrat_mock_bot.handlers.admin_test
import ibrat_mock_bot.handlers.events
import ibrat_mock_bot.handlers.register
import ibrat_mock_bot.feature.ban
import ibrat_mock_bot.feature.bot_instance
import ibrat_mock_bot.feature.events_list
import ibrat_mock_bot.feature.event_translations
import ibrat_mock_bot.feature.REQUIRED_CHANNELS
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
        bot.polling(none_stop=True, interval=0, timeout=10000000)
    except Exception as e:
        logging.error(f"Ошибка в работе бота: {e}")
        time.sleep(5)  # Перезапуск через 5 сек
