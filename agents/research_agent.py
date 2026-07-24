import yfinance as yf
import os
import requests
from dotenv import load_dotenv

load_dotenv()

PUBLIC_API_KEY = os.getenv("PUBLIC_DATA_API_KEY")
KIS_APP_KEY = os.getenv("KIS_APP_KEY")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")
KIS_BASE_URL = "https://openapi.koreainvestment.com:9443"

# ── 한투 API 토큰 발급 ──
def get_kis_token():
    url = f"{KIS_BASE_URL}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET
    }
    try:
        res = requests.post(url, headers=headers, json=body)
        return res.json().get("access_token", None)
    except:
        return None

# ── 국내 주식 데이터 (한투 API) ──
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