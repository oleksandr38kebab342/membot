# if __name__ == "__main__":
#     while True:
#         try:
#             bot.polling(none_stop=True, timeout=60)
#         except Exception as e:
#             print(f"Error occurred: {e}")
#             bot.stop_polling()
#             time.sleep(10)
import telebot
from telebot import types
import random
import os
import uuid
import json
import sqlite3
import time  


ключ = '7263357915:AAGlhHrShoDVhwRPunuc5JFcfTWjQQ6ZOnQ'
bot = telebot.TeleBot(ключ)

ADMIN_USERS = [824228525]

def initialize_json_file(filename):
    if not os.path.exists(filename) or os.stat(filename).st_size == 0:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([], f)

for filename in ['Звичайні.json', 'Чорні.json', 'Проби.json']:
    initialize_json_file(filename)

jokes_to_approve = {}

def get_db_connection():
    return sqlite3.connect('data.db')

def load_jokes_from_db(table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, data FROM {table_name}")
    jokes = cursor.fetchall()  # повертає список (id, data)
 # jokes_to_approve більше не використовується
    return jokes

def save_joke_to_db(table_name, joke):
    # joke має бути tuple: (text, user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, user_id INTEGER)")
    cursor.execute(f"INSERT INTO {table_name} (data, user_id) VALUES (?, ?)", joke)
    conn.commit()
    conn.close()

def delete_joke_from_attempt(joke):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attempt WHERE data = ?", (joke,))
    conn.commit()
    conn.close()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Звичайні жарти")
    btn2 = types.KeyboardButton("Чорні жарти")
    btn3 = types.KeyboardButton("Відправити анекдот")
    buttons = [btn1, btn2, btn3]
    btn5 = types.KeyboardButton("Рейтинг")
    buttons.append(btn5)
    # Додаємо кнопку "Одобрення" лише для модератора
    if message.from_user.id in ADMIN_USERS:
        btn4 = types.KeyboardButton("Одобрення")
        buttons.append(btn4)
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Привіт! Обери тип жартів або надішли свій анекдот:", reply_markup=markup)

@bot.message_handler(commands=['comicchnu'])
def send_chat_id(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, f"Your chat ID is: {chat_id}")

@bot.message_handler(func=lambda message: message.text in ["Звичайні жарти", "Чорні жарти", "Відправити анекдот", "Одобрення"])
def handle_joke_request(message):
    if message.text == "Рейтинг":
        import rating
        top = rating.get_top_users()
        if top:
            msg = "Топ 7 користувачів за рейтингом:\n"
            for i, (username, rate) in enumerate(top, 1):
                msg += f"{i}. {username}: {rate} балів\n"
            bot.send_message(message.chat.id, msg)
        else:
            bot.send_message(message.chat.id, "Ще немає користувачів з балами.")
    if message.text == "Одобрення" and message.from_user.id in ADMIN_USERS:
        jokes = load_jokes_from_db('attempt')
        if jokes:
            joke_id, joke_text = jokes[0]
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("Звичайні", callback_data=f"approve_usual|{joke_id}")
            btn2 = types.InlineKeyboardButton("Чорні", callback_data=f"approve_black|{joke_id}")
            btn3 = types.InlineKeyboardButton("Видалити", callback_data=f"delete|{joke_id}")
            markup.add(btn1, btn2, btn3)
            bot.send_message(message.chat.id, f"Анекдот на одобрення:\n\n{joke_text}", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Немає жартів на одобрення.")
    if message.text == "Звичайні жарти":
        jokes = load_jokes_from_db('common')
        if jokes:
            joke_text = random.choice(jokes)[1]  # беремо лише текст
            bot.send_message(message.chat.id, joke_text)
        else:
            bot.send_message(message.chat.id, "Вибачте, але зараз немає звичайних жартів.")
    elif message.text == "Чорні жарти":
        jokes = load_jokes_from_db('black')
        if jokes:
            joke_text = random.choice(jokes)[1]
            bot.send_message(message.chat.id, joke_text)
        else:
            bot.send_message(message.chat.id, "Вибачте, але зараз немає чорних жартів.")
    elif message.text == "Відправити анекдот":
        msg = bot.send_message(message.chat.id, "Надішліть свій анекдот:")
        bot.register_next_step_handler(msg, save_user_joke)

def save_user_joke(message):
    joke = message.text
    joke_id = str(uuid.uuid4())
    jokes_to_approve[joke_id] = joke
    save_joke_to_db('attempt', (joke, message.from_user.id))
    bot.send_message(message.chat.id, "Дякуємо! Ваш анекдот було збережено для перевірки.")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM attempt")
    count = cursor.fetchone()[0]
    conn.close()
    # Пороги для сповіщень: 8, 15, 22, ...
    threshold = 7
    notify = False
    if count > threshold:
        if (count - threshold) % 7 == 1:
            notify = True
    if notify:
        for admin_id in ADMIN_USERS:
            bot.send_message(admin_id, "Є нові анекдоти на одобрення! Натисніть кнопку 'Одобрення'.")
@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('delete'))
def handle_approval(call):
    action, joke_id = call.data.split('|', 1)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT data FROM attempt WHERE id = ?", (joke_id,))
        result = cursor.fetchone()
        if not result:
            bot.send_message(call.message.chat.id, "Помилка: анекдот не знайдено або вже оброблений.")
            # Видаляємо повідомлення з кнопками
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            conn.close()
            return
        joke_text = result[0]
        # Отримуємо user_id для рейтингу
        cursor.execute("SELECT user_id FROM attempt WHERE id = ?", (joke_id,))
        user_row = cursor.fetchone()
        user_id = user_row[0] if user_row else None
        username = None
        # Отримуємо username через get_chat (можна додати кешування)
        if user_id:
            try:
                user = bot.get_chat(user_id)
                username = user.username or str(user_id)
            except Exception:
                username = str(user_id)
        # Видаляємо повідомлення з кнопками після вибору дії
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        import rating
        if action == 'approve_usual':
            save_joke_to_db('common', (joke_text, user_id))
            cursor.execute("DELETE FROM attempt WHERE id = ?", (joke_id,))
            conn.commit()
            if user_id:
                rating.add_or_update_user_rating(user_id, username, 5)
            bot.send_message(call.message.chat.id, "Анекдот додано до звичайних жартів.")
        elif action == 'approve_black':
            save_joke_to_db('black', (joke_text, user_id))
            cursor.execute("DELETE FROM attempt WHERE id = ?", (joke_id,))
            conn.commit()
            if user_id:
                rating.add_or_update_user_rating(user_id, username, 10)
            bot.send_message(call.message.chat.id, "Анекдот додано до чорних жартів.")
        elif action == 'delete':
            cursor.execute("DELETE FROM attempt WHERE id = ?", (joke_id,))
            conn.commit()
            if user_id:
                rating.add_or_update_user_rating(user_id, username, 0)
            bot.send_message(call.message.chat.id, "Анекдот видалено.")
        else:
            bot.send_message(call.message.chat.id, "Невідома дія!")
        # Показуємо наступний анекдот, якщо є
        cursor.execute("SELECT id, data FROM attempt")
        next_joke_row = cursor.fetchone()
        if next_joke_row:
            next_joke_id, next_joke_text = next_joke_row
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("Звичайні", callback_data=f"approve_usual|{next_joke_id}")
            btn2 = types.InlineKeyboardButton("Чорні", callback_data=f"approve_black|{next_joke_id}")
            btn3 = types.InlineKeyboardButton("Видалити", callback_data=f"delete|{next_joke_id}")
            markup.add(btn1, btn2, btn3)
            bot.send_message(call.message.chat.id, f"Анекдот на одобрення:\n\n{next_joke_text}", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, "Немає жартів на одобрення.")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Виникла помилка: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"Error occurred: {e}")
            bot.stop_polling()
            time.sleep(10)