"""
Financial Metrics Module for MoneyMitra Dashboard

This module provides functions to calculate and display various financial metrics
for stock analysis, with reliable data fetching and formatting.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
import format_utils

def get_financial_metrics(symbol, is_indian=False):
    """
    Calculate and compile financial metrics for a given stock
    
    Args:
        symbol (str): Stock ticker symbol
        is_indian (bool): Whether it's an Indian stock
    
    Returns:
        dict: Dictionary with different financial metrics categories
    """
    try:
        # Get ticker data
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        if not info:
            return None
            
        # Get historical data for performance calculations
        hist_data = ticker.history(period="1y")
        
        # Create result dictionary with all metric categories
        result = {
            'valuation_metrics': get_valuation_metrics(info, is_indian),
            'profitability_ratios': get_profitability_ratios(info),
            'financial_health': get_financial_health_metrics(info),
            'performance_metrics': get_performance_metrics(hist_data, info),
            'technical_indicators': get_technical_indicators(hist_data),
            'growth_metrics': get_growth_metrics(info),
            'dividend_info': get_dividend_info(info, is_indian),
            'price_info': get_price_info(info, is_indian),
            'volume_info': get_volume_info(info),
            'share_statistics': get_share_statistics(info, is_indian)
        }
        
        return result
    
    except Exception as e:
        st.error(f"Error calculating financial metrics: {str(e)}")
        return None

def get_valuation_metrics(info, is_indian):
    """Get valuation metrics from stock info"""
    metrics = {}
    
    # P/E Ratio
    metrics["P/E Ratio"] = format_utils.format_number(info.get("trailingPE", "N/A"))
    
    # Forward P/E
    metrics["Forward P/E"] = format_utils.format_number(info.get("forwardPE", "N/A"))
    
    # PEG Ratio
    metrics["PEG Ratio"] = format_utils.format_number(info.get("pegRatio", "N/A"))
    
    # Price to Sales
    metrics["Price/Sales"] = format_utils.format_number(info.get("priceToSalesTrailing12Months", "N/A"))
    
    # Price to Book
    metrics["Price/Book"] = format_utils.format_number(info.get("priceToBook", "N/A"))
    
    # Enterprise Value / EBITDA
    metrics["EV/EBITDA"] = format_utils.format_number(info.get("enterpriseToEbitda", "N/A"))
    
    # Enterprise Value / Revenue
    metrics["EV/Revenue"] = format_utils.format_number(info.get("enterpriseToRevenue", "N/A"))
    
    return metrics

def get_profitability_ratios(info):
    """Get profitability ratios from stock info"""
    metrics = {}
    
    # Gross Margin
    metrics["Gross Margin"] = format_utils.format_percent(info.get("grossMargins", "N/A"))
    
    # Operating Margin
    metrics["Operating Margin"] = format_utils.format_percent(info.get("operatingMargins", "N/A"))
    
    # Profit Margin
    metrics["Profit Margin"] = format_utils.format_percent(info.get("profitMargins", "N/A"))
    
    # Return on Assets (ROA)
    metrics["Return on Assets"] = format_utils.format_percent(info.get("returnOnAssets", "N/A"))
    
    # Return on Equity (ROE)
    metrics["Return on Equity"] = format_utils.format_percent(info.get("returnOnEquity", "N/A"))
    
    # EBITDA Margin
    ebitda = info.get("ebitda", None)
    total_revenue = info.get("totalRevenue", None)
    
    if ebitda is not None and total_revenue is not None and total_revenue != 0:
        ebitda_margin = ebitda / total_revenue
        metrics["EBITDA Margin"] = format_utils.format_percent(ebitda_margin)
    else:
        metrics["EBITDA Margin"] = "N/A"
    
    return metrics

def get_financial_health_metrics(info):
    """Get financial health metrics from stock info"""
    metrics = {}
    
    # Current Ratio
    metrics["Current Ratio"] = format_utils.format_number(info.get("currentRatio", "N/A"))
    
    # Quick Ratio
    metrics["Quick Ratio"] = format_utils.format_number(info.get("quickRatio", "N/A"))
    
    # Debt to Equity
    metrics["Debt to Equity"] = format_utils.format_number(info.get("debtToEquity", "N/A"))
    
    # Interest Coverage
    metrics["Interest Coverage"] = format_utils.format_number(info.get("interestCoverage", "N/A"))
    
    # Total Debt / Total Assets
    total_debt = info.get("totalDebt", None)
    total_assets = info.get("totalAssets", None)
    
    if total_debt is not None and total_assets is not None and total_assets != 0:
        debt_to_assets = total_debt / total_assets
        metrics["Debt/Assets Ratio"] = format_utils.format_percent(debt_to_assets)
    else:
        metrics["Debt/Assets Ratio"] = "N/A"
    
    return metrics

def get_performance_metrics(hist_data, info):
    """Get stock performance metrics"""
    metrics = {}
    
    if hist_data is not None and not hist_data.empty:
        # Calculate returns over different periods
        current_price = hist_data['Close'].iloc[-1] if not hist_data.empty else None
        
        if current_price:
            # Day change
            prev_close = hist_data['Close'].iloc[-2] if len(hist_data) > 1 else None
            if prev_close:
                day_change = (current_price / prev_close - 1)
                metrics["1-Day Return"] = format_utils.format_percent(day_change)
            
            # Week change (5 trading days)
            week_ago = hist_data['Close'].iloc[-6] if len(hist_data) > 5 else None
            if week_ago:
                week_change = (current_price / week_ago - 1)
                metrics["1-Week Return"] = format_utils.format_percent(week_change)
            
            # Month change (21 trading days)
            month_ago = hist_data['Close'].iloc[-22] if len(hist_data) > 21 else None
            if month_ago:
                month_change = (current_price / month_ago - 1)
                metrics["1-Month Return"] = format_utils.format_percent(month_change)
            
            # YTD change
            start_of_year = datetime(datetime.now().year, 1, 1)
            ytd_data = hist_data.loc[hist_data.index >= start_of_year]
            if not ytd_data.empty:
                ytd_start_price = ytd_data['Close'].iloc[0]
                ytd_change = (current_price / ytd_start_price - 1)
                metrics["YTD Return"] = format_utils.format_percent(ytd_change)
            
            # 1Y change
            year_ago = hist_data['Close'].iloc[0] if len(hist_data) > 250 else None
            if year_ago:
                year_change = (current_price / year_ago - 1)
                metrics["1-Year Return"] = format_utils.format_percent(year_change)
    
        # Calculate volatility
        if len(hist_data) > 20:
            # Daily returns
            daily_returns = hist_data['Close'].pct_change().dropna()
            
            # 30-day volatility (annualized)
            vol_30d = daily_returns.tail(30).std() * np.sqrt(252)
            metrics["30-Day Volatility"] = format_utils.format_percent(vol_30d)
            
            # 90-day volatility (annualized)
            if len(daily_returns) >= 90:
                vol_90d = daily_returns.tail(90).std() * np.sqrt(252)
                metrics["90-Day Volatility"] = format_utils.format_percent(vol_90d)
        
        # Beta (if available)
        beta = info.get("beta", None)
        if beta is not None:
            metrics["Beta"] = format_utils.format_number(beta)
        
    return metrics

def get_technical_indicators(hist_data):
    """Calculate technical indicators from historical data"""
    metrics = {}
    
    if hist_data is not None and not hist_data.empty and len(hist_data) > 50:
        # Current price
        current_price = hist_data['Close'].iloc[-1]
        
        # SMA 20
        sma_20 = hist_data['Close'].rolling(window=20).mean().iloc[-1]
        metrics["SMA (20)"] = format_utils.format_number(sma_20)
        
        # SMA 50
        sma_50 = hist_data['Close'].rolling(window=50).mean().iloc[-1]
        metrics["SMA (50)"] = format_utils.format_number(sma_50)
        
        # SMA 200 (if we have enough data)
        if len(hist_data) >= 200:
            sma_200 = hist_data['Close'].rolling(window=200).mean().iloc[-1]
            metrics["SMA (200)"] = format_utils.format_number(sma_200)
            
            # Price relative to SMAs
            metrics["Price/SMA (200)"] = format_utils.format_percent(current_price / sma_200 - 1)
        
        # RSI (14)
        delta = hist_data['Close'].diff().dropna()
        up_days = delta.copy()
        up_days[delta <= 0] = 0.0
        down_days = abs(delta.copy())
        down_days[delta > 0] = 0.0
        
        avg_gain = up_days.rolling(window=14).mean()
        avg_loss = down_days.rolling(window=14).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        metrics["RSI (14)"] = format_utils.format_number(rsi.iloc[-1])
        
    return metrics

def get_growth_metrics(info):
    """Get growth metrics from stock info"""
    metrics = {}
    
    # Earnings growth
    metrics["EPS Growth (1Y)"] = format_utils.format_percent(info.get("earningsGrowth", "N/A"))
    
    # Revenue growth
    metrics["Revenue Growth (1Y)"] = format_utils.format_percent(info.get("revenueGrowth", "N/A"))
    
    # Free cash flow growth
    metrics["Free Cash Flow Growth"] = format_utils.format_percent(info.get("freeCashFlowGrowth", "N/A"))
    
    # Future revenue growth (estimate)
    metrics["Est. Revenue Growth"] = format_utils.format_percent(info.get("revenueGrowthEstimate", "N/A"))
    
    # Future earnings growth (estimate)
    metrics["Est. EPS Growth"] = format_utils.format_percent(info.get("earningsGrowthEstimate", "N/A"))
    
    return metrics

def get_dividend_info(info, is_indian):
    """Get dividend information from stock info"""
    metrics = {}
    
    # Dividend rate
    dividend_rate = info.get("dividendRate", None)
    if dividend_rate is not None:
        metrics["Dividend Rate"] = format_utils.format_currency(dividend_rate, is_indian)
    else:
        metrics["Dividend Rate"] = "N/A"
    
    # Dividend yield
    dividend_yield = info.get("dividendYield", None)
    if dividend_yield is not None:
        metrics["Dividend Yield"] = format_utils.format_percent(dividend_yield)
    else:
        metrics["Dividend Yield"] = "N/A"
    
    # Payout ratio
    payout_ratio = info.get("payoutRatio", None)
    if payout_ratio is not None:
        metrics["Payout Ratio"] = format_utils.format_percent(payout_ratio)
    else:
        metrics["Payout Ratio"] = "N/A"
    
    # Ex-dividend date
    ex_dividend_date = info.get("exDividendDate", None)
    if ex_dividend_date is not None:
        metrics["Ex-Dividend Date"] = datetime.fromtimestamp(ex_dividend_date).strftime("%Y-%m-%d")
    else:
        metrics["Ex-Dividend Date"] = "N/A"
    
    # Last dividend date
    last_dividend_date = info.get("lastDividendDate", None)
    if last_dividend_date is not None:
        metrics["Last Dividend Date"] = datetime.fromtimestamp(last_dividend_date).strftime("%Y-%m-%d")
    else:
        metrics["Last Dividend Date"] = "N/A"
    
    return metrics

def get_price_info(info, is_indian):
    """Get price information from stock info"""
    metrics = {}
    
    # Current price
    current_price = info.get("currentPrice", None)
    if current_price is not None:
        metrics["Current Price"] = format_utils.format_currency(current_price, is_indian)
    else:
        metrics["Current Price"] = "N/A"
    
    # Previous close
    prev_close = info.get("previousClose", None)
    if prev_close is not None:
        metrics["Previous Close"] = format_utils.format_currency(prev_close, is_indian)
    else:
        metrics["Previous Close"] = "N/A"
    
    # Open price
    open_price = info.get("open", None)
    if open_price is not None:
        metrics["Open"] = format_utils.format_currency(open_price, is_indian)
    else:
        metrics["Open"] = "N/A"
    
    # Day low
    day_low = info.get("dayLow", None)
    if day_low is not None:
        metrics["Day Low"] = format_utils.format_currency(day_low, is_indian)
    else:
        metrics["Day Low"] = "N/A"
    
    # Day high
    day_high = info.get("dayHigh", None)
    if day_high is not None:
        metrics["Day High"] = format_utils.format_currency(day_high, is_indian)
    else:
        metrics["Day High"] = "N/A"
    
    # 52-week low
    week_low = info.get("fiftyTwoWeekLow", None)
    if week_low is not None:
        metrics["52-Week Low"] = format_utils.format_currency(week_low, is_indian)
    else:
        metrics["52-Week Low"] = "N/A"
    
    # 52-week high
    week_high = info.get("fiftyTwoWeekHigh", None)
    if week_high is not None:
        metrics["52-Week High"] = format_utils.format_currency(week_high, is_indian)
    else:
        metrics["52-Week High"] = "N/A"
    
    # Target price (analyst mean)
    target_mean_price = info.get("targetMeanPrice", None)
    if target_mean_price is not None:
        metrics["Target Price (Mean)"] = format_utils.format_currency(target_mean_price, is_indian)
    else:
        metrics["Target Price (Mean)"] = "N/A"
    
    return metrics

def get_volume_info(info):
    """Get volume information from stock info"""
    metrics = {}
    
    # Current volume
    volume = info.get("volume", None)
    if volume is not None:
        metrics["Volume"] = format_utils.format_large_number(volume)
    else:
        metrics["Volume"] = "N/A"
    
    # Average volume
    avg_volume = info.get("averageVolume", None)
    if avg_volume is not None:
        metrics["Avg Volume"] = format_utils.format_large_number(avg_volume)
    else:
        metrics["Avg Volume"] = "N/A"
    
    # Average 10-day volume
    avg_volume_10d = info.get("averageVolume10days", None)
    if avg_volume_10d is not None:
        metrics["Avg Volume (10d)"] = format_utils.format_large_number(avg_volume_10d)
    else:
        metrics["Avg Volume (10d)"] = "N/A"
    
    # Average 3-month volume
    avg_volume_3m = info.get("averageDailyVolume3Month", None)
    if avg_volume_3m is not None:
        metrics["Avg Volume (3m)"] = format_utils.format_large_number(avg_volume_3m)
    else:
        metrics["Avg Volume (3m)"] = "N/A"
    
    # Volume to average volume ratio
    if volume is not None and avg_volume is not None and avg_volume != 0:
        vol_ratio = volume / avg_volume
        metrics["Volume/Avg Ratio"] = format_utils.format_number(vol_ratio)
    else:
        metrics["Volume/Avg Ratio"] = "N/A"
    
    return metrics

def get_share_statistics(info, is_indian):
    """Get share statistics from stock info"""
    metrics = {}
    
    # Market cap
    market_cap = info.get("marketCap", None)
    if market_cap is not None:
        if is_indian:
            metrics["Market Cap"] = format_utils.format_indian_numbers(market_cap, in_crores=True) + " Cr"
        else:
            metrics["Market Cap"] = format_utils.format_large_number(market_cap)
    else:
        metrics["Market Cap"] = "N/A"
    
    # Enterprise value
    enterprise_value = info.get("enterpriseValue", None)
    if enterprise_value is not None:
        if is_indian:
            metrics["Enterprise Value"] = format_utils.format_indian_numbers(enterprise_value, in_crores=True) + " Cr"
        else:
            metrics["Enterprise Value"] = format_utils.format_large_number(enterprise_value)
    else:
        metrics["Enterprise Value"] = "N/A"
    
    # Shares outstanding
    shares_outstanding = info.get("sharesOutstanding", None)
    if shares_outstanding is not None:
        metrics["Shares Outstanding"] = format_utils.format_large_number(shares_outstanding)
    else:
        metrics["Shares Outstanding"] = "N/A"
    
    # Float shares
    float_shares = info.get("floatShares", None)
    if float_shares is not None:
        metrics["Float Shares"] = format_utils.format_large_number(float_shares)
    else:
        metrics["Float Shares"] = "N/A"
    
    # Institutional ownership
    institutional_ownership = info.get("heldPercentInstitutions", None)
    if institutional_ownership is not None:
        metrics["Institutional Ownership"] = format_utils.format_percent(institutional_ownership)
    else:
        metrics["Institutional Ownership"] = "N/A"
    
    # Insider ownership
    insider_ownership = info.get("heldPercentInsiders", None)
    if insider_ownership is not None:
        metrics["Insider Ownership"] = format_utils.format_percent(insider_ownership)
    else:
        metrics["Insider Ownership"] = "N/A"
    
    return metrics