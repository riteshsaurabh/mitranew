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
        
def create_price_chart(data, title, is_indian=False):
    """
    Create a price chart for stock with a modern, Gen-Z friendly design
    
    Args:
        data (pandas.DataFrame): Stock price data
        title (str): Chart title (usually company name)
        is_indian (bool): Whether it's an Indian stock (for currency symbol)
        
    Returns:
        plotly.graph_objects.Figure: Price chart figure
    """
    # Set currency based on whether it's an Indian stock
    currency = "₹" if is_indian else "$"
    
    # Create figure with secondary y-axis for volume
    fig = make_subplots(
        rows=2, 
        cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(f"{title} - Price", "Volume"),
        row_heights=[0.7, 0.3]
    )
    
    # Add price line
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name='Close Price',
            line=dict(color='#FF6B1A', width=2),
            hovertemplate=f'Date: %{{x}}<br>Price: {currency}%{{y:.2f}}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Add volume bars
    colors = ['#26A69A' if row['Close'] >= row['Open'] else '#EF5350' for _, row in data.iterrows()]
    
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.7,
            hovertemplate='Date: %{x}<br>Volume: %{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Determine currency name based on is_indian
    currency_name = "INR" if is_indian else "USD"
    
    # Update layout with modern styling
    fig.update_layout(
        title=None,  # We'll use Streamlit's header instead
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='rgba(250,250,250,0.9)',
        font=dict(
            family="Arial, sans-serif",
            size=12,
            color="#2D3047"
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        height=500
    )
    
    # Update axes for modern look
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(230,230,230,0.6)',
        zeroline=False
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(230,230,230,0.6)',
        zeroline=False,
        tickprefix=currency,
        row=1, col=1
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(230,230,230,0.6)',
        zeroline=False,
        row=2, col=1
    )
    
    return fig

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

def create_candlestick_chart(data, currency="$"):
    """
    Create a candlestick chart for stock prices
    
    Args:
        data (pandas.DataFrame): Stock price data
        currency (str): Currency symbol to display (default: $)
    
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
    
    # Determine currency name for title
    currency_name = "USD"
    if currency == "₹":
        currency_name = "INR"
    
    # Update layout
    fig.update_layout(
        title="Candlestick Chart",
        xaxis_title="Date",
        yaxis_title=f"Price ({currency_name})",
        xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    
    fig.update_yaxes(tickprefix=currency)
    
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

def display_metrics_cards(metrics_data, section_title="", is_indian=False):
    """
    Display financial metrics in a modern card layout
    
    Args:
        metrics_data (dict): Financial metrics to display
        section_title (str): Section title
        is_indian (bool): Whether to use Indian currency format
    """
    if section_title:
        st.markdown(f"<h4 style='margin-bottom: 15px;'>{section_title}</h4>", unsafe_allow_html=True)
    
    # Create columns for the metrics
    num_metrics = len(metrics_data)
    cols_per_row = 3
    
    # Calculate number of rows needed
    num_rows = (num_metrics + cols_per_row - 1) // cols_per_row
    
    # Generate rows of cards
    keys = list(metrics_data.keys())
    values = list(metrics_data.values())
    
    for row in range(num_rows):
        # Create columns for this row
        columns = st.columns(cols_per_row)
        
        # Add metrics to each column
        for col in range(cols_per_row):
            idx = row * cols_per_row + col
            if idx < num_metrics:
                with columns[col]:
                    # Generate a random color for the metric card
                    metric_colors = ["#FF6B1A", "#2D3047", "#00C853", "#2196F3"]
                    color = metric_colors[idx % len(metric_colors)]
                    
                    # Create a styled metric card
                    st.markdown(f"""
                    <div style="background: linear-gradient(90deg, {color}10, {color}05); 
                        padding: 15px; border-radius: 10px; border-left: 4px solid {color};
                        margin-bottom: 15px; height: 100%;">
                        <p style="color: #71717a; font-size: 0.8rem; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.05em;">
                            {keys[idx]}
                        </p>
                        <h3 style="color: #2D3047; margin: 0; font-size: 1.3rem; font-weight: 600;">
                            {values[idx]}
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)

