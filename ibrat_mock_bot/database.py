#database.py
import json
import os

DB_FILE = "ibrat_users.json"

# Загружаем существующую базу данных или создаем новую
if os.path.exists(DB_FILE):  # Проверяем, существует ли файл
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            users_db = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        users_db = {}  # Если ошибка чтения JSON, создаем пустую базу
else:
    users_db = {}

# Временное хранилище данных пользователей в процессе регистрации
user_data = {}

# Функция для сохранения базы данных
def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users_db, f, indent=4, ensure_ascii=False)

def get_user_by_id(user_id):
    return users_db.get(str(user_id))  # Преобразуем ID в строку для поиска



print("Database module loaded successfully.")