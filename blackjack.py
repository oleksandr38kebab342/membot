import logging
import time

import telebot
from telebot import types

import config
import db
import repositories
import scheduler
import services


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

if not config.BOT_TOKEN:
    raise SystemExit("BOT_TOKEN is required. Set it as an environment variable.")

bot = telebot.TeleBot(config.BOT_TOKEN, threaded=True, num_threads=8)


def build_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Звичайні жарти")
    btn2 = types.KeyboardButton("Чорні жарти")
    btn3 = types.KeyboardButton("Відправити анекдот")
    btn4 = types.KeyboardButton("Рейтинг")
    btn5 = types.KeyboardButton(config.PROFILE_BUTTON)
    buttons = [btn1, btn2, btn3, btn4, btn5]
    if user_id in config.ADMIN_USERS:
        buttons.append(types.KeyboardButton("Одобрення"))
    markup.add(*buttons)
    return markup


def safe_handler(handler):
    def wrapper(message):
        try:
            return handler(message)
        except Exception:
            logger.exception("Handler error")
            try:
                bot.send_message(message.chat.id, "Сталася помилка. Спробуйте пізніше.")
            except Exception:
                pass
    return wrapper


def safe_callback(handler):
    def wrapper(call):
        try:
            return handler(call)
        except Exception:
            logger.exception("Callback error")
            try:
                bot.send_message(call.message.chat.id, "Сталася помилка. Спробуйте пізніше.")
            except Exception:
                pass
    return wrapper


def ensure_user(message):
    username = message.from_user.username or str(message.from_user.id)
    repositories.upsert_user(message.from_user.id, username)
    return username

@bot.message_handler(commands=['start'])
@safe_handler
def send_welcome(message):
    ensure_user(message)
    markup = build_main_menu(message.from_user.id)
    bot.send_message(message.chat.id, "Привіт! Обери тип жартів або надішли свій анекдот:", reply_markup=markup)

@bot.message_handler(commands=['comicchnu'])
@safe_handler
def send_chat_id(message):
    ensure_user(message)
    chat_id = message.chat.id
    bot.send_message(chat_id, f"Your chat ID is: {chat_id}")


@bot.message_handler(commands=['profile'])
@safe_handler
def profile_command(message):
    ensure_user(message)
    show_profile(message)

