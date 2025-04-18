from telebot import TeleBot, types
from ibrat_mock_bot.handlers.events import *
from ibrat_mock_bot.database import save_db, user_data, users_db, DB_FILE
from ibrat_mock_bot.feature.bot_instance import bot
from ibrat_mock_bot.config import ADMIN_IDS
import json

# Доступные языки
LANGUAGES = {
    "en": "English",
    "ru": "Русский",
    "uz": "O'zbek tili"
}

MESSAGES = {
    "choose_lang": "Привет! Давайте начнем регистрацию на Ibrat Mock Trials.\n🌍 Выберите язык / Choose a language / Tilni tanlang:",
    "ask_name": {
        "en": "Enter your full name (Name Surname):",
        "ru": "Введите ваше имя и фамилию:",
        "uz": "Ismingiz va familiyangizni kiriting:"
    },
    "ask_phone": {
        "en": "📞 Share your phone number:",
        "ru": "📞 Поделитесь своим номером телефона:",
        "uz": "📞 Telefon raqamingizni ulashing:"
    },
    "ask_english": {
        "en": "Select your English level:",
        "ru": "Выберите ваш уровень английского:",
        "uz": "Ingliz til darajangizni tanlang:"
    },
    "ask_age": {
        "en": "Enter your age:",
        "ru": "Введите ваш возраст:",
        "uz": "Yoshingizni kiriting:"
    },
    "success": {
        "en": "Congratulations! You have successfully registered for Ibrat Mock Trials! 🎉\nTo sign up for the Mock Trials, enter the command /events",
        "ru": "Поздравляем! Вы успешно зарегистрированы в Ibrat Mock Trials! 🎉\nЧтобы записаться в Mock Trials введите команду /events",
        "uz": "Tabriklaymiz! Siz Ibrat Mock Trials ga muvaffaqiyatli ro'yxatdan o'tdingiz! 🎉\nMock Trials yozilish uchun /events buyrug'ini kiriting"
    }
}


# Уведомление администраторов
def notify_admins_about_registration(user_info):
    """Отправляет информацию о новом пользователе всем администраторам."""
    message = (
        "🎉 <b>Новый пользователь зарегистрировался:</b>\n"
        f"👤 <b>Имя Фамилия:</b> <code>{user_info['full_name']}</code>\n"
        f"📞 <b>Телефон:</b> +{user_info['phone']}\n"
        f"🇬🇧 <b>Уровень:</b> <code>{user_info['english_level']}</code>\n"
        f"🎂 <b>Возраст:</b> <code>{user_info['age']}</code>\n"
        f"🆔 <b>Telegram ID:</b> <code>{user_info['telegram_id']}</code>\n"
        f"📌 <b>Username:</b> @{user_info['username'] if user_info['username'] else 'Не указан'}"
    )

    for admin_id in ADMIN_IDS:
        bot.send_message(admin_id, message, parse_mode="HTML")


# Функция для создания inline-клавиатуры
def get_inline_markup(options):
    markup = types.InlineKeyboardMarkup()
    for key, value in options.items():
        markup.add(types.InlineKeyboardButton(value, callback_data=key))
    return markup


@bot.message_handler(commands=['language'])
def change_language(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("English", callback_data="lang_en"))
    markup.add(types.InlineKeyboardButton("Русский", callback_data="lang_ru"))
    markup.add(types.InlineKeyboardButton("O'zbek tili", callback_data="lang_uz"))

    bot.send_message(
        message.chat.id,
        "🌍 Выберите язык / Choose a language / Tilni tanlang:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    try:
        chosen_lang = call.data.split("_")[1]
        telegram_id = str(call.message.chat.id)

        if telegram_id not in users_db:
            users_db[telegram_id] = {}

        users_db[telegram_id]["lang"] = chosen_lang

        # Сохраняем изменения в базе данных
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(users_db, f, indent=4, ensure_ascii=False)

        # Тексты подтверждения
        confirmation_text = {
            "en": "✅ Language has been changed to English!\nTo return the button, use the command - /events",
            "ru": "✅ Язык был изменен на Русский!\nЧтобы вернуть кнопку, используйте команду - /events",
            "uz": "✅ Til o'zbek tiliga o'zgartirildi!\nTugmani qaytarish uchun - /events buyrug'idan foydalaning"
        }

        # Удаляем кнопки с помощью ReplyKeyboardRemove
        bot.send_message(
            call.message.chat.id,
            confirmation_text[chosen_lang],
            reply_markup=ReplyKeyboardRemove()  # Удаление клавиатуры
        )

        bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"[ERROR] - Ошибка в обработчике выбора языка: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка. Попробуйте снова.")


