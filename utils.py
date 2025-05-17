import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

@st.cache_data(ttl=3600)
def get_stock_data(ticker, period='1y'):
    """
    Fetch stock data from Yahoo Finance
    
    Args:
        ticker (str): Stock ticker symbol
        period (str): Time period to fetch data for
    
    Returns:
        pandas.DataFrame: Historical stock data
    """
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    
    if hist.empty:
        return pd.DataFrame()
    
    return hist

@st.cache_data(ttl=3600)
def get_company_info(ticker):
    """
    Fetch company information from Yahoo Finance
    
    Args:
        ticker (str): Stock ticker symbol
    
    Returns:
        dict: Company information
    """
    stock = yf.Ticker(ticker)
    info = stock.info
    return info

def format_large_number(num):
    """
    Format large numbers to K, M, B, T
    
    Args:
        num: Number to format
    
    Returns:
        str: Formatted number
    """
    if not isinstance(num, (int, float)):
        return "N/A"
    
    abs_num = abs(num)
    if abs_num >= 1_000_000_000_000:
        return f"${abs_num / 1_000_000_000_000:.2f}T"
    elif abs_num >= 1_000_000_000:
        return f"${abs_num / 1_000_000_000:.2f}B"
    elif abs_num >= 1_000_000:
        return f"${abs_num / 1_000_000:.2f}M"
    elif abs_num >= 1_000:
        return f"${abs_num / 1_000:.2f}K"
    else:
        return f"${abs_num:.2f}"

