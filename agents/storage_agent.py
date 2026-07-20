import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = "data/investment.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_memo(title, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    kst_now = (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO memos (title, content, created_at) VALUES (?, ?, ?)", (title, content, kst_now))
    conn.commit()
    conn.close()

def load_memos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, created_at FROM memos ORDER BY created_at DESC")
    memos = cursor.fetchall()
    conn.close()
    return memos
def delete_memo(memo_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memos WHERE id = ?", (memo_id,))
    conn.commit()
    conn.close()

def update_memo(memo_id, new_content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE memos SET content = ? WHERE id = ?", (new_content, memo_id))
    conn.commit()
    conn.close()