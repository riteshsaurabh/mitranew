#!/usr/bin/env python3
"""
Test script for yfinance functionality
"""

import yfinance as yf
import pandas as pd

def get_stock_data(symbol, period="1y"):
    """Get stock data using yfinance"""
    print(f"\n=== Fetching data for {symbol} ({period}) ===")
    
    # Get data
    ticker = yf.Ticker(symbol)
    info = ticker.info
    history = ticker.history(period=period)
    
    # Display basic info
    company_name = info.get('longName', symbol)
    sector = info.get('sector', 'N/A')
    industry = info.get('industry', 'N/A')
    market_cap = info.get('marketCap', 0)
    market_cap_str = f"${market_cap/1e9:.2f}B" if market_cap else "N/A"
    
    print(f"Company: {company_name}")
    print(f"Sector: {sector}")
    print(f"Industry: {industry}")
    print(f"Market Cap: {market_cap_str}")
    
    # Price info
    current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
    prev_close = info.get('previousClose', 0)
    change = current_price - prev_close if prev_close else 0
    change_pct = (change / prev_close * 100) if prev_close else 0
    
    print(f"Current Price: ${current_price:.2f}")
    print(f"Change: {change:.2f} ({change_pct:.2f}%)")
    
    # Calculate returns
    if not history.empty:
        start_price = history['Close'].iloc[0]
        end_price = history['Close'].iloc[-1]
        period_return = (end_price - start_price) / start_price * 100
        print(f"{period} Return: {period_return:.2f}%")
    
    # Recent prices
    print("\nRecent price data:")
    print(history.tail().to_string())
    
    return ticker, info, history

def main():
    """Test multiple stocks"""
    
    # Test US stocks
    get_stock_data("AAPL", "1y")
    get_stock_data("MSFT", "1y")
    
    # Test Indian stock
    get_stock_data("RELIANCE.NS", "1y")
    
    print("\nStock data fetching completed successfully!")

if __name__ == "__main__":
    main() 