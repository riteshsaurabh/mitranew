
import requests
import time

def get_sector(ticker, api_key):
    url = f"https://eodhd.com/api/fundamentals/{ticker}"
    params = {"api_token": api_key, "fmt": "json", "filter": "General"}
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("Sector"), data.get("Exchange")
    return None, None

def get_peers(sector, exchange="US", limit=10, api_key=""):
    url = "https://eodhd.com/api/screener"
    filters = f'[["sector","=","{sector}"],["exchange","=","{exchange}"]]'
    params = {
        "api_token": api_key,
        "filters": filters,
        "limit": limit,
        "sort": "market_capitalization.desc",
        "fmt": "json"
    }
    resp = requests.get(url, params=params)
    return [item["code"] for item in resp.json().get("data", [])] if resp.status_code == 200 else []

def get_sentiment(ticker, api_key):
    url = "https://eodhd.com/api/sentiments"
    params = {
        "s": ticker,
        "api_token": api_key,
        "fmt": "json"
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200 and resp.json():
        s = resp.json()[0]["sentiment"]
        polarity, pos, neg = s["polarity"], s["pos"], s["neg"]
        label = "Neutral"
        if polarity > 0.1 and pos > 0.5 and neg < 0.2:
            label = "Bullish"
        elif polarity < -0.1 and neg > 0.3:
            label = "Bearish"
        return {
            "Ticker": ticker,
            "Polarity": polarity,
            "Positive": pos,
            "Negative": neg,
            "Label": label
        }
    return {
        "Ticker": ticker,
        "Polarity": None,
        "Positive": None,
        "Negative": None,
        "Label": "No Data"
    }

def analyze_peer_sentiment(ticker, api_key):
    sector, exchange = get_sector(ticker, api_key)
    if not sector:
        print("Could not retrieve sector.")
        return

    print(f"\n🔍 Scanning peers in sector: {sector}\n")
    peers = get_peers(sector, exchange, api_key=api_key)
    results = []

    for peer in peers:
        sentiment = get_sentiment(peer, api_key)
        results.append(sentiment)
        print(f"{peer}: {sentiment['Label']} | Polarity={sentiment['Polarity']}")

        # Respect rate limits if needed
        time.sleep(1)

    return results

# Example
api_key = "682d76fa5c4b17.85025825"
ticker = "AAPL.US"
analyze_peer_sentiment(ticker, api_key)
