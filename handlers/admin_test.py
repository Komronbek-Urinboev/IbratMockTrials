import os
import json
import shutil
import importlib
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,

)

# Импортируем объекты бота, базы и конфигураций
from feature.bot_instance import bot
from database import users_db, save_db  # save_db — функция для сохранения изменений в базе, если используется
from config import ADMIN_IDS
from feature.events_list import EVENT_LIST


# ==================================================================
# Функция отображения главного меню для пользователей
def show_main_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Записаться на Ibrat Mock Trials"))
    if chat_id in ADMIN_IDS:
        markup.add(KeyboardButton("Административная панель"))
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)


# ==================================================================
# Административная панель
@bot.message_handler(commands=["admin_panel"])
def admin_panel(message):
    if message.chat.id not in ADMIN_IDS:
        return  # Только для администраторов

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Просмотр базы данных"))
    markup.add(KeyboardButton("Скачать базу данных в $Excel$"))
    markup.add(KeyboardButton("Посмотреть список зарегестрированных"))
    markup.add(KeyboardButton("Изменить мероприятия (events_list.py)"))
    markup.add(KeyboardButton("Рассылка"))
    markup.add(KeyboardButton("Статистика"))
    bot.send_message(message.chat.id, "Административная панель:", reply_markup=markup)

# ==================================================================
# Просмотр базы данных зарегистрированных пользователей
@bot.message_handler(func=lambda message: message.text == "Просмотр базы данных" and message.chat.id in ADMIN_IDS)
def view_database(message):
    if not users_db:
        bot.send_message(message.chat.id, "База данных пуста.")
        return

    messages = []
    data = "Список зарегистрированных пользователей:\n\n"
    for user_id, user_info in users_db.items():
        username = user_info.get("username", "None")
        user_text = (
            f"ID: <code>{user_id}</code>\n"
            f"Имя Фамилия: <code>{user_info.get('full_name', 'Не указано')}</code>\n"
            f"Телефон: +{user_info.get('phone', 'Не указан')}\n"
            f"Instagram: <code>{user_info.get('instagram', 'Не указан')}</code>\n"  # Добавлено поле Instagram
            f"Уровень: <code>{user_info.get('english_level', 'Не указан')}</code>\n"
            f"Возраст: <code>{user_info.get('age', 'Не указан')}</code>\n"
            f"Username: @{username}\n"
        )
        user_text += "\n"
        if len(data) + len(user_text) > 4000:  # Telegram лимит ≈4096 символов
            messages.append(data)
            data = user_text
        else:
            data += user_text
    messages.append(data)
    for msg in messages:
        bot.send_message(message.chat.id, msg, parse_mode="HTML")


# ==================================================================
# Скачивание базы данных в Excel-формате
@bot.message_handler(
    func=lambda message: message.text == "Скачать базу данных в $Excel$" and message.chat.id in ADMIN_IDS)
def download_database(message):
    if not users_db:
        bot.send_message(message.chat.id, "База данных пуста.")
        return

    file_path = "users_database.xlsx"
    data_list = []
    for user_id, user_info in users_db.items():
        record = user_info.copy()
        record["user_id"] = user_id
        # Если Instagram не был добавлен, то поле просто отсутствует, но его можно добавить по умолчанию:
        record.setdefault("instagram", "Не указан")
        if "registered_events" in record and isinstance(record["registered_events"], list):
            record["registered_events"] = "\n".join(record["registered_events"])
        data_list.append(record)
    df = pd.DataFrame(data_list)
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Users", index=False)
        worksheet = writer.sheets["Users"]
        for col_num, value in enumerate(df.columns.values):
            max_len = max(df[value].astype(str).map(len).max(), len(value))
            worksheet.set_column(col_num, col_num, max_len + 2)
    with open(file_path, "rb") as f:
        bot.send_document(message.chat.id, f)
    os.remove(file_path)


# ==================================================================
# Просмотр списка зарегистрированных пользователей по мероприятиям
@bot.message_handler(
    func=lambda message: message.text == "Посмотреть список зарегестрированных" and message.chat.id in ADMIN_IDS)
def show_registered_events_menu(message):
    markup = InlineKeyboardMarkup()
    for event in EVENT_LIST:
        city = event["city"].get("ru", event["city"].get("uz", ""))
        date = event["date"]
        time_ = event["time"]
        location = event["location"].get("ru", event["location"].get("uz", ""))
        btn_text = f"{city} | {date} | {time_} | {location}"
        button = InlineKeyboardButton(btn_text, callback_data=f"admin_view_{event['id']}")
        markup.add(button)
    bot.send_message(message.chat.id, "Выберите мероприятие:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_view_"))
