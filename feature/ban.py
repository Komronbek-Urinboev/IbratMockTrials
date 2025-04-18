from feature.bot_instance import *
from config import ADMIN_IDS

blacklist = set()  # Чёрный список пользователей


@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id not in ADMIN_IDS:
        return  # Только админы могут банить

    command_parts = message.text.split()
    if len(command_parts) != 2 or not command_parts[1].isdigit():
        bot.send_message(message.chat.id, "❌ Используйте: /ban ID_пользователя")
        return

    user_id = int(command_parts[1])
    blacklist.add(user_id)  # Добавляем в чёрный список
    bot.send_message(message.chat.id, f"✅ Пользователь {user_id} заблокирован.")


@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id not in ADMIN_IDS:
        return  # Только админы могут разбанивать

    command_parts = message.text.split()
    if len(command_parts) != 2 or not command_parts[1].isdigit():
        bot.send_message(message.chat.id, "❌ Используйте: /unban ID_пользователя")
        return

    user_id = int(command_parts[1])
    blacklist.discard(user_id)  # Убираем из чёрного списка
    bot.send_message(message.chat.id, f"✅ Пользователь {user_id} разблокирован.")


@bot.message_handler(commands=['ban_status'])
def start_command(message):
    if message.from_user.id in blacklist:
        return  # Игнорируем команду, если пользователь в бане

    bot.send_message(message.chat.id, "Привет! Я твой бот и ты не заблокирован")


print("Ban module loaded successfully.")
