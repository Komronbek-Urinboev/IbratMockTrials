# events.py

from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from ibrat_mock_bot.feature.bot_instance import bot
from ibrat_mock_bot.database import users_db, save_db  # Импорт функции сохранения БД
from ibrat_mock_bot.feature.events_list import EVENT_LIST
from ibrat_mock_bot.feature.REQUIRED_CHANNELS import REQUIRED_CHANNELS
from ibrat_mock_bot.languages.MESSAGES import MESSAGES
import qrcode
from io import BytesIO


def get_user_language(chat_id):
    user = users_db.get(str(chat_id))
    if user and "lang" in user:  # Если в записи указан язык
        return user["lang"]
    return "uz"  # Язык по умолчанию


def show_main_menu(chat_id):
    lang = get_user_language(chat_id)
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(MESSAGES["register_button"][lang]))
    bot.send_message(chat_id, MESSAGES["choose_action"][lang], reply_markup=markup)


def get_translated_event_data(event, lang):
    """Получает переводы для города и места проведения."""
    return {
        "city": event["city"].get(lang, event["city"]["uz"]),
        "location": event["location"].get(lang, event["location"]["uz"])
    }


# Функция для сохранения информации о регистрации мероприятия в БД
def save_event_to_user_db(chat_id, event):
    # Формируем строку с данными о мероприятии, используя русский перевод (можно адаптировать под выбранный язык)
    event_info = (
        f"{event['id']}: {event['city']['ru']} + {event['date']} + {event['time']} + "
        f"{event['location']['ru']} + {event['group']['ru']}"
    )
    user = users_db.get(str(chat_id), {})
    if "registered_events" not in user:
        user["registered_events"] = []
    user["registered_events"].append(event_info)
    users_db[str(chat_id)] = user
    save_db()  # Сохраняем изменения в файле ibrat_users.json


@bot.message_handler(func=lambda message: message.text in [MESSAGES["register_button"][lang] for lang in MESSAGES["register_button"]])
def show_events(message):
    chat_id = message.chat.id
    lang = get_user_language(chat_id)
    markup = InlineKeyboardMarkup()
    for event in EVENT_LIST:
        translated = get_translated_event_data(event, lang)
        btn_text = f"{translated['city']} | {event['date']} | {event['time']} | {translated['location']}"
        btn = InlineKeyboardButton(btn_text, callback_data=f"register_{event['id']}")
        markup.add(btn)
    markup.add(InlineKeyboardButton(MESSAGES["cancel"][lang], callback_data="cancel"))
    bot.send_message(chat_id, MESSAGES["choose_event"][lang], reply_markup=markup)


# После выбора ивента отправляем инструкции по обязательной подписке на каналы
@bot.callback_query_handler(func=lambda call: call.data.startswith("register_"))
def confirm_registration(call):
    chat_id = call.message.chat.id
    lang = get_user_language(chat_id)
    event_id = call.data.split("_")[1]
    user = users_db.get(str(chat_id))

    if not user:
        bot.send_message(chat_id, MESSAGES["not_registered"][lang])
        return

    markup = InlineKeyboardMarkup()
    for channel in REQUIRED_CHANNELS:
        markup.add(InlineKeyboardButton(channel["name"], url=channel["link"]))
    markup.add(InlineKeyboardButton(MESSAGES["check_subscription"][lang], callback_data=f"check_sub_{event_id}"))
    bot.send_message(chat_id, MESSAGES["subscribe_channels"][lang], reply_markup=markup)