def create_technical_chart(data, chart_title="Stock Price", chart_type="candlestick", indicators=None, ma_periods=None, is_indian=False):
    """
    Create a technical chart with user-selected indicators
    
    Args:
        data (pandas.DataFrame): Stock price data
        chart_title (str): Chart title
        chart_type (str): Chart type (candlestick, line, ohlc, area)
        indicators (list): List of indicators to include
        ma_periods (list): List of periods for moving averages
        is_indian (bool): Whether it's an Indian stock
        
    Returns:
        plotly.graph_objects.Figure: Technical chart figure
    """
    if indicators is None:
        indicators = []
    if ma_periods is None:
        ma_periods = []
    
    # Set currency based on whether it's an Indian stock
    currency = "₹" if is_indian else "$"
    
    # Create subplots with rows based on selected indicators
    rows = 1 + ("Volume" in indicators) + ("RSI" in indicators) + ("MACD" in indicators)
    row_heights = [0.5]
    
    # Define row heights for additional indicators
    if "Volume" in indicators:
        row_heights.append(0.1)
    if "RSI" in indicators:
        row_heights.append(0.2)
    if "MACD" in indicators:
        row_heights.append(0.2)
    
    # Create figure
    fig = make_subplots(
        rows=rows, 
        cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights
    )
    
    # Main price chart
    current_row = 1
    
    if chart_type == "candlestick":
        # Candlestick chart
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
            ),
            row=current_row, col=1
        )
    elif chart_type == "line":
        # Line chart
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['Close'],
                mode='lines',
                name='Close Price',
                line=dict(color='#FF6B1A', width=2),
                hovertemplate=f'Date: %{{x}}<br>Price: {currency}%{{y:.2f}}<extra></extra>'
            ),
            row=current_row, col=1
        )
    elif chart_type == "ohlc":
        # OHLC chart
        fig.add_trace(
            go.Ohlc(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                increasing_line_color='#26A69A',
                decreasing_line_color='#EF5350',
                name='Price'
            ),
            row=current_row, col=1
        )
    elif chart_type == "area":
        # Area chart
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['Close'],
                mode='lines',
                fill='tozeroy',
                name='Close Price',
                line=dict(color='#FF6B1A', width=2),
                fillcolor='rgba(255, 107, 26, 0.2)',
                hovertemplate=f'Date: %{{x}}<br>Price: {currency}%{{y:.2f}}<extra></extra>'
            ),
            row=current_row, col=1
        )
    
    # Add Moving Averages
    if "Moving Average" in indicators and ma_periods:
        colors = ['#4D908E', '#277DA1', '#F94144', '#F3722C', '#F8961E']
        
        for i, period in enumerate(ma_periods):
            if len(data) >= period:
                ma_data = data['Close'].rolling(window=period).mean()
                color = colors[i % len(colors)]
                
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=ma_data,
                        mode='lines',
                        name=f'{period}-day MA',
                        line=dict(color=color, width=1.5, dash='dot'),
                        hovertemplate=f'{period}-day MA: {currency}%{{y:.2f}}<extra></extra>'
                    ),
                    row=current_row, col=1
                )
    
    # Add Bollinger Bands
    if "Bollinger Bands" in indicators:
        # Calculate 20-day Moving Average
        ma20 = data['Close'].rolling(window=20).mean()
        
        # Calculate upper and lower bands (20-day MA +/- 2 standard deviations)
        std20 = data['Close'].rolling(window=20).std()
        upper_band = ma20 + (std20 * 2)
        lower_band = ma20 - (std20 * 2)
        
        # Add bands to chart
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=upper_band,
                mode='lines',
                name='Upper BB',
                line=dict(color='rgba(45, 48, 71, 0.4)', width=1, dash='dot'),
                hovertemplate=f'Upper BB: {currency}%{{y:.2f}}<extra></extra>'
            ),
            row=current_row, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=ma20,
                mode='lines',
                name='20-day MA',
                line=dict(color='rgba(45, 48, 71, 0.7)', width=1.5),
                hovertemplate=f'20-day MA: {currency}%{{y:.2f}}<extra></extra>'
            ),
            row=current_row, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=lower_band,
                mode='lines',
                name='Lower BB',
                line=dict(color='rgba(45, 48, 71, 0.4)', width=1, dash='dot'),
                hovertemplate=f'Lower BB: {currency}%{{y:.2f}}<extra></extra>',
                fill='tonexty',
                fillcolor='rgba(45, 48, 71, 0.05)'
            ),
            row=current_row, col=1
        )
    
    # Add Volume
    if "Volume" in indicators:
        current_row += 1
        colors = ['#26A69A' if row['Close'] >= row['Open'] else '#EF5350' for _, row in data.iterrows()]
        
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['Volume'],
                name='Volume',
                marker_color=colors,
                hovertemplate='Date: %{x}<br>Volume: %{y:,.0f}<extra></extra>'
            ),
            row=current_row, col=1
        )
    
    # Add RSI
    if "RSI" in indicators:
        current_row += 1
        
        # Calculate RSI
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Add RSI line
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=rsi,
                mode='lines',
                name='RSI (14)',
                line=dict(color='#FF6B1A', width=1.5),
                hovertemplate='RSI: %{y:.2f}<extra></extra>'
            ),
            row=current_row, col=1
        )
        
        # Add overbought/oversold lines
        fig.add_trace(
            go.Scatter(
                x=[data.index[0], data.index[-1]],
                y=[70, 70],
                mode='lines',
                name='Overbought',
                line=dict(color='#EF5350', width=1, dash='dash'),
                hoverinfo='none'
            ),
            row=current_row, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=[data.index[0], data.index[-1]],
                y=[30, 30],
                mode='lines',
                name='Oversold',
                line=dict(color='#26A69A', width=1, dash='dash'),
                hoverinfo='none'
            ),
            row=current_row, col=1
        )
    
    # Add MACD
    if "MACD" in indicators:
        current_row += 1
        
        # Calculate MACD
        ema12 = data['Close'].ewm(span=12, adjust=False).mean()
        ema26 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        
        # Add MACD line
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=macd,
                mode='lines',
                name='MACD',
                line=dict(color='#2D3047', width=1.5),
                hovertemplate='MACD: %{y:.2f}<extra></extra>'
            ),
            row=current_row, col=1
        )
        
        # Add signal line
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=signal,
                mode='lines',
                name='Signal',
                line=dict(color='#FF6B1A', width=1.5, dash='dot'),
                hovertemplate='Signal: %{y:.2f}<extra></extra>'
            ),
            row=current_row, col=1
        )
        
        # Add histogram
        colors = ['#26A69A' if val >= 0 else '#EF5350' for val in histogram]
        
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=histogram,
                name='Histogram',
                marker_color=colors,
                hovertemplate='Histogram: %{y:.2f}<extra></extra>'
            ),
            row=current_row, col=1
        )
    
    # Update layout with modern styling
    fig.update_layout(
        title=chart_title,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='rgba(250,250,250,0.9)',
        font=dict(
            family="Arial, sans-serif",
            size=12,
            color="#2D3047"
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=800 if rows > 2 else 600
    )
    
    # Update axes for modern look
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(230,230,230,0.6)',
        zeroline=False
    )
    
    # Apply stylish y-axes to all rows
    for row in range(1, rows + 1):
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(230,230,230,0.6)',
            zeroline=False,
            row=row, col=1
        )
    
    # Add currency prefix to price chart
    fig.update_yaxes(
        tickprefix=currency + ' ',
        row=1, col=1
    )
    
    # Set y-axis ranges for RSI
    if "RSI" in indicators:
        rsi_row = 1 + ("Volume" in indicators) + 1
        fig.update_yaxes(
            range=[0, 100],
            row=rsi_row, col=1
        )
    
    return fig

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
