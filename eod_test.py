import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import os

def test_eod_api(api_key, symbol="AAPL"):
    """Test EOD API with a simple request"""
    print(f"Testing EOD API with symbol: {symbol}")
    
    # Get stock price data
    url = f"https://eodhistoricaldata.com/api/eod/{symbol}?api_token={api_key}&period=d&fmt=json"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        print(f"Successfully retrieved {len(df)} data points for {symbol}")
        print(df.tail())
        return True
    else:
        print(f"API request failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def get_stock_fundamentals(api_key, symbol="AAPL"):
    """Get stock fundamentals data using EOD API"""
    url = f"https://eodhistoricaldata.com/api/fundamentals/{symbol}?api_token={api_key}&fmt=json"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nFundamentals data for {symbol}:")
        print(f"Company Name: {data.get('General', {}).get('Name', 'N/A')}")
        print(f"Description: {data.get('General', {}).get('Description', 'N/A')[:150]}...")
        print(f"Sector: {data.get('General', {}).get('Sector', 'N/A')}")
        print(f"Industry: {data.get('General', {}).get('Industry', 'N/A')}")
        return True
    else:
        print(f"API request failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    # Ask for API key
    api_key = input("Please enter your EODHD API key: ")
    
    # Test US stock
    test_eod_api(api_key, "AAPL")
    get_stock_fundamentals(api_key, "AAPL")
    
    # Test Indian stock
    test_eod_api(api_key, "RELIANCE.BSE")
    get_stock_fundamentals(api_key, "RELIANCE.BSE") 