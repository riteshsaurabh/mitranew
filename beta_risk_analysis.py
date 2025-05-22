
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

def get_beta(ticker, api_key):
    url = f"https://eodhd.com/api/technical-indicator/{ticker}"
    params = {
        "function": "beta",
        "period": 90,
        "api_token": api_key,
        "fmt": "json"
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200 and resp.json():
        beta_value = resp.json()[-1].get("beta")
        if beta_value is not None:
            if beta_value < 1.0:
                label = "Less Volatile (Defensive)"
            elif beta_value > 1.0:
                label = "More Volatile (Aggressive)"
            else:
                label = "Moves with Market"
            return {
                "Ticker": ticker,
                "Beta": beta_value,
                "Label": label
            }
    return {
        "Ticker": ticker,
        "Beta": None,
        "Label": "No Data"
    }

def analyze_peer_beta(ticker, api_key):
    sector, exchange = get_sector(ticker, api_key)
    if not sector:
        print("Could not retrieve sector.")
        return

    print(f"\n📊 Beta Risk Analysis for Sector: {sector}\n")
    peers = get_peers(sector, exchange, api_key=api_key)
    results = []

    for peer in peers:
        result = get_beta(peer, api_key)
        results.append(result)
        print(f"{result['Ticker']}: {result['Label']} | Beta={result['Beta']}")
        time.sleep(1)

    return results

# Example usage
api_key = "682d76fa5c4b17.85025825"
ticker = "AAPL.US"
analyze_peer_beta(ticker, api_key)
