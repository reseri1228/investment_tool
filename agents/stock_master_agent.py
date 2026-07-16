import os
import io
import sqlite3
import zipfile
import urllib.request
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/investment.db")

KOSPI_URL = "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip"
KOSDAQ_URL = "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip"


def init_stock_master_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_master (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            market TEXT NOT NULL,
            type TEXT DEFAULT 'STOCK',
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def needs_update():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT updated_at FROM stock_master LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if not row:
            return True
        return row[0] != str(date.today())
    except:
        return True


def parse_mst_file(data: bytes, market: str):
    results = []
    try:
        f = io.TextIOWrapper(io.BytesIO(data), encoding="cp949", errors="ignore")
        for line in f:
            if len(line) < 9:
                continue
            code = line[0:9].strip()
            # 종목명은 고정 오프셋에 위치
            name = line[21:].strip()
            # 종목명만 추출 (첫 번째 공백 이후 잘라냄)
            if name:
                name = name.split()[0] if name.split() else name
            if code and name:
                results.append((code, name, market, "STOCK", str(date.today())))
    except Exception as e:
        print(f"파싱 오류: {e}")
    return results


def download_and_parse(url: str, market: str):
    try:
        with urllib.request.urlopen(url, timeout=30) as res:
            zip_data = res.read()
        with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
            mst_name = [n for n in z.namelist() if n.endswith(".mst")][0]
            mst_data = z.read(mst_name)
        return parse_mst_file(mst_data, market)
    except Exception as e:
        print(f"{market} 마스터파일 다운로드 실패: {e}")
        return []


def update_stock_master():
    try:
        kospi = download_and_parse(KOSPI_URL, "KOSPI")
        kosdaq = download_and_parse(KOSDAQ_URL, "KOSDAQ")
        all_stocks = kospi + kosdaq

        if not all_stocks:
            print("데이터 없음 — 기존 DB 유지")
            return False

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT OR REPLACE INTO stock_master (code, name, market, type, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, all_stocks)
        conn.commit()
        conn.close()
        print(f"종목 마스터 갱신 완료: {len(all_stocks)}개")
        return True
    except Exception as e:
        print(f"갱신 실패 — 기존 DB 유지: {e}")
        return False


def auto_update_if_needed():
    init_stock_master_db()
    if needs_update():
        print("종목 마스터 갱신 중...")
        update_stock_master()


def search_stock_master(keyword: str, limit: int = 10):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code, name, market, type
            FROM stock_master
            WHERE name LIKE ?
            LIMIT ?
        """, (f"%{keyword}%", limit))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except:
        return []