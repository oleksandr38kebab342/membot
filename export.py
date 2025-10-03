import sqlite3
import json

DB_PATH = 'data.db'

# Експортує всі таблиці у форматі JSON

def export_db_to_json():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tables = ['common', 'black', 'attempt', 'rating']
    export = {}
    for table in tables:
        cursor.execute(f'SELECT * FROM {table}')
        rows = cursor.fetchall()
        # Отримати назви колонок
        col_names = [desc[0] for desc in cursor.description]
        export[table] = [dict(zip(col_names, row)) for row in rows]
    conn.close()
    return json.dumps(export, ensure_ascii=False, indent=2)

# Для використання у боті:
# from export import export_db_to_json
# data = export_db_to_json()
# bot.send_document(chat_id, io.BytesIO(data.encode('utf-8')), filename='db_export.json')
