
import sqlite3
import json


DB_PATH = 'data.db'
BLACK_JSON = 'Чорні.json'

def clean_joke(joke):
    joke = joke.strip()
    if joke.startswith('"') and joke.endswith('"'):
        joke = joke[1:-1]
    if not joke:
        return None
    return joke

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS common (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        user_id INTEGER
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS black (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        user_id INTEGER
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS attempt (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        user_id INTEGER
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS rating (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        rate INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

def migrate_black_jokes():
    with open(BLACK_JSON, 'r', encoding='utf-8') as f:
        jokes = json.load(f)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for joke in jokes:
        cleaned = clean_joke(joke)
        if cleaned:
            cursor.execute('INSERT INTO black (data) VALUES (?)', (cleaned,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    migrate_black_jokes()
    print("Database initialized and black jokes migrated.")
