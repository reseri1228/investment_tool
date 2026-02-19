import sqlite3

DB_PATH = "data/investment.db"

def init_stock_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            ticker TEXT,
            market TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_stock(name, ticker, market):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stocks (name, ticker, market) VALUES (?, ?, ?)", 
                   (name, ticker, market))
    conn.commit()
    conn.close()

def load_stocks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, ticker, market FROM stocks ORDER BY created_at DESC")
    stocks = cursor.fetchall()
    conn.close()
    return stocks

def delete_stock(stock_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stocks WHERE id = ?", (stock_id,))
    conn.commit()
    conn.close()