# Проверка подписки на каналы и завершение регистрации
@bot.callback_query_handler(func=lambda call: call.data.startswith("check_sub_"))
def check_subscription(call):
    chat_id = call.message.chat.id
    lang = get_user_language(chat_id)
    # Извлекаем event_id из callback_data
    event_id = call.data.split("_")[2].strip()
    message_id = call.message.message_id

    try:
        user_subscribed = all(
            bot.get_chat_member(channel["id"], chat_id).status in ["member", "administrator", "creator"]
            for channel in REQUIRED_CHANNELS
        )
    except Exception as e:
        bot.send_message(chat_id, f"{MESSAGES['subscription_error'][lang]}: {str(e)}")
        return

    event = next((e for e in EVENT_LIST if str(e["id"]).strip() == event_id), None)
    if event is None:
        bot.send_message(chat_id, MESSAGES["event_not_found"][lang])
        return

    user_info = users_db.get(str(chat_id), {})

    if user_subscribed:
        # Функция для получения детальных переводов (включая группу)
        def get_translated_event_data_detail(event, lang):
            return {
                "city": event["city"].get(lang, event["city"]["uz"]),
                "location": event["location"].get(lang, event["location"]["uz"]),
                "group": event["group"].get(lang, event["group"]["uz"])
            }

        translated = get_translated_event_data_detail(event, lang)
        event_text = (
            f"{MESSAGES['registration_success_event'][lang].splitlines()[0]}\n\n"
            f"{MESSAGES['event_data_label'][lang]}\n\n"
            f"{MESSAGES['qr_label_location'][lang]} - {translated['location']}\n"
            f"{MESSAGES['qr_label_city'][lang]} - {translated['city']}\n"
            f"{MESSAGES['qr_label_date'][lang]} - {event['date']}\n"
            f"{MESSAGES['qr_label_time'][lang]} - {event['time']}\n\n"
            f"{translated['group']}"
        )

        # Формируем QR-код с данными пользователя и события
        qr_data = (
            f"{MESSAGES['registration_success_event'][lang].splitlines()[0]}\n\n"
            f"{MESSAGES['event_data_label'][lang]}\n\n"
            f"{MESSAGES['qr_label_location'][lang]} - {translated['location']}\n"
            f"{MESSAGES['qr_label_city'][lang]} - {translated['city']}\n"
            f"{MESSAGES['qr_label_date'][lang]} - {event['date']}\n"
            f"{MESSAGES['qr_label_time'][lang]} - {event['time']}\n\n"
            f"{MESSAGES['qr_label_group'][lang]}: {translated['group']}\n\n"
            f"{MESSAGES['user_name_label'][lang]}: {user_info.get('full_name', 'Не указано')}\n"
            f"{MESSAGES['user_phone_label'][lang]}: {user_info.get('phone', 'Не указано')}\n"
            f"{MESSAGES['user_english_level_label'][lang]}: {user_info.get('english_level', 'Не указано')}\n"
            f"{MESSAGES['user_age_label'][lang]}: {user_info.get('age', 'Не указано')}\n"
            f"{MESSAGES['user_id_label'][lang]}: {chat_id}\n"
            f"{MESSAGES['user_username_label'][lang]}: @{user_info.get('username', 'Не указано')}"
        )

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")
        qr_io = BytesIO()
        img.save(qr_io, format="PNG")
        qr_io.seek(0)

        bot.send_message(chat_id, event_text, parse_mode="HTML")
        bot.send_photo(chat_id, qr_io, caption=MESSAGES["qr_caption"][lang])

        # После отправки поздравления и QR-кода – сохраняем данные регистрации в БД
        save_event_to_user_db(chat_id, event)

    else:
        bot.delete_message(chat_id, message_id)
        markup = InlineKeyboardMarkup()
        for channel in REQUIRED_CHANNELS:
            markup.add(InlineKeyboardButton(channel["name"], url=channel["link"]))
        markup.add(InlineKeyboardButton(MESSAGES["check_subscription"][lang], callback_data=f"check_sub_{event_id}"))
        bot.send_message(chat_id, MESSAGES["subscribe_channels"][lang], reply_markup=markup)


@bot.message_handler(commands=["events"])
def start_command(message):
    chat_id = message.chat.id
    lang = get_user_language(chat_id)
    show_main_menu(chat_id)


@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_registration(call):
    lang = get_user_language(call.message.chat.id)
    bot.send_message(call.message.chat.id, MESSAGES["registration_cancelled"][lang], reply_markup=ReplyKeyboardRemove())


print("Events_test module loaded successfully.")
