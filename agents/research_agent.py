import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
PUBLIC_API_KEY = os.getenv("PUBLIC_DATA_API_KEY")

# 검색 캐시 (종목명/티커는 자주 안 바뀌므로 저장)
_search_cache = {}

def get_stock_data(ticker):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": ticker,
        "apikey": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    quote = data.get("Global Quote", {})
    return {
        "ticker": ticker,
        "price": quote.get("05. price", "N/A"),
        "change_percent": quote.get("10. change percent", "N/A"),
        "volume": quote.get("06. volume", "N/A")
    }

def get_company_overview(ticker):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "OVERVIEW",
        "symbol": ticker,
        "apikey": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return {
        "market_cap": data.get("MarketCapitalization", "N/A"),
        "52_week_high": data.get("52WeekHigh", "N/A"),
        "52_week_low": data.get("52WeekLow", "N/A"),
        "dividend": data.get("DividendYield", "N/A"),
        "debt_to_equity": data.get("DebtToEquityRatio", "N/A")
    }

def get_chart_data(ticker):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": "compact",
        "apikey": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    time_series = data.get("Time Series (Daily)", {})
    dates = []
    closes = []
    for date, values in sorted(time_series.items()):
        dates.append(date)
        closes.append(float(values["4. close"]))
    return dates, closes

def get_kr_stock_data(ticker):
    url = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"
    params = {
        "serviceKey": PUBLIC_API_KEY,
        "numOfRows": 1,
        "pageNo": 1,
        "resultType": "json",
        "likeSrtnCd": ticker
    }
    response = requests.get(url, params=params)
    data = response.json()
    try:
        item = data["response"]["body"]["items"]["item"][0]
        return {
            "ticker": ticker,
            "name": item.get("itmsNm", "N/A"),
            "price": item.get("clpr", "N/A"),
            "change_percent": item.get("fltRt", "N/A"),
            "volume": item.get("trqu", "N/A"),
            "market_cap": item.get("mrktTotAmt", "N/A")
        }
    except:
        return None

def search_ticker(keyword):
    # 캐시에 있으면 API 호출 안함
    if keyword in _search_cache:
        return _search_cache[keyword]
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "SYMBOL_SEARCH",
        "keywords": keyword,
        "apikey": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    results = []
    for match in data.get("bestMatches", []):
        ticker = match.get("1. symbol", "")
        name = match.get("2. name", "")
        region = match.get("4. region", "")
        results.append({
            "ticker": ticker,
            "name": name,
            "region": region
        })
    
    # 결과 캐시에 저장
    _search_cache[keyword] = results
    return results