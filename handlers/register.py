from telebot import TeleBot, types
from handlers.events import *
from database import save_db, user_data, users_db, DB_FILE
from feature.bot_instance import bot
from config import ADMIN_IDS
import json
from feature.antispam import *

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
    "ask_instagram": {  # Новый ключ для Instagram
        "en": "Share your Instagram account:",
        "ru": "Поделитесь своим аккаунтом в Instagram:",
        "uz": "Instagram akkauntingizni ulashing:"
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

MESSAGES.update({
    "instagram_updated": {
        "en": "Your Instagram account has been updated. ✅",
        "ru": "Ваш аккаунт в Instagram обновлен. ✅",
        "uz": "Instagram akkauntingiz yangilandi. ✅"
    }
})

# Уведомление администраторов
def notify_admins_about_registration(user_info):
    """Отправляет информацию о новом пользователе всем администраторам."""
    message = (
        "🎉 <b>Новый пользователь зарегистрировался:</b>\n"
        f"👤 <b>Имя Фамилия:</b> <code>{user_info['full_name']}</code>\n"
        f"👉Instagram👈: {user_info.get('instagram', 'Не указано')}\n"
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
    if check_spam(message, "language"):
        return  # Если спам – завершаем выполнение
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
# ==================================================================
# Команда /start для начала или проверки регистрации
@bot.message_handler(commands=['start'])
def start(message):
    if check_spam(message, "start"):
        return  # Если спам – завершаем выполнение
    user_id = str(message.chat.id)

    # Если пользователь уже зарегистрирован, проверяем наличие Instagram
    if user_id in users_db:
        lang = users_db[user_id].get("lang", "uz")
        # Если Instagram отсутствует или пуст, запрашиваем его
        if "instagram" not in users_db[user_id] or not users_db[user_id]["instagram"]:
            bot.send_message(message.chat.id, MESSAGES["ask_instagram"][lang])
            bot.register_next_step_handler(message, update_instagram)
            return

        # Если Instagram уже указан, стандартное сообщение о регистрации
        already_registered_msg = {
            "en": "You are already registered! ✅\nEnter the command /events to register for Ibrat Mock Trials",
            "ru": "Вы уже зарегистрированы! ✅\nВведите команду /events чтобы зарегистрироваться на Ibrat Mock Trials",
            "uz": "Siz allaqachon ro'yxatdan o'tgansiz! ✅\n/events buyrug‘ini kiriting va Ibrat Mock Trials uchun ro‘yxatdan o‘ting"
        }
        bot.send_message(message.chat.id, already_registered_msg[lang])
        return

    # Если пользователь не зарегистрирован – начинаем регистрацию с выбора языка
    bot.send_message(message.chat.id, MESSAGES["choose_lang"], reply_markup=get_inline_markup(LANGUAGES))
    user_data[message.chat.id] = {}

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    lang = "uz"  # язык по умолчанию
    if user_id in users_db:
        lang = users_db[user_id].get("lang", "uz")

    help_texts = {
        "ru": (
            "<b>Команды бота:</b>\n"
            "• /start - Обновить бота\n"
            "• /events - Подать заявку на участие в Mock Trials\n"
            "• /language - Установить язык\n"
            "• /help - Помощь\n\n"
            "<b>Bot:</b> Официальный бот Ibrat Mock Trials — присоединяйтесь, "
            "регистрируйтесь и следите за юридическими сессиями по всему Узбекистану.\n"
            "<b>Канал:</b> @IbratMockTrials\n"
            "<b>Вопросы:</b> @mocktrial_support\n\n"
            "<b>Организаторы:</b>"
        ),
        "en": (
            "<b>Bot Commands:</b>\n"
            "• /start - Refresh bot\n"
            "• /events - Apply for Mock Trials\n"
            "• /language - Set the language\n"
            "• /help - Help\n\n"
            "<b>Bot:</b> Official bot of Ibrat Mock Trials — join, register, and stay updated "
            "on Uzbekistan’s nationwide legal sessions.\n"
            "<b>Channel:</b> @IbratMockTrials\n"
            "<b>For inquiries:</b> @mocktrial_support\n\n"
            "<b>Organizers:</b>"
        ),
        "uz": (
            "<b>Bot buyruqlari:</b>\n"
            "• /start - Botni yangilash\n"
            "• /events - Mock Trials da qatnashish\n"
            "• /language - Tilni o'zgartirish\n"
            "• /help - Yordam\n\n"
            "<b>Bot:</b> Ibrat Mock Trials rasmiy boti — qo‘shiling, ro‘yxatdan o‘ting va "
            "O‘zbekistondagi huquqiy sessiyalar yangiliklaridan xabardor bo‘ling.\n"
            "<b>Kanal:</b> @IbratMockTrials\n"
            "<b>Savollar uchun:</b> @mocktrial_support\n\n"
            "<b>Tashkilotchilar:</b>"
        )
    }

    # --- inline кнопки для организаторов ---
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Oybek Abdullaev", url="https://t.me/ysjshoe"))
    markup.add(InlineKeyboardButton("Asadbek Oltinov", url="https://t.me/asadbekoltinov"))
    markup.add(InlineKeyboardButton("Khabibulloh Abdullahonov", url="https://t.me/Khabi0208"))
    markup.add(InlineKeyboardButton("Bot orqali qanday ro‘yxatdan o‘tiladi?", url="https://telegra.ph/How-to-register-Ibrat-Mock-Trials-09-07"))

    bot.send_message(message.chat.id, help_texts[lang], reply_markup=markup, parse_mode="HTML")

# ==================================================================
# Обработчик для обновления Instagram аккаунта
def update_instagram(message):
    user_id = str(message.chat.id)
    lang = users_db.get(user_id, {}).get("lang", "uz")
    if not message.text:
        bot.send_message(message.chat.id, MESSAGES["ask_instagram"][lang])
        bot.register_next_step_handler(message, update_instagram)
        return
    # Обновляем профиль пользователя и сохраняем в базу данных
    users_db[user_id]["instagram"] = message.text
    save_db()
    instagram_updated_msg = MESSAGES["instagram_updated"][lang]
    bot.send_message(message.chat.id, instagram_updated_msg)

# Обработчик выбора языка при регистрации
@bot.callback_query_handler(func=lambda call: call.data in LANGUAGES)
def choose_language(call):
    lang = call.data
    user_data[call.message.chat.id]["lang"] = lang
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, MESSAGES["ask_name"][lang])
    bot.register_next_step_handler(call.message, get_name)


def get_name(message):
    lang = user_data[message.chat.id]["lang"]
    if len(message.text.split()) < 1:
        bot.send_message(message.chat.id, MESSAGES["ask_name"][lang])
        bot.register_next_step_handler(message, get_name)
        return
    user_data[message.chat.id]["full_name"] = message.text

    # Запрашиваем аккаунт в Instagram
    bot.send_message(message.chat.id, MESSAGES["ask_instagram"][lang])
    bot.register_next_step_handler(message, get_instagram)


def get_instagram(message):
    lang = user_data[message.chat.id]["lang"]
    if not message.text:
        bot.send_message(message.chat.id, MESSAGES["ask_instagram"][lang])
        bot.register_next_step_handler(message, get_instagram)
        return
    user_data[message.chat.id]["instagram"] = message.text

    # После получения аккаунта Instagram, переходим к запросу номера телефона
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(types.KeyboardButton("📲 Share phone number", request_contact=True))
    bot.send_message(message.chat.id, MESSAGES["ask_phone"][lang], reply_markup=markup)
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
