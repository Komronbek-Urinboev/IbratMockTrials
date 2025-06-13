import time

SPAM_THRESHOLD = 1  # Максимальное число вызовов до игнорирования
SPAM_BLOCK_TIME = 10  # Время игнорирования в секундах

# В этой структуре для каждого пользователя сохраняем данные вида:
# { user_id: { action_key: [count, last_call_timestamp] } }
user_spam_data = {}


def check_spam(obj, action_key):
    user_id = obj.from_user.id
    now = time.time()

    if user_id not in user_spam_data:
        user_spam_data[user_id] = {}

    if action_key not in user_spam_data[user_id]:
        # Инициализируем счётчик и время последнего вызова
        user_spam_data[user_id][action_key] = [0, now]

    count, last_time = user_spam_data[user_id][action_key]

    # Если прошло больше SPAM_BLOCK_TIME секунд с последнего вызова, сбрасываем счётчик
    if now - last_time > SPAM_BLOCK_TIME:
        count = 0

    count += 1
    # Обновляем время последнего вызова
    user_spam_data[user_id][action_key] = [count, now]

    if count > SPAM_THRESHOLD:
        return True
    return False
