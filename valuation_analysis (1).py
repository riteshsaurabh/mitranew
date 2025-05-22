
import requests
import statistics

API_KEY = "682d76fa5c4b17.85025825"

def get_fundamentals(ticker):
    url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={API_KEY}&fmt=json&filter=Highlights"
    resp = requests.get(url)
    return resp.json() if resp.status_code == 200 else {}

def get_sector(ticker):
    url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={API_KEY}&fmt=json&filter=General"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("Sector"), data.get("Exchange")
    return None, None

def get_sector_peers(sector, exchange="US", limit=25):
    filters = f'[["sector","=","{sector}"],["exchange","=","{exchange}"]]'
    params = {
        "api_token": API_KEY,
        "filters": filters,
        "limit": limit,
        "sort": "market_capitalization.desc",
        "fmt": "json"
    }
    url = "https://eodhd.com/api/screener"
    resp = requests.get(url, params=params)
    return resp.json().get("data", []) if resp.status_code == 200 else []

def extract_metric(data, field):
    try:
        return float(data.get(field)) if data.get(field) is not None else None
    except:
        return None

def compare_to_sector(value, peers_values):
    if value is None or not peers_values:
        return "unknown"
    median = statistics.median(peers_values)
    if value < 0.8 * median:
        return "undervalued"
    elif value > 1.2 * median:
        return "overvalued"
    else:
        return "fair"

def classify(ticker):
    sector, exchange = get_sector(ticker)
    if not sector:
        print(f"❌ Could not fetch sector for {ticker}")
        return

    print(f"\n📊 Analyzing {ticker} in sector '{sector}'")

    fundamentals = get_fundamentals(ticker)
    peers = get_sector_peers(sector, exchange)

    pe = extract_metric(fundamentals, "PERatio")
    peg = extract_metric(fundamentals, "PEGRatio")
    pb = extract_metric(fundamentals, "PriceBookMRQ")
    roe = extract_metric(fundamentals, "ReturnOnEquity")

    pe_vals = [extract_metric(p, "PERatio") for p in peers if extract_metric(p, "PERatio") is not None]
    peg_vals = [extract_metric(p, "PEGRatio") for p in peers if extract_metric(p, "PEGRatio") is not None]
    pb_vals = [extract_metric(p, "PriceBookMRQ") for p in peers if extract_metric(p, "PriceBookMRQ") is not None]
    roe_vals = [extract_metric(p, "ReturnOnEquity") for p in peers if extract_metric(p, "ReturnOnEquity") is not None]

    score = {"undervalued": 0, "fair": 0, "overvalued": 0}

    def score_metric(name, val, peer_vals):
        verdict = compare_to_sector(val, peer_vals)
        if verdict != "unknown":
            score[verdict] += 1
        print(f"• {name}: {val} vs sector → {verdict.capitalize()}")

    score_metric("P/E", pe, pe_vals)
    score_metric("PEG", peg, peg_vals)
    score_metric("P/B", pb, pb_vals)
    score_metric("ROE", roe, roe_vals)

    print(f"\n🧮 Metric Votes — {score}")

    final = max(score, key=score.get)
    if score[final] >= 2:
        print(f"\n✅ Final Verdict: {final.upper()}")
        return final.capitalize()
    else:
        print("\n❓ Final Verdict: Inconclusive")
        return "Inconclusive"

# Example usage
if __name__ == "__main__":
    classify("AAPL.US")
