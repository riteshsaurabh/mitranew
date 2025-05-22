import requests

API_KEY = "682d76fa5c4b17.85025825"

def get_indicator(ticker, function, period):
    url = f"https://eodhd.com/api/technical-indicator/{ticker}"
    params = {
        "function": function,
        "period": period,
        "api_token": API_KEY,
        "fmt": "json"
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"Error getting {function}")
        return None

def in_buy_zone(ticker):
    print(f"\nAnalyzing {ticker}...\n")

    # Get indicators
    rsi_data = get_indicator(ticker, "rsi", 14)
    bbands_data = get_indicator(ticker, "bbands", 20)
    macd_data = get_indicator(ticker, "macd", 12)

    # Extract latest values
    rsi_value = float(rsi_data[-1]['rsi']) if rsi_data else None
    bbands = bbands_data[-1] if bbands_data else {}
    macd = macd_data[-1] if macd_data else {}

    lower_band = float(bbands.get("lowerBand", 0))
    close_price = float(bbands.get("close", 0))
    macd_line = float(macd.get("macd", 0))
    signal_line = float(macd.get("signal", 0))

    # Check signals
    buy_signals = 0

    if rsi_value and rsi_value < 30:
        print(f"✅ RSI ({rsi_value:.2f}) < 30 → Oversold")
        buy_signals += 1
    else:
        print(f"❌ RSI ({rsi_value:.2f}) not oversold" if rsi_value else "❌ RSI not available")

    if close_price and lower_band and close_price <= lower_band * 1.03:
        print(f"✅ Price near lower Bollinger Band (Close: {close_price}, Lower: {lower_band})")
        buy_signals += 1
    else:
        print(f"❌ Price not near lower Bollinger Band" if close_price and lower_band else "❌ Bollinger Bands not available")

    if macd_line and signal_line and macd_line > signal_line:
        print(f"✅ MACD crossover (MACD: {macd_line}, Signal: {signal_line})")
        buy_signals += 1
    else:
        print(f"❌ No MACD crossover" if macd_line and signal_line else "❌ MACD not available")

    # Result
    if buy_signals >= 2:
        print("\n🔔 BUY ZONE: ✅ (2 or more buy signals met)")
        return True
    else:
        print("\n⛔ NOT in Buy Zone ❌")
        return False

# Example usage
in_buy_zone("AAPL.US")
