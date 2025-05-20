import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
import format_utils

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
        dict: Key financial ratios formatted to 2 decimal places
    """
    # Initialize empty dictionary for ratios
    ratios = {}
    
    # Format percentage values
    percentage_ratios = [
        'grossMargins', 'operatingMargins', 'profitMargins', 
        'returnOnAssets', 'returnOnEquity'
    ]
    
    for ratio in percentage_ratios:
        value = info.get(ratio)
        if value is not None:
            # Convert to percentage and format with 2 decimal places
            ratios[ratio] = format_utils.format_percent(value)
        else:
            ratios[ratio] = "N/A"
    
    # Format other numeric ratios
    other_ratios = [
        'currentRatio', 'quickRatio', 'debtToEquity',
        'interestCoverage', 'assetTurnover', 'inventoryTurnover',
        'receivablesTurnover', 'payablesTurnover'
    ]
    
    for ratio in other_ratios:
        value = info.get(ratio)
        if value is not None:
            # Format with 2 decimal places
            ratios[ratio] = format_utils.format_number(value)
        else:
            ratios[ratio] = "N/A"
    
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
            one_day_return = ((latest_close / hist_data['Close'].iloc[-2]) - 1)
            performance['oneDay'] = format_utils.format_percent(one_day_return)
        
        # 5 day return
        if len(hist_data) > 5:
            five_day_return = ((latest_close / hist_data['Close'].iloc[-6]) - 1)
            performance['fiveDay'] = format_utils.format_percent(five_day_return)
        
        # 1 month return (21 trading days)
        if len(hist_data) > 21:
            one_month_return = ((latest_close / hist_data['Close'].iloc[-22]) - 1)
            performance['oneMonth'] = format_utils.format_percent(one_month_return)
        
        # 3 month return (63 trading days)
        if len(hist_data) > 63:
            three_month_return = ((latest_close / hist_data['Close'].iloc[-64]) - 1)
            performance['threeMonth'] = format_utils.format_percent(three_month_return)
        
        # 6 month return (126 trading days)
        if len(hist_data) > 126:
            six_month_return = ((latest_close / hist_data['Close'].iloc[-127]) - 1)
            performance['sixMonth'] = format_utils.format_percent(six_month_return)
        
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
            ytd_return = ((latest_close / ytd_data['Close'].iloc[0]) - 1)
            performance['ytd'] = format_utils.format_percent(ytd_return)
        
        # 1 year return (252 trading days)
        if len(hist_data) > 252:
            one_year_return = ((latest_close / hist_data['Close'].iloc[-253]) - 1)
            performance['oneYear'] = format_utils.format_percent(one_year_return)
        
        # 2 year return (504 trading days)
        if len(hist_data) > 504:
            two_year_return = ((latest_close / hist_data['Close'].iloc[-505]) - 1)
            performance['twoYear'] = format_utils.format_percent(two_year_return)
        
        # 3 year return (756 trading days)
        if len(hist_data) > 756:
            three_year_return = ((latest_close / hist_data['Close'].iloc[-757]) - 1)
            performance['threeYear'] = format_utils.format_percent(three_year_return)
        
        # 5 year return (1260 trading days)
        if len(hist_data) > 1260:
            five_year_return = ((latest_close / hist_data['Close'].iloc[-1261]) - 1)
            performance['fiveYear'] = format_utils.format_percent(five_year_return)
        
        # 10 year return (2520 trading days)
        if len(hist_data) > 2520:
            ten_year_return = ((latest_close / hist_data['Close'].iloc[-2521]) - 1)
            performance['tenYear'] = format_utils.format_percent(ten_year_return)
        
        # Max period return
        max_return = ((latest_close / hist_data['Close'].iloc[0]) - 1)
        performance['max'] = format_utils.format_percent(max_return)
        
        # Volatility metrics
        beta = info.get('beta')
        performance['beta'] = format_utils.format_number(beta) if beta is not None else "N/A"
        
        # Standard deviation of returns (annualized)
        one_year_data = hist_data.iloc[-252:]
        daily_returns = one_year_data['Close'].pct_change().dropna()
        std_1y = daily_returns.std() * np.sqrt(252)
        performance['std1Y'] = format_utils.format_percent(std_1y)
        
        # Maximum drawdown over 1 year
        rolling_max = one_year_data['Close'].cummax()
        drawdown = (one_year_data['Close'] / rolling_max - 1.0)
        min_drawdown = drawdown.min()
        performance['maxDrawdown'] = format_utils.format_percent(min_drawdown)
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        # Get oneYear as a number, not as a formatted string
        one_year_return_value = ((latest_close / hist_data['Close'].iloc[-253]) - 1) if len(hist_data) > 252 else 0
        excess_return = one_year_return_value - risk_free_rate
        if daily_returns.std() * np.sqrt(252) > 0:
            sharpe = excess_return / (daily_returns.std() * np.sqrt(252))
            performance['sharpeRatio'] = format_utils.format_number(sharpe)
        
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
