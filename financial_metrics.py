import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta

@st.cache_data(ttl=3600)
def get_financial_metrics(ticker):
    """
    Calculate and compile financial metrics for a given stock
    
    Args:
        ticker (str): Stock ticker symbol
    
    Returns:
        dict: Dictionary with different financial metrics categories
    """
    try:
        # Initialize metrics dictionary
        metrics = {
            'key_ratios': {},
            'performance': {},
            'valuation': {}
        }
        
        # Get stock data
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get historical data for performance calculations
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*10)  # 10 years of data
        hist = stock.history(start=start_date, end=end_date)
        
        # Extract key ratios
        metrics['key_ratios'] = extract_key_ratios(info)
        
        # Calculate performance metrics
        metrics['performance'] = calculate_performance_metrics(hist, info)
        
        # Extract valuation metrics
        metrics['valuation'] = extract_valuation_metrics(info)
        
        return metrics
    
    except Exception as e:
        print(f"Error getting financial metrics: {e}")
        # Return empty dictionaries if there's an error
        return {
            'key_ratios': {},
            'performance': {},
            'valuation': {}
        }

def extract_key_ratios(info):
    """
    Extract key financial ratios from stock info
    
    Args:
        info (dict): Stock info dictionary from yfinance
    
    Returns:
        dict: Key financial ratios
    """
    # Initialize empty dictionary for ratios
    ratios = {}
    
    # Profitability ratios
    ratios['grossMargins'] = info.get('grossMargins')
    ratios['operatingMargins'] = info.get('operatingMargins')
    ratios['profitMargins'] = info.get('profitMargins')
    ratios['returnOnAssets'] = info.get('returnOnAssets')
    ratios['returnOnEquity'] = info.get('returnOnEquity')
    
    # Liquidity ratios
    ratios['currentRatio'] = info.get('currentRatio')
    ratios['quickRatio'] = info.get('quickRatio')
    
    # Solvency ratios
    ratios['debtToEquity'] = info.get('debtToEquity')
    
    # Other financial ratios that might be available
    # Note: Some of these may not be available in yfinance API
    ratios['interestCoverage'] = info.get('interestCoverage', None)
    ratios['assetTurnover'] = info.get('assetTurnover', None)
    ratios['inventoryTurnover'] = info.get('inventoryTurnover', None)
    ratios['receivablesTurnover'] = info.get('receivablesTurnover', None)
    ratios['payablesTurnover'] = info.get('payablesTurnover', None)
    
    return ratios

