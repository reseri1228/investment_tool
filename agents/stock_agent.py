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
            status TEXT DEFAULT '관심',
            tag TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 기존 DB에 컬럼이 없으면 추가 (이미 쓰던 DB 보호)
    try:
        cursor.execute("ALTER TABLE stocks ADD COLUMN status TEXT DEFAULT '관심'")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE stocks ADD COLUMN tag TEXT DEFAULT ''")
    except:
        pass
    conn.commit()
    conn.close()

def add_stock(name, ticker, market, status="관심", tag=""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO stocks (name, ticker, market, status, tag) VALUES (?, ?, ?, ?, ?)",
        (name, ticker, market, status, tag)
    )
    conn.commit()
    conn.close()

def load_stocks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, ticker, market, status, tag FROM stocks ORDER BY created_at DESC")
    stocks = cursor.fetchall()
    conn.close()
    return stocks

def update_stock_status(stock_id, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE stocks SET status = ? WHERE id = ?", (status, stock_id))
    conn.commit()
    conn.close()

def update_stock_tag(stock_id, tag):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE stocks SET tag = ? WHERE id = ?", (tag, stock_id))
    conn.commit()
    conn.close()

def delete_stock(stock_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stocks WHERE id = ?", (stock_id,))
    conn.commit()
    conn.close()