def create_line_chart(data, currency="$"):
    """
    Create a line chart for stock prices
    
    Args:
        data (pandas.DataFrame): Stock price data
        currency (str): Currency symbol to display (default: $)
    
    Returns:
        plotly.graph_objects.Figure: Line chart figure
    """
    fig = go.Figure()
    
    # Add close price line
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name='Close Price',
            line=dict(color='#2C6E49', width=2),
            hovertemplate=f'Date: %{{x}}<br>Price: {currency}%{{y:.2f}}<extra></extra>'
        )
    )
    
    # Add moving averages
    ma_periods = [20, 50, 200]
    colors = ['#4D908E', '#277DA1', '#F94144']
    
    for period, color in zip(ma_periods, colors):
        if len(data) >= period:
            ma_data = data['Close'].rolling(window=period).mean()
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=ma_data,
                    mode='lines',
                    name=f'{period}-day MA',
                    line=dict(color=color, width=1.5, dash='dot'),
                    hovertemplate=f'{period}-day MA: {currency}%{{y:.2f}}<extra></extra>'
                )
            )
    
    # Determine currency name for title
    currency_name = "USD"
    if currency == "₹":
        currency_name = "INR"
    
    # Update layout
    fig.update_layout(
        title=f"Stock Price History",
        xaxis_title="Date",
        yaxis_title=f"Price ({currency_name})",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    
    fig.update_yaxes(tickprefix='$')
    
    return fig

def create_candlestick_chart(data):
    """
    Create a candlestick chart for stock prices
    
    Args:
        data (pandas.DataFrame): Stock price data
    
    Returns:
        plotly.graph_objects.Figure: Candlestick chart figure
    """
    fig = go.Figure()
    
    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            increasing_line_color='#26A69A',
            decreasing_line_color='#EF5350',
            name='Price'
        )
    )
    
    # Update layout
    fig.update_layout(
        title="Candlestick Chart",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    
    fig.update_yaxes(tickprefix='$')
    
    return fig

def create_volume_chart(data):
    """
    Create a volume chart for stock trading volume
    
    Args:
        data (pandas.DataFrame): Stock price data
    
    Returns:
        plotly.graph_objects.Figure: Volume chart figure
    """
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add close price line
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name='Close Price',
            line=dict(color='#2C6E49', width=2),
            hovertemplate='Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
        ),
        secondary_y=True
    )
    
    # Add volume bars
    colors = ['#26A69A' if row['Close'] >= row['Open'] else '#EF5350' for _, row in data.iterrows()]
    
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color=colors,
            hovertemplate='Date: %{x}<br>Volume: %{y:,.0f}<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Update layout
    fig.update_layout(
        title="Price and Volume Analysis",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    
    # Update axes
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Volume", secondary_y=False)
    fig.update_yaxes(title_text="Price (USD)", tickprefix='$', secondary_y=True)
    
    return fig

@st.cache_data(ttl=3600)
def get_income_statement(ticker):
    """
    Fetch income statement data from Yahoo Finance
    
    Args:
        ticker (str): Stock ticker symbol
    
    Returns:
        pandas.DataFrame: Income statement data
    """
    try:
        stock = yf.Ticker(ticker)
        income_stmt = stock.income_stmt
        
        if income_stmt.empty:
            return pd.DataFrame()
        
        # Clean and format the data
        income_stmt = income_stmt.T
        
        # Format the numbers to millions
        income_stmt = income_stmt / 1_000_000
        
        return income_stmt
    except Exception as e:
        print(f"Error fetching income statement: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_balance_sheet(ticker):
    """
    Fetch balance sheet data from Yahoo Finance
    
    Args:
        ticker (str): Stock ticker symbol
    
    Returns:
        pandas.DataFrame: Balance sheet data
    """
    try:
        stock = yf.Ticker(ticker)
        balance_sheet = stock.balance_sheet
        
        if balance_sheet.empty:
            return pd.DataFrame()
        
        # Clean and format the data
        balance_sheet = balance_sheet.T
        
        # Format the numbers to millions
        balance_sheet = balance_sheet / 1_000_000
        
        return balance_sheet
    except Exception as e:
        print(f"Error fetching balance sheet: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_cash_flow(ticker):
    """
    Fetch cash flow data from Yahoo Finance
    
    Args:
        ticker (str): Stock ticker symbol
    
    Returns:
        pandas.DataFrame: Cash flow data
    """
    try:
        stock = yf.Ticker(ticker)
        cash_flow = stock.cashflow
        
        if cash_flow.empty:
            return pd.DataFrame()
        
        # Clean and format the data
        cash_flow = cash_flow.T
        
        # Format the numbers to millions
        cash_flow = cash_flow / 1_000_000
        
        return cash_flow
    except Exception as e:
        print(f"Error fetching cash flow: {e}")
        return pd.DataFrame()

def display_key_ratios_table(ratios_data):
    """
    Display key financial ratios in a table
    
    Args:
        ratios_data (dict): Key financial ratios
    """
    # Create two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Profitability Ratios")
        profitability = pd.DataFrame({
            "Ratio": ["Gross Margin", "Operating Margin", "Net Profit Margin", "Return on Assets (ROA)", "Return on Equity (ROE)"],
            "Value": [
                f"{ratios_data.get('grossMargins', 'N/A') * 100:.2f}%" if isinstance(ratios_data.get('grossMargins'), (int, float)) else "N/A",
                f"{ratios_data.get('operatingMargins', 'N/A') * 100:.2f}%" if isinstance(ratios_data.get('operatingMargins'), (int, float)) else "N/A",
                f"{ratios_data.get('profitMargins', 'N/A') * 100:.2f}%" if isinstance(ratios_data.get('profitMargins'), (int, float)) else "N/A",
                f"{ratios_data.get('returnOnAssets', 'N/A') * 100:.2f}%" if isinstance(ratios_data.get('returnOnAssets'), (int, float)) else "N/A",
                f"{ratios_data.get('returnOnEquity', 'N/A') * 100:.2f}%" if isinstance(ratios_data.get('returnOnEquity'), (int, float)) else "N/A"
            ]
        })
        st.table(profitability)
    
    with col2:
        st.subheader("Liquidity & Solvency Ratios")
        liquidity = pd.DataFrame({
            "Ratio": ["Current Ratio", "Quick Ratio", "Debt-to-Equity", "Interest Coverage"],
            "Value": [
                f"{ratios_data.get('currentRatio', 'N/A'):.2f}" if isinstance(ratios_data.get('currentRatio'), (int, float)) else "N/A",
                f"{ratios_data.get('quickRatio', 'N/A'):.2f}" if isinstance(ratios_data.get('quickRatio'), (int, float)) else "N/A",
                f"{ratios_data.get('debtToEquity', 'N/A'):.2f}" if isinstance(ratios_data.get('debtToEquity'), (int, float)) else "N/A",
                f"{ratios_data.get('interestCoverage', 'N/A'):.2f}" if isinstance(ratios_data.get('interestCoverage'), (int, float)) else "N/A"
            ]
        })
        st.table(liquidity)
    
    # Additional ratios in a single column
    st.subheader("Efficiency Ratios")
    efficiency = pd.DataFrame({
        "Ratio": ["Asset Turnover", "Inventory Turnover", "Receivables Turnover", "Payables Turnover"],
        "Value": [
            f"{ratios_data.get('assetTurnover', 'N/A'):.2f}" if isinstance(ratios_data.get('assetTurnover'), (int, float)) else "N/A",
            f"{ratios_data.get('inventoryTurnover', 'N/A'):.2f}" if isinstance(ratios_data.get('inventoryTurnover'), (int, float)) else "N/A",
            f"{ratios_data.get('receivablesTurnover', 'N/A'):.2f}" if isinstance(ratios_data.get('receivablesTurnover'), (int, float)) else "N/A",
            f"{ratios_data.get('payablesTurnover', 'N/A'):.2f}" if isinstance(ratios_data.get('payablesTurnover'), (int, float)) else "N/A"
        ]
    })
    st.table(efficiency)

def display_performance_table(performance_data):
    """
    Display stock performance metrics in a table
    
    Args:
        performance_data (dict): Stock performance metrics
    """
    # Create columns for different time periods
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Short-term Performance")
        short_term = pd.DataFrame({
            "Period": ["1 Day", "5 Day", "1 Month", "3 Month"],
            "Return": [
                f"{performance_data.get('oneDay', 'N/A'):.2f}%" if isinstance(performance_data.get('oneDay'), (int, float)) else "N/A",
                f"{performance_data.get('fiveDay', 'N/A'):.2f}%" if isinstance(performance_data.get('fiveDay'), (int, float)) else "N/A",
                f"{performance_data.get('oneMonth', 'N/A'):.2f}%" if isinstance(performance_data.get('oneMonth'), (int, float)) else "N/A",
                f"{performance_data.get('threeMonth', 'N/A'):.2f}%" if isinstance(performance_data.get('threeMonth'), (int, float)) else "N/A"
            ]
        })
        st.table(short_term)
    
    with col2:
        st.subheader("Medium-term Performance")
        medium_term = pd.DataFrame({
            "Period": ["6 Month", "YTD", "1 Year", "2 Year"],
            "Return": [
                f"{performance_data.get('sixMonth', 'N/A'):.2f}%" if isinstance(performance_data.get('sixMonth'), (int, float)) else "N/A",
                f"{performance_data.get('ytd', 'N/A'):.2f}%" if isinstance(performance_data.get('ytd'), (int, float)) else "N/A",
                f"{performance_data.get('oneYear', 'N/A'):.2f}%" if isinstance(performance_data.get('oneYear'), (int, float)) else "N/A",
                f"{performance_data.get('twoYear', 'N/A'):.2f}%" if isinstance(performance_data.get('twoYear'), (int, float)) else "N/A"
            ]
        })
        st.table(medium_term)
    
    with col3:
        st.subheader("Long-term Performance")
        long_term = pd.DataFrame({
            "Period": ["3 Year", "5 Year", "10 Year", "Max"],
            "Return": [
                f"{performance_data.get('threeYear', 'N/A'):.2f}%" if isinstance(performance_data.get('threeYear'), (int, float)) else "N/A",
                f"{performance_data.get('fiveYear', 'N/A'):.2f}%" if isinstance(performance_data.get('fiveYear'), (int, float)) else "N/A",
                f"{performance_data.get('tenYear', 'N/A'):.2f}%" if isinstance(performance_data.get('tenYear'), (int, float)) else "N/A",
                f"{performance_data.get('max', 'N/A'):.2f}%" if isinstance(performance_data.get('max'), (int, float)) else "N/A"
            ]
        })
        st.table(long_term)
    
    # Volatility metrics
    st.subheader("Volatility Metrics")
    volatility = pd.DataFrame({
        "Metric": ["Beta", "Standard Deviation (1Y)", "Sharpe Ratio", "Maximum Drawdown (1Y)"],
        "Value": [
            f"{performance_data.get('beta', 'N/A'):.2f}" if isinstance(performance_data.get('beta'), (int, float)) else "N/A",
            f"{performance_data.get('std1Y', 'N/A'):.2f}%" if isinstance(performance_data.get('std1Y'), (int, float)) else "N/A",
            f"{performance_data.get('sharpeRatio', 'N/A'):.2f}" if isinstance(performance_data.get('sharpeRatio'), (int, float)) else "N/A",
            f"{performance_data.get('maxDrawdown', 'N/A'):.2f}%" if isinstance(performance_data.get('maxDrawdown'), (int, float)) else "N/A"
        ]
    })
    st.table(volatility)

def display_valuation_table(valuation_data):
    """
    Display stock valuation metrics in a table
    
    Args:
        valuation_data (dict): Stock valuation metrics
    """
    # Create two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Price Multiples")
        price_multiples = pd.DataFrame({
            "Ratio": ["P/E Ratio (TTM)", "Forward P/E", "PEG Ratio", "P/S Ratio", "P/B Ratio"],
            "Value": [
                f"{valuation_data.get('trailingPE', 'N/A'):.2f}" if isinstance(valuation_data.get('trailingPE'), (int, float)) else "N/A",
                f"{valuation_data.get('forwardPE', 'N/A'):.2f}" if isinstance(valuation_data.get('forwardPE'), (int, float)) else "N/A",
                f"{valuation_data.get('pegRatio', 'N/A'):.2f}" if isinstance(valuation_data.get('pegRatio'), (int, float)) else "N/A",
                f"{valuation_data.get('priceToSalesTrailing12Months', 'N/A'):.2f}" if isinstance(valuation_data.get('priceToSalesTrailing12Months'), (int, float)) else "N/A",
                f"{valuation_data.get('priceToBook', 'N/A'):.2f}" if isinstance(valuation_data.get('priceToBook'), (int, float)) else "N/A"
            ]
        })
        st.table(price_multiples)
    
    with col2:
        st.subheader("Enterprise Value Multiples")
        ev_multiples = pd.DataFrame({
            "Ratio": ["EV/Revenue", "EV/EBITDA", "EV/EBIT", "EV/FCF"],
            "Value": [
                f"{valuation_data.get('enterpriseToRevenue', 'N/A'):.2f}" if isinstance(valuation_data.get('enterpriseToRevenue'), (int, float)) else "N/A",
                f"{valuation_data.get('enterpriseToEbitda', 'N/A'):.2f}" if isinstance(valuation_data.get('enterpriseToEbitda'), (int, float)) else "N/A",
                f"{valuation_data.get('enterpriseToEbit', 'N/A'):.2f}" if isinstance(valuation_data.get('enterpriseToEbit'), (int, float)) else "N/A",
                f"{valuation_data.get('enterpriseToFcf', 'N/A'):.2f}" if isinstance(valuation_data.get('enterpriseToFcf'), (int, float)) else "N/A"
            ]
        })
        st.table(ev_multiples)
    
    # Dividend metrics
    st.subheader("Dividend Metrics")
    dividends = pd.DataFrame({
        "Metric": ["Dividend Yield", "Dividend Payout Ratio", "Dividend Growth Rate (5Y)", "Years of Dividend Growth"],
        "Value": [
            f"{valuation_data.get('dividendYield', 'N/A') * 100:.2f}%" if isinstance(valuation_data.get('dividendYield'), (int, float)) else "N/A",
            f"{valuation_data.get('payoutRatio', 'N/A') * 100:.2f}%" if isinstance(valuation_data.get('payoutRatio'), (int, float)) else "N/A",
            f"{valuation_data.get('dividendGrowth5Y', 'N/A'):.2f}%" if isinstance(valuation_data.get('dividendGrowth5Y'), (int, float)) else "N/A",
            f"{valuation_data.get('dividendGrowthYears', 'N/A')}" if isinstance(valuation_data.get('dividendGrowthYears'), (int, float)) else "N/A"
        ]
    })
    st.table(dividends)