def admin_view_event_registrations(call):
    admin_id = call.message.chat.id
    event_id = call.data.split("_")[-1]
    records = []
    for user_id, user_info in users_db.items():
        if "registered_events" in user_info:
            for reg in user_info["registered_events"]:
                if reg.startswith(f"{event_id}:"):
                    record = {
                        "Имя и Фамилия": user_info.get("full_name", "Не указано"),
                        "Телефон": user_info.get("phone", "Не указан"),
                        "Instagram": user_info.get("instagram", "Не указан"),  # Добавлено поле Instagram
                        "Уровень английского": user_info.get("english_level", "Не указан"),
                        "Возраст": user_info.get("age", "Не указан"),
                        "Telegram ID": user_id,
                        "Username": user_info.get("username", "Не указан"),
                        "Название Ивента": reg
                    }
                    records.append(record)
                    break
    if not records:
        bot.send_message(admin_id, "По данному мероприятию нет зарегистрированных пользователей.")
        return
    file_path = f"event_{event_id}_registrations.xlsx"
    df = pd.DataFrame(records)
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Registrations", index=False)
        worksheet = writer.sheets["Registrations"]
        for col_num, value in enumerate(df.columns.values):
            max_len = max(df[value].astype(str).map(len).max(), len(value))
            worksheet.set_column(col_num, col_num, max_len + 2)
    with open(file_path, "rb") as f:
        bot.send_document(admin_id, f)
    os.remove(file_path)

# ==================================================================
# Функционал рассылки сообщений
@bot.message_handler(func=lambda message: message.text == "Рассылка" and message.chat.id in ADMIN_IDS)
def broadcast_message_step1(message):
    bot.send_message(message.chat.id, "Введите текст для рассылки:\n(Для отмены введите 'Отмена')")
    bot.register_next_step_handler(message, broadcast_message)


def broadcast_message(message):
    if message.text.strip().lower() == "отмена":
        bot.send_message(message.chat.id, "Рассылка отменена.")
        return
    text = message.text
    successful = 0
    failed = 0
    for user_id in users_db:
        try:
            user_id_int = int(user_id)
            if user_id_int > 0:
                bot.send_message(user_id, text)
                successful += 1
        except Exception:
            failed += 1
    bot.send_message(
        message.chat.id,
        f"Сообщение успешно отправлено: {successful} пользователей.\nНевозможно отправить: {failed} пользователей."
    )


# ==================================================================
# Функционал статистики и аналитики
@bot.message_handler(func=lambda message: message.text == "Статистика" and message.chat.id in ADMIN_IDS)
def show_statistics(message):
    stats = {}
    for event in EVENT_LIST:
        event_id = event["id"]
        count = 0
        for user_info in users_db.values():
            registered = user_info.get("registered_events", [])
            if any(reg.startswith(f"{event_id}:") for reg in registered):
                count += 1
        stats[event_id] = count

    labels = []
    values_list = []
    for event in EVENT_LIST:
        event_id = event["id"]
        label = f"{event['city'].get('ru', 'N/A')} ({event['date']})"
        labels.append(label)
        values_list.append(stats.get(event_id, 0))

    plt.figure(figsize=(10, 6))
    plt.bar(labels, values_list, color="skyblue")
    plt.title("Количество регистраций по мероприятиям")
    plt.xlabel("Мероприятия")
    plt.ylabel("Количество регистраций")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    graph_path = "event_statistics.png"
    plt.savefig(graph_path)
    plt.close()
    with open(graph_path, "rb") as f:
        bot.send_photo(message.chat.id, f)
    os.remove(graph_path)


# ==================================================================
# Функционал замены файла events_list.py
@bot.message_handler(
    func=lambda message: message.text == "Изменить мероприятия (events_list.py)" and message.chat.id in ADMIN_IDS)
def request_file(message):
    bot.send_message(message.chat.id, "Отправьте файл с названием `events_list.py` для замены текущего файла.")


@bot.message_handler(content_types=["document"])
def handle_document(message):
    if message.chat.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой операции.")
        return

    document = message.document
    if not document.file_name.endswith(".py"):
        bot.send_message(message.chat.id, "Ошибка: файл должен иметь расширение .py.")
        return
    if document.file_name != "events_list.py":
        bot.send_message(message.chat.id, "Ошибка: имя файла должно быть `events_list.py`.")
        return

    try:
        file_info = bot.get_file(document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.send_message(message.chat.id, f"Не удалось скачать файл: {e}")
        return

    # Вычисляем BASE_DIR как родительскую директорию модуля ibrat_mock_bot,
    # предполагая, что admin.py находится в ibrat_mock_bot/handlers
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Формируем путь к файлу: BASE_DIR/feature/events_list.py
    target_path = os.path.join(BASE_DIR, "feature", "events_list.py")
    target_path = os.path.normpath(target_path)

    if os.path.exists(target_path):
        os.remove(target_path)

    try:
        with open(target_path, "wb") as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id, "Файл events_list.py успешно заменён!")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при сохранении файла: {e}")
        return

    try:
        importlib.reload(__import__("feature.events_list", fromlist=[""]))
        bot.send_message(message.chat.id, "Модуль events_list.py перезагружен.")
    except Exception as e:
        bot.send_message(message.chat.id,
                         f"Не удалось перезагрузить модуль автоматически: {e}\nПожалуйста, перезапустите бота вручную.")


# ==================================================================
print("Admin module loaded successfully.")