# Команда /start для начала регистрации
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    if user_id in users_db:
        lang = users_db[user_id].get("lang", "uz")  # по умолчанию uz
        already_registered_msg = {
            "en": "You are already registered! ✅",
            "ru": "Вы уже зарегистрированы! ✅",
            "uz": "Siz allaqachon ro'yxatdan o'tgansiz! ✅"
        }
        bot.send_message(message.chat.id, already_registered_msg[lang])
        return

    bot.send_message(message.chat.id, MESSAGES["choose_lang"], reply_markup=get_inline_markup(LANGUAGES))
    user_data[message.chat.id] = {}


# Обработчик выбора языка при регистрации
@bot.callback_query_handler(func=lambda call: call.data in LANGUAGES)
def choose_language(call):
    lang = call.data
    user_data[call.message.chat.id]["lang"] = lang
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, MESSAGES["ask_name"][lang])
    bot.register_next_step_handler(call.message, get_name)


# Остальные шаги регистрации
def get_name(message):
    lang = user_data[message.chat.id]["lang"]
    if len(message.text.split()) < 1:
        bot.send_message(message.chat.id, MESSAGES["ask_name"][lang])
        bot.register_next_step_handler(message, get_name)
        return
    user_data[message.chat.id]["full_name"] = message.text
    bot.send_message(message.chat.id, MESSAGES["ask_phone"][lang],
                     reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True).add(
                         types.KeyboardButton("📲 Share phone number", request_contact=True)))
    bot.register_next_step_handler(message, get_phone)


def get_phone(message):
    lang = user_data[message.chat.id]["lang"]
    if not message.contact:
        bot.send_message(message.chat.id, MESSAGES["ask_phone"][lang])
        bot.register_next_step_handler(message, get_phone)
        return
    user_data[message.chat.id]["phone"] = message.contact.phone_number
    remove_keyboard = types.ReplyKeyboardRemove()
    english_levels = {lvl: lvl for lvl in
                      ["Beginner", "Elementary", "Pre-Intermediate", "Intermediate", "Upper-Intermediate", "Advanced"]}
    bot.send_message(message.chat.id, MESSAGES["ask_english"][lang], reply_markup=get_inline_markup(english_levels))
    bot.send_message(message.chat.id, "🙃", reply_markup=remove_keyboard)


@bot.callback_query_handler(
    func=lambda call: call.data in ["Beginner", "Elementary", "Pre-Intermediate", "Intermediate", "Upper-Intermediate",
                                    "Advanced"])
def get_english_level(call):
    lang = user_data[call.message.chat.id]["lang"]
    user_data[call.message.chat.id]["english_level"] = call.data
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, MESSAGES["ask_age"][lang])
    bot.register_next_step_handler(call.message, get_age)


def get_age(message):
    lang = user_data[message.chat.id]["lang"]
    if not message.text.isdigit() or int(message.text) < 2:
        bot.send_message(message.chat.id, MESSAGES["ask_age"][lang])
        bot.register_next_step_handler(message, get_age)
        return
    user_data[message.chat.id]["age"] = int(message.text)
    user_data[message.chat.id]["telegram_id"] = message.chat.id
    user_data[message.chat.id]["username"] = message.from_user.username
    user_data[message.chat.id]["first_name"] = message.from_user.first_name
    users_db[str(message.chat.id)] = user_data[message.chat.id]
    save_db()

    # Уведомление администраторов о новом пользователе
    notify_admins_about_registration(users_db[str(message.chat.id)])

    bot.send_message(message.chat.id, MESSAGES["success"][lang])

print("Register module loaded successfully.")