def calculate_performance_metrics(hist_data, info):
    """
    Calculate performance metrics from historical data
    
    Args:
        hist_data (pandas.DataFrame): Historical stock data
        info (dict): Stock info dictionary from yfinance
    
    Returns:
        dict: Performance metrics
    """
    # Initialize performance dictionary
    performance = {}
    
    # Handle empty data
    if hist_data.empty:
        return performance
    
    # Calculate returns for various periods
    try:
        # Get latest close price
        latest_close = hist_data['Close'].iloc[-1]
        
        # 1 day return
        if len(hist_data) > 1:
            performance['oneDay'] = ((latest_close / hist_data['Close'].iloc[-2]) - 1) * 100
        
        # 5 day return
        if len(hist_data) > 5:
            performance['fiveDay'] = ((latest_close / hist_data['Close'].iloc[-6]) - 1) * 100
        
        # 1 month return (21 trading days)
        if len(hist_data) > 21:
            performance['oneMonth'] = ((latest_close / hist_data['Close'].iloc[-22]) - 1) * 100
        
        # 3 month return (63 trading days)
        if len(hist_data) > 63:
            performance['threeMonth'] = ((latest_close / hist_data['Close'].iloc[-64]) - 1) * 100
        
        # 6 month return (126 trading days)
        if len(hist_data) > 126:
            performance['sixMonth'] = ((latest_close / hist_data['Close'].iloc[-127]) - 1) * 100
        
        # YTD return
        current_year = datetime.now().year
        ytd_start = datetime(current_year, 1, 1)
        # Convert index to datetime if it's not already
        if not isinstance(hist_data.index, pd.DatetimeIndex):
            hist_data.index = pd.to_datetime(hist_data.index)
        # Use datetime objects without timezone for comparison
        # Convert any timezone-aware datetimes to naive datetimes for comparison
        naive_dates = hist_data.index.tz_localize(None) if hist_data.index.tz is not None else hist_data.index
        ytd_data = hist_data[naive_dates >= ytd_start]
        if not ytd_data.empty:
            performance['ytd'] = ((latest_close / ytd_data['Close'].iloc[0]) - 1) * 100
        
        # 1 year return (252 trading days)
        if len(hist_data) > 252:
            performance['oneYear'] = ((latest_close / hist_data['Close'].iloc[-253]) - 1) * 100
        
        # 2 year return (504 trading days)
        if len(hist_data) > 504:
            performance['twoYear'] = ((latest_close / hist_data['Close'].iloc[-505]) - 1) * 100
        
        # 3 year return (756 trading days)
        if len(hist_data) > 756:
            performance['threeYear'] = ((latest_close / hist_data['Close'].iloc[-757]) - 1) * 100
        
        # 5 year return (1260 trading days)
        if len(hist_data) > 1260:
            performance['fiveYear'] = ((latest_close / hist_data['Close'].iloc[-1261]) - 1) * 100
        
        # 10 year return (2520 trading days)
        if len(hist_data) > 2520:
            performance['tenYear'] = ((latest_close / hist_data['Close'].iloc[-2521]) - 1) * 100
        
        # Max period return
        performance['max'] = ((latest_close / hist_data['Close'].iloc[0]) - 1) * 100
        
        # Volatility metrics
        performance['beta'] = info.get('beta')
        
        # Standard deviation of returns (annualized)
        one_year_data = hist_data.iloc[-252:]
        daily_returns = one_year_data['Close'].pct_change().dropna()
        performance['std1Y'] = daily_returns.std() * np.sqrt(252) * 100
        
        # Maximum drawdown over 1 year
        rolling_max = one_year_data['Close'].cummax()
        drawdown = (one_year_data['Close'] / rolling_max - 1.0) * 100
        performance['maxDrawdown'] = drawdown.min()
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        excess_return = (performance.get('oneYear', 0) / 100) - risk_free_rate
        if performance.get('std1Y'):
            performance['sharpeRatio'] = excess_return / (performance['std1Y'] / 100)
        
    except Exception as e:
        print(f"Error calculating performance metrics: {e}")
    
    return performance

def extract_valuation_metrics(info):
    """
    Extract valuation metrics from stock info
    
    Args:
        info (dict): Stock info dictionary from yfinance
    
    Returns:
        dict: Valuation metrics
    """
    # Initialize valuation dictionary
    valuation = {}
    
    # Price multiples
    valuation['trailingPE'] = info.get('trailingPE')
    valuation['forwardPE'] = info.get('forwardPE')
    valuation['pegRatio'] = info.get('pegRatio')
    valuation['priceToSalesTrailing12Months'] = info.get('priceToSalesTrailing12Months')
    valuation['priceToBook'] = info.get('priceToBook')
    
    # Enterprise value multiples
    valuation['enterpriseToRevenue'] = info.get('enterpriseToRevenue')
    valuation['enterpriseToEbitda'] = info.get('enterpriseToEbitda')
    valuation['enterpriseToEbit'] = info.get('enterpriseToEbit', None)  # May not be available
    valuation['enterpriseToFcf'] = info.get('enterpriseToFcf', None)    # May not be available
    
    # Dividend metrics
    valuation['dividendYield'] = info.get('dividendYield', 0)
    valuation['payoutRatio'] = info.get('payoutRatio', 0)
    
    # These are typically not available directly from yfinance
    valuation['dividendGrowth5Y'] = None
    valuation['dividendGrowthYears'] = None
    
    return valuation
