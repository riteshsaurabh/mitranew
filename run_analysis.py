#!/usr/bin/env python3
"""
Money-Mitra Financial Analysis CLI
This script allows you to run financial analysis from the Money-Mitra application 
without requiring Streamlit to be installed.
"""

import sys
import os
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Import project modules if they exist
try:
    import financial_metrics
    import utils
    HAS_PROJECT_MODULES = True
except ImportError:
    HAS_PROJECT_MODULES = False
    print("Warning: Some project modules couldn't be imported. Limited functionality available.")

def get_stock_data(symbol, period="1y"):
    """Get stock data using yfinance"""
    ticker = yf.Ticker(symbol)
    info = ticker.info
    history = ticker.history(period=period)
    return ticker, info, history

def basic_analysis(symbol, period="1y"):
    """Run basic financial analysis on a stock"""
    print(f"\n=== Basic Analysis for {symbol} ===")
    
    # Get data
    ticker, info, history = get_stock_data(symbol, period)
    
    # Display basic info
    company_name = info.get('shortName', symbol)
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
    
    # Advanced metrics if available
    if HAS_PROJECT_MODULES:
        try:
            # Get metrics from project modules
            pe_ratio = financial_metrics.get_valuation_metrics(info).get('P/E Ratio', 'N/A')
            pb_ratio = financial_metrics.get_valuation_metrics(info).get('P/B Ratio', 'N/A')
            dividend_yield = financial_metrics.get_valuation_metrics(info).get('Dividend Yield', 'N/A')
            
            print("\n=== Valuation Metrics ===")
            print(f"P/E Ratio: {pe_ratio}")
            print(f"P/B Ratio: {pb_ratio}")
            print(f"Dividend Yield: {dividend_yield}")
            
            # Get performance metrics
            performance = financial_metrics.get_performance_metrics(ticker, info, history)
            print("\n=== Performance Metrics ===")
            for metric, value in performance.items():
                print(f"{metric}: {value}")
        except Exception as e:
            print(f"Could not compute advanced metrics: {e}")

def main():
    """Main function to parse arguments and run analysis"""
    if len(sys.argv) < 2:
        print("Usage: python run_analysis.py SYMBOL [PERIOD]")
        print("Example: python run_analysis.py AAPL 1y")
        print("\nAvailable periods: 1mo, 3mo, 6mo, 1y, 2y, 5y, max")
        return
    
    symbol = sys.argv[1]
    period = sys.argv[2] if len(sys.argv) > 2 else "1y"
    
    basic_analysis(symbol, period)

if __name__ == "__main__":
    main() 