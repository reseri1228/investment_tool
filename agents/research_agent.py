import yfinance as yf
import os
from dotenv import load_dotenv

load_dotenv()

PUBLIC_API_KEY = os.getenv("PUBLIC_DATA_API_KEY")

def detect_market(ticker):
    if ticker.endswith(".KS") or ticker.endswith(".KQ"):
        return "국내"
    return "미국"

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

def get_chart_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        dates = hist.index.strftime("%Y-%m-%d").tolist()
        closes = hist["Close"].tolist()
        return dates, closes
    except:
        return [], []

def get_kr_stock_data(ticker):
    try:
        # 이미 .KS나 .KQ가 붙어있으면 그대로 사용
        if ticker.endswith(".KS") or ticker.endswith(".KQ"):
            full_ticker = ticker
        else:
            full_ticker = ticker + ".KS"
        
        stock = yf.Ticker(full_ticker)
        info = stock.info
        if info.get("currentPrice"):
            return {
                "ticker": ticker,
                "name": info.get("longName", "N/A"),
                "price": str(info.get("currentPrice", "N/A")),
                "change_percent": str(round(info.get("regularMarketChangePercent", 0), 2)) + "%",
                "volume": str(info.get("regularMarketVolume", "N/A")),
                "market_cap": str(info.get("marketCap", "N/A"))
            }
        stock = yf.Ticker(ticker + ".KQ")
        info = stock.info
        return {
            "ticker": ticker,
            "name": info.get("longName", "N/A"),
            "price": str(info.get("currentPrice", "N/A")),
            "change_percent": str(round(info.get("regularMarketChangePercent", 0) * 100, 2)) + "%",
            "volume": str(info.get("regularMarketVolume", "N/A")),
            "market_cap": str(info.get("marketCap", "N/A"))
        }
    except:
        return None

def search_ticker(keyword):
    try:
        ticker = yf.Ticker(keyword)
        info = ticker.info
        if info.get("longName"):
            market = detect_market(keyword)
            return [{
                "ticker": keyword,
                "name": info.get("longName", "N/A"),
                "region": "Korea" if market == "국내" else "United States",
                "market": market
            }]
        return []
    except:
        return []