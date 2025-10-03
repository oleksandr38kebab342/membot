import sqlite3

def get_db_connection():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    # Оновлення структури таблиць жартів
    for table in ['common', 'black', 'attempt']:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                user_id INTEGER
            )
        """)
    # Таблиця рейтингу
    cursor.execute('''CREATE TABLE IF NOT EXISTS rating (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        rate INTEGER DEFAULT 0
    )''')
    conn.commit()
    return conn

# Додаємо користувача або оновлюємо його рейтинг
def add_or_update_user_rating(user_id, username, points):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS rating (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        rate INTEGER DEFAULT 0
    )''')
    cursor.execute('SELECT rate FROM rating WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        cursor.execute('UPDATE rating SET rate = rate + ?, username = ? WHERE user_id = ?', (points, username, user_id))
    else:
        cursor.execute('INSERT INTO rating (user_id, username, rate) VALUES (?, ?, ?)', (user_id, username, points))
    conn.commit()
    conn.close()

# Отримати топ-7 користувачів
def get_top_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username, rate FROM rating ORDER BY rate DESC LIMIT 7')
    top = cursor.fetchall()
    conn.close()
    return top