@bot.message_handler(func=lambda message: message.text in ["Звичайні жарти", "Чорні жарти", "Відправити анекдот", "Одобрення", "Рейтинг", config.PROFILE_BUTTON])
@safe_handler
def handle_joke_request(message):
    ensure_user(message)
    if message.text == "Рейтинг":
        top = repositories.get_top_users()
        if top:
            msg = "Топ 7 користувачів за рейтингом:\n"
            for i, (username, rate) in enumerate(top, 1):
                msg += f"{i}. {username}: {rate} балів\n"
            bot.send_message(message.chat.id, msg)
        else:
            bot.send_message(message.chat.id, "Ще немає користувачів з балами.")
        return
    if message.text == config.PROFILE_BUTTON:
        show_profile(message)
        return
    if message.text == "Одобрення" and message.from_user.id in config.ADMIN_USERS:
        joke = repositories.get_random_attempt()
        if joke:
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("Звичайні", callback_data=f"approve_usual|{joke.id}")
            btn2 = types.InlineKeyboardButton("Чорні", callback_data=f"approve_black|{joke.id}")
            btn3 = types.InlineKeyboardButton("Видалити", callback_data=f"delete|{joke.id}")
            markup.add(btn1, btn2, btn3)
            bot.send_message(message.chat.id, f"Анекдот на одобрення:\n\n{joke.data}", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Немає жартів на одобрення.")
        return
    if message.text == "Звичайні жарти":
        joke = repositories.get_random_joke("common")
        if joke:
            bot.send_message(message.chat.id, joke.data)
        else:
            bot.send_message(message.chat.id, "Вибачте, але зараз немає звичайних жартів.")
        return
    if message.text == "Чорні жарти":
        joke = repositories.get_random_joke("black")
        if joke:
            bot.send_message(message.chat.id, joke.data)
        else:
            bot.send_message(message.chat.id, "Вибачте, але зараз немає чорних жартів.")
        return
    if message.text == "Відправити анекдот":
        msg = bot.send_message(message.chat.id, "Надішліть свій анекдот:")
        bot.register_next_step_handler(msg, save_user_joke)

@safe_handler
def save_user_joke(message):
    ensure_user(message)
    joke = (message.text or "").strip()
    if not joke:
        bot.send_message(message.chat.id, "Анекдот не може бути порожнім. Спробуйте ще раз.")
        return
    can_submit, wait_seconds = services.can_submit_joke(message.from_user.id, config.COOLDOWN_SECONDS)
    if not can_submit:
        bot.send_message(message.chat.id, f"Зачекайте {wait_seconds} сек перед наступним анекдотом.")
        return
    services.record_joke_submission(message.from_user.id)
    repositories.add_attempt_joke(joke, message.from_user.id)
    bot.send_message(message.chat.id, "Дякуємо! Ваш анекдот було збережено для перевірки.")

    count = repositories.count_attempts()
    threshold = 7
    notify = False
    if count > threshold and (count - threshold) % 7 == 1:
        notify = True
    if notify:
        for admin_id in config.ADMIN_USERS:
            bot.send_message(admin_id, "Є нові анекдоти на одобрення! Натисніть кнопку 'Одобрення'.")
@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('delete'))
@safe_callback
def handle_approval(call):
    action, joke_id = call.data.split('|', 1)
    joke = repositories.get_attempt_by_id(joke_id)
    if not joke:
        bot.send_message(call.message.chat.id, "Помилка: анекдот не знайдено або вже оброблений.")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        return
    user = repositories.get_user(joke.user_id) if joke.user_id else None
    username = user.username if user else str(joke.user_id)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    if action == 'approve_usual':
        repositories.add_common_joke(joke.data, joke.user_id)
        repositories.delete_attempt_by_id(joke.id)
        if joke.user_id:
            repositories.add_or_update_user_rating(joke.user_id, username, 5, accepted_inc=1)
        bot.send_message(call.message.chat.id, "Анекдот додано до звичайних жартів.")
    elif action == 'approve_black':
        repositories.add_black_joke(joke.data, joke.user_id)
        repositories.delete_attempt_by_id(joke.id)
        if joke.user_id:
            repositories.add_or_update_user_rating(joke.user_id, username, 10, accepted_inc=1)
        bot.send_message(call.message.chat.id, "Анекдот додано до чорних жартів.")
    elif action == 'delete':
        repositories.delete_attempt_by_id(joke.id)
        bot.send_message(call.message.chat.id, "Анекдот видалено.")
    else:
        bot.send_message(call.message.chat.id, "Невідома дія!")
    next_joke = repositories.get_random_attempt()
    if next_joke:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Звичайні", callback_data=f"approve_usual|{next_joke.id}")
        btn2 = types.InlineKeyboardButton("Чорні", callback_data=f"approve_black|{next_joke.id}")
        btn3 = types.InlineKeyboardButton("Видалити", callback_data=f"delete|{next_joke.id}")
        markup.add(btn1, btn2, btn3)
        bot.send_message(call.message.chat.id, f"Анекдот на одобрення:\n\n{next_joke.data}", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "Немає жартів на одобрення.")


def show_profile(message):
    profile = repositories.get_user_profile(message.from_user.id)
    if not profile:
        bot.send_message(message.chat.id, "У вас поки немає рейтингу.")
        return
    msg = (
        f"Профіль: {profile['username']}\n"
        f"Бали: {profile['rate']}\n"
        f"Прийняті жарти: {profile['accepted_count']}\n"
        f"Місце в рейтингу: {profile['rank']}"
    )
    bot.send_message(message.chat.id, msg)

if __name__ == "__main__":
    db.init_db()
    scheduler.start_joke_of_day_scheduler(bot, config.JOKE_DAY_TIME, config.TIMEZONE)
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"Error occurred: {e}")
            bot.stop_polling()
            time.sleep(10)