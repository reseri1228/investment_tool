import yfinance as yf
import time
from datetime import datetime, timedelta
import os
import requests
from dotenv import load_dotenv

load_dotenv()

PUBLIC_API_KEY = os.getenv("PUBLIC_DATA_API_KEY")
KIS_APP_KEY = os.getenv("KIS_APP_KEY")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")
KIS_BASE_URL = "https://openapi.koreainvestment.com:9443"
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# ── 한투 API 토큰 발급 ──
_kis_token_cache = {"token": None, "expires_at": 0}

def get_kis_token():
    now = time.time()
    if _kis_token_cache["token"] and now < _kis_token_cache["expires_at"]:
        return _kis_token_cache["token"]

    url = f"{KIS_BASE_URL}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET
    }
    try:
        res = requests.post(url, headers=headers, json=body)
        token = res.json().get("access_token", None)
        if token:
            _kis_token_cache["token"] = token
            _kis_token_cache["expires_at"] = now + 60 * 60 * 23
        return token
    except:
        return None


def get_kr_stock_data(ticker):
    try:
        # 티커에서 .KS, .KQ 제거해서 6자리 종목코드 추출
        code = ticker.replace(".KS", "").replace(".KQ", "").zfill(6)

        token = get_kis_token()
        if not token:
            return None

        url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "tr_id": "FHKST01010100"
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": code
        }

        res = requests.get(url, headers=headers, params=params)
        data = res.json().get("output", {})

        if not data:
            return None

        price = data.get("stck_prpr", "N/A")
        change_rate = data.get("prdy_ctrt", "N/A")
        volume = data.get("acml_vol", "N/A")

        return {
            "ticker": ticker,
            "name": data.get("hts_kor_isnm", "N/A"),
            "price": price,
            "change_percent": f"{change_rate}%",
            "volume": volume,
            "market_cap": "N/A"
        }
    except:
        return None

# ── 미국 주식 데이터 (yfinance) ──


def get_kr_dividend_info(ticker):
    """국내 종목의 최근 1년 배당금 합계를 조회 (예탁원정보 배당일정 API)"""
    try:
        code = ticker.replace(".KS", "").replace(".KQ", "").zfill(6)

        token = get_kis_token()
        if not token:
            return None

        today = datetime.today()
        one_year_ago = today - timedelta(days=365)
        f_dt = one_year_ago.strftime("%Y%m%d")
        t_dt = today.strftime("%Y%m%d")

        url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/ksdinfo/dividend"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "tr_id": "HHKDB669102C0",
        }
        params = {
            "CTS": "",
            "GB1": "0",
            "F_DT": f_dt,
            "T_DT": t_dt,
            "SHT_CD": code,
            "HIGH_GB": "",
        }

        res = requests.get(url, headers=headers, params=params)
        data = res.json().get("output1", [])

        if not data:
            return {"annual_dividend_sum": 0, "count": 0}

        total = 0
        for row in data:
            try:
                total += int(row.get("per_sto_divi_amt", "0"))
            except ValueError:
                pass

        return {"annual_dividend_sum": total, "count": len(data)}
    except:
        return None


def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "ticker": ticker,
            "price": str(info.get("currentPrice", "N/A")),
            "change_percent": str(round((info.get("currentPrice", 0) - info.get("previousClose", 0)) / info.get("previousClose", 1) * 100, 2)) + "%",
            "volume": str(info.get("regularMarketVolume", "N/A"))
        }
    except:
        return {
            "ticker": ticker,
            "price": "N/A",
            "change_percent": "N/A",
            "volume": "N/A"
        }

# ── 미국 주식 개요 (yfinance) ──
def get_company_overview(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "market_cap": info.get("marketCap", "N/A"),
            "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            "dividend": info.get("dividendYield", "N/A"),
            "dividend_rate": info.get("dividendRate", "N/A"),
            "debt_to_equity": info.get("debtToEquity", "N/A")
        }
    except:
        return None

# ── 차트 데이터 (yfinance, 국내/미국 공통) ──
def get_chart_data(ticker, period="6mo"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        dates = hist.index.strftime("%Y-%m-%d").tolist()
        closes = hist["Close"].tolist()
        return dates, closes
    except:
        return [], []

# ── 종목 뉴스 검색 (네이버 뉴스 API) ──
def get_stock_news(query, display=3):
    try:
        url = "https://openapi.naver.com/v1/search/news.json"
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        params = {
            "query": query,
            "display": display,
            "sort": "date"
        }
        res = requests.get(url, headers=headers, params=params)
        items = res.json().get("items", [])

        news_list = []
        for item in items:
            title = item.get("title", "").replace("<b>", "").replace("</b>", "").replace("&quot;", chr(34))
            description = item.get("description", "").replace("<b>", "").replace("</b>", "").replace("&quot;", chr(34))
            news_list.append({
                "title": title,
                "description": description,
                "link": item.get("link", ""),
                "pubDate": item.get("pubDate", "")
            })
        return news_list
    except:
        return []

# ── 종목 검색 (yfinance) ──
def detect_market(ticker):
    if ticker.endswith(".KS") or ticker.endswith(".KQ"):
        return "국내"
    return "미국"

def is_korean(text):
    return any('\uAC00' <= c <= '\uD7A3' for c in text)

def search_kr_ticker(keyword):
    from agents.stock_master_agent import search_stock_master
    rows = search_stock_master(keyword)
    results = []
    for code, name, market, type_ in rows:
        results.append({
            "ticker": code + ".KS" if market == "KOSPI" else code + ".KQ",
            "name": name,
            "region": market,
            "market": "국내"
        })
    return results

def search_us_ticker(keyword):
    try:
        search = yf.Search(keyword, max_results=10)
        results = []
        for item in search.quotes:
            ticker = item.get("symbol", "")
            name = item.get("shortname") or item.get("longname", "N/A")
            exchange = item.get("exchDisp", "")
            market = "국내" if exchange in ["Korea", "KOSDAQ"] else "미국"
            results.append({
                "ticker": ticker,
                "name": name,
                "region": exchange,
                "market": market
            })
        return results
    except:
        return []

def search_ticker(keyword):
    if is_korean(keyword):
        return search_kr_ticker(keyword)
    else:
        return search_us_ticker(keyword)