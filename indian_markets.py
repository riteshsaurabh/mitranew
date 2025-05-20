import pandas as pd
import yfinance as yf
from nsetools import Nse
import pandas_datareader.data as web
from datetime import datetime, timedelta
import re

# Initialize NSE
nse = Nse()

def is_indian_symbol(symbol):
    """
    Check if a symbol is an Indian stock (NSE/BSE)
    
    Args:
        symbol (str): Stock symbol to check
    
    Returns:
        bool: True if it's an Indian stock, False otherwise
    """
    # Check for .NS or .BO suffix
    if symbol.endswith('.NS') or symbol.endswith('.BO'):
        return True
    
    # Check if it's in NSE list
    try:
        symbol_clean = symbol.replace('.NS', '')
        stock_info = nse.get_quote(symbol_clean)
        if stock_info:
            return True
    except:
        pass
    
    return False

def format_indian_symbol(symbol):
    """
    Format symbol for Indian exchanges
    
    Args:
        symbol (str): The stock symbol
    
    Returns:
        str: Properly formatted symbol for Yahoo Finance
    """
    # If it already has .NS or .BO suffix, return as is
    if symbol.endswith('.NS') or symbol.endswith('.BO'):
        return symbol
    
    # Try to find in NSE
    try:
        symbol_clean = symbol.replace('.NS', '').replace('.BO', '')
        stock_info = nse.get_quote(symbol_clean)
        if stock_info:
            return f"{symbol_clean}.NS"
    except:
        # If not found in NSE, assume BSE (less common)
        return f"{symbol}.BO"
    
    # Default to NSE
    return f"{symbol}.NS"

def get_indian_stock_data(symbol, period='1y'):
    """
    Get Indian stock historical data
    
    Args:
        symbol (str): Stock symbol (with or without .NS/.BO suffix)
        period (str): Period for historical data
    
    Returns:
        pandas.DataFrame: Historical stock data
    """
    # Format symbol for Indian exchanges
    formatted_symbol = format_indian_symbol(symbol)
    
    # Use Yahoo Finance to get data
    stock = yf.Ticker(formatted_symbol)
    hist = stock.history(period=period)
    
    return hist

def get_indian_company_info(symbol):
    """
    Get Indian company information
    
    Args:
        symbol (str): Stock symbol (with or without .NS/.BO suffix)
    
    Returns:
        dict: Company information
    """
    # Format symbol for Indian exchanges
    formatted_symbol = format_indian_symbol(symbol)
    
    # Clean the symbol for NSE lookup
    clean_symbol = formatted_symbol.replace('.NS', '').replace('.BO', '')
    
    # Try to get NSE data
    try:
        nse_info = nse.get_quote(clean_symbol)
    except:
        nse_info = None
    
    # Get Yahoo Finance data
    yf_info = yf.Ticker(formatted_symbol).info
    
    # Combine data from both sources
    combined_info = yf_info.copy()
    
    # Add NSE-specific data if available
    if nse_info:
        # Currency conversion for prices (assuming Yahoo Finance returns in USD)
        if 'currentPrice' in combined_info:
            if not isinstance(combined_info['currentPrice'], str) and combined_info['currentPrice'] is not None:
                combined_info['currentPrice_INR'] = combined_info['currentPrice'] * 83.0  # Approximate USD to INR
        
        # Add NSE-specific fields
        for key in ['companyName', 'lastPrice', 'open', 'dayHigh', 'dayLow', 'close', 'previousClose',
                   'pChange', 'change', 'totalTradedVolume', 'totalTradedValue', 'marketCap']:
            if key in nse_info:
                combined_info[f'nse_{key}'] = nse_info[key]
    
    return combined_info

def get_nifty_index_data(period='1y'):
    """
    Get NIFTY 50 index data
    
    Args:
        period (str): Period for historical data
    
    Returns:
        pandas.DataFrame: Historical index data
    """
    # Use Yahoo Finance to get NIFTY 50 data
    index = yf.Ticker('^NSEI')
    hist = index.history(period=period)
    return hist

def get_sensex_index_data(period='1y'):
    """
    Get SENSEX index data
    
    Args:
        period (str): Period for historical data
    
    Returns:
        pandas.DataFrame: Historical index data
    """
    # Use Yahoo Finance to get SENSEX data
    index = yf.Ticker('^BSESN')
    hist = index.history(period=period)
    return hist

def get_top_nse_gainers():
    """
    Get top gainers in NSE
    
    Returns:
        list: List of top gainers with their details
    """
    try:
        return nse.get_top_gainers()
    except:
        return []

def get_top_nse_losers():
    """
    Get top losers in NSE
    
    Returns:
        list: List of top losers with their details
    """
    try:
        return nse.get_top_losers()
    except:
        return []

def get_all_nse_stocks():
    """
    Get all stock codes listed in NSE
    
    Returns:
        dict: Dictionary of stocks with symbol as key and name as value
    """
    try:
        return nse.get_stock_codes()
    except:
        return {}

def format_inr(amount):
    """
    Format amount in Indian Rupees notation (lakhs, crores)
    
    Args:
        amount: Number to format
    
    Returns:
        str: Formatted amount in INR notation with exactly 2 decimal places
    """
    if not isinstance(amount, (int, float)):
        return "N/A"
    
    abs_amount = abs(amount)
    if abs_amount >= 10000000:  # Crore (10 million)
        return f"₹{abs_amount / 10000000:.2f} Cr"
    elif abs_amount >= 100000:  # Lakh (100 thousand)
        return f"₹{abs_amount / 100000:.2f} L"
    elif abs_amount >= 1000:    # Thousand
        return f"₹{abs_amount / 1000:.2f} K"
    else:
        return f"₹{abs_amount:.2f}"

def convert_usd_to_inr(usd_value, conversion_rate=83.0):
    """
    Convert USD value to INR
    
    Args:
        usd_value: Value in USD
        conversion_rate: USD to INR conversion rate (default: 83)
    
    Returns:
        float: Value in INR
    """
    if not isinstance(usd_value, (int, float)):
        return None
    
    return usd_value * conversion_rate