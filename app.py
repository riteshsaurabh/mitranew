import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import utils
import financial_metrics
import simple_watchlist
import indian_markets
import stock_news
import stock_prediction
import format_utils

# Set page configuration
st.set_page_config(
    page_title="MoneyMitra - Your Financial Companion",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
with open("style.css") as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Title and description
st.markdown("""
<div style="display:flex; align-items:center; margin-bottom:20px; background:linear-gradient(90deg, #2D3047 0%, #1B998B 100%); padding:20px; border-radius:15px; box-shadow:0 4px 15px rgba(0,0,0,0.1);">
    <div style="margin-left:10px;">
        <h1 style="color:white; margin:0; font-weight:800;">MoneyMitra - Your Financial Mitra</h1>
        <p style="color:#EAEAEA; margin:5px 0 0 0; font-size:1rem;">Empowering informed investment decisions</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Function to get peer stock symbols based on sector
def get_peer_symbols(symbol, sector, is_indian=False):
    """
    Get peer stock symbols based on sector
    
    Args:
        symbol (str): Current stock symbol
        sector (str): Stock sector
        is_indian (bool): Whether it's an Indian stock
        
    Returns:
        list: List of peer stock symbols
    """
    if is_indian:
        # Define Indian peer stocks by sector
        indian_peers = {
            "Information Technology": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS"],
            "Financial Services": ["HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS"],
            "Oil & Gas": ["RELIANCE.NS", "ONGC.NS", "IOC.NS", "BPCL.NS", "HINDPETRO.NS"],
            "Automotive": ["TATAMOTORS.NS", "M&M.NS", "MARUTI.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS"],
            "Pharmaceutical": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "BIOCON.NS"],
            "Consumer Goods": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS"],
            "Metals & Mining": ["TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "COALINDIA.NS", "NMDC.NS"],
            "Telecommunications": ["BHARTIARTL.NS", "IDEA.NS", "TATACOMM.NS"],
            "Power": ["NTPC.NS", "POWERGRID.NS", "ADANIPOWER.NS", "TATAPOWER.NS", "TORNTPOWER.NS"]
        }
        
        default_sector = "Financial Services"
        sector_to_use = sector if sector in indian_peers else default_sector
        
        # Filter out the current symbol and return up to 4 peers
        peers = [p for p in indian_peers[sector_to_use] if p != symbol]
        return peers[:4]
    else:
        # For non-Indian stocks, use default peers by sector
        default_peers = {
            "Technology": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
            "Financial": ["JPM", "BAC", "GS", "WFC", "C"],
            "Healthcare": ["JNJ", "PFE", "MRK", "UNH", "ABBV"],
            "Consumer": ["PG", "KO", "PEP", "WMT", "MCD"],
            "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
            "Industrial": ["GE", "MMM", "CAT", "HON", "UPS"],
            "Utilities": ["NEE", "DUK", "SO", "D", "EXC"],
            "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "PSA"]
        }
        
        default_sector = "Technology"
        sector_to_use = next((k for k in default_peers.keys() if k.lower() in sector.lower()), default_sector)
        
        # Filter out the current symbol and return up to 4 peers
        peers = [p for p in default_peers[sector_to_use] if p != symbol]
        return peers[:4]

# Function to get peer comparison data
def get_peer_comparison_data(main_symbol, peer_symbols, is_indian=False):
    """
    Get peer comparison data for visualization
    
    Args:
        main_symbol (str): Main stock symbol to compare against
        peer_symbols (list): List of peer stock symbols
        is_indian (bool): Whether they're Indian stocks
        
    Returns:
        pd.DataFrame: DataFrame with peer comparison data
    """
    # Include the main symbol
    all_symbols = [main_symbol] + peer_symbols
    
    # Fetch data for all symbols
    data = {}
    for symbol in all_symbols:
        try:
            ticker = yf.Ticker(symbol)
            # Basic info
            info = ticker.info
            
            # Format the data
            name = info.get('shortName', symbol)
            if len(name) > 20:  # Truncate long names
                name = name[:18] + "..."
                
            price = info.get('currentPrice', None)
            market_cap = info.get('marketCap', None) 
            pe_ratio = info.get('trailingPE', None)
            eps = info.get('trailingEps', None)
            dividend_yield = info.get('dividendYield', None)
            
            # Format market cap to billions/crores
            if market_cap:
                if is_indian:
                    market_cap = market_cap / 10000000  # Convert to crores
                else:
                    market_cap = market_cap / 1000000000  # Convert to billions
            
            # Format price according to currency
            if is_indian and price:
                price_formatted = format_utils.format_currency(price, is_indian=True)
            elif price:
                price_formatted = format_utils.format_currency(price, is_indian=False)
            else:
                price_formatted = "N/A"
                
            # Format market cap
            if market_cap:
                if is_indian:
                    market_cap_formatted = format_utils.format_large_number(market_cap, is_indian=True) + " Cr"
                else:
                    market_cap_formatted = format_utils.format_large_number(market_cap, is_indian=False) + " B"
            else:
                market_cap_formatted = "N/A"
                
            # Add to data dictionary
            data[symbol] = {
                'Name': name,
                'Price': price_formatted,
                'Market Cap': market_cap_formatted,
                'P/E Ratio': format_utils.format_number(pe_ratio) if pe_ratio else "N/A",
                'EPS': format_utils.format_currency(eps, is_indian) if eps else "N/A",
                'Dividend Yield': format_utils.format_percent(dividend_yield) if dividend_yield else "N/A",
                # Raw values for sorting
                '_price': price,
                '_market_cap': market_cap,
                '_pe': pe_ratio,
                '_eps': eps,
                '_dividend_yield': dividend_yield
            }
        except Exception as e:
            data[symbol] = {
                'Name': symbol,
                'Price': "Error",
                'Market Cap': "Error",
                'P/E Ratio': "Error",
                'EPS': "Error", 
                'Dividend Yield': "Error",
                # Raw values for sorting
                '_price': None,
                '_market_cap': None,
                '_pe': None,
                '_eps': None,
                '_dividend_yield': None
            }
            
    # Create a DataFrame
    df = pd.DataFrame(data).T
    
    # Reorder columns
    display_cols = ['Name', 'Price', 'Market Cap', 'P/E Ratio', 'EPS', 'Dividend Yield']
    df = df[display_cols]
    
    return df

# Sidebar for watchlists and other tools
with st.sidebar:
    st.markdown('<div style="text-align:center;"><h3 style="color:#1B998B;">Your Watchlists</h3></div>', unsafe_allow_html=True)
    
    # Display watchlists
    simple_watchlist.display_watchlist_sidebar()

# Modern search container
st.markdown("""
<div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
    margin-bottom: 30px; border-left: 4px solid #FF6B1A;">
    <h3 style="margin-top:0; color:#2D3047; font-weight:600; margin-bottom:15px;">
        <span style="color:#FF6B1A; margin-right:10px;">📊</span>Find Your Investment
    </h3>
    <p style="color:#71717A; font-size:0.9rem; margin-bottom:20px;">
        Enter stock symbol to analyze market performance and financial metrics
    </p>
</div>
""", unsafe_allow_html=True)

# Input for stock symbol with modern styling
col_symbol, col_period = st.columns([1, 1])

with col_symbol:
    # Check if a stock was selected from the watchlist
    initial_value = st.session_state.get('selected_stock', 'RELIANCE.NS')
    # Make sure initial_value is not None 
    if initial_value is None:
        initial_value = 'RELIANCE.NS'
        
    st.markdown('<p style="font-weight:600; font-size:0.9rem; margin-bottom:8px;">Stock Symbol</p>', unsafe_allow_html=True)
    stock_symbol = st.text_input("", value=initial_value, placeholder="e.g., RELIANCE.NS, INFY.NS")
    
    # Help text for NSE stocks
    st.markdown('<p style="color:#71717A; font-size:0.75rem;">Use .NS for NSE stocks (e.g., RELIANCE.NS)</p>', unsafe_allow_html=True)

with col_period:
    # Custom styled select box
    st.markdown('<p style="font-weight:600; font-size:0.9rem; margin-bottom:8px;">Time Period</p>', unsafe_allow_html=True)
    time_period = st.selectbox(
        "",
        ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
        format_func=lambda x: {
            "1mo": "1 Month",
            "3mo": "3 Months",
            "6mo": "6 Months",
            "1y": "1 Year",
            "2y": "2 Years",
            "5y": "5 Years",
            "10y": "10 Years",
            "ytd": "Year to Date",
            "max": "Maximum"
        }[x]
    )

# Load data with status indicator
with st.spinner(f"Loading data for {stock_symbol}..."):
    try:
        # Check if it's an Indian stock
        is_indian = indian_markets.is_indian_symbol(stock_symbol)
        
        # If symbol doesn't include .NS or .BO for Indian stocks, add it
        if is_indian and not ('.NS' in stock_symbol or '.BO' in stock_symbol):
            stock_symbol = indian_markets.format_indian_symbol(stock_symbol)
            
        # Get stock data with appropriate handling for Indian stocks
        if is_indian:
            stock_data = indian_markets.get_indian_stock_data(stock_symbol, period=time_period)
            company_info = indian_markets.get_indian_company_info(stock_symbol)
        else:
            stock_data = yf.download(stock_symbol, period=time_period)
            ticker = yf.Ticker(stock_symbol)
            company_info = ticker.info
            
        if stock_data.empty:
            st.error(f"No data found for {stock_symbol}. Please check the symbol and try again.")
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        stock_data = pd.DataFrame()
        company_info = {}

# Check if data was loaded successfully
if not stock_data.empty:
    # Get company name and logo if available
    company_name = company_info.get('shortName', stock_symbol)
    company_sector = company_info.get('sector', 'N/A')
    company_industry = company_info.get('industry', 'N/A')
    company_website = company_info.get('website', '#')
    
    # Display company header
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
            <h2 style="margin:0; color:#2D3047;">{company_name}</h2>
            <div style="display:flex; gap:15px; margin-top:10px;">
                <span style="background:#f0f0f0; padding:5px 12px; border-radius:20px; font-size:0.8rem; color:#555;">
                    <strong>Sector:</strong> {company_sector}
                </span>
                <span style="background:#f0f0f0; padding:5px 12px; border-radius:20px; font-size:0.8rem; color:#555;">
                    <strong>Industry:</strong> {company_industry}
                </span>
                <a href="{company_website}" target="_blank" style="background:#1B998B; padding:5px 12px; border-radius:20px; font-size:0.8rem; color:white; text-decoration:none;">
                    Company Website
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Display current stock price with change
        current_price = stock_data['Close'].iloc[-1]
        prev_close = stock_data['Close'].iloc[-2] if len(stock_data) > 1 else stock_data['Close'].iloc[0]
        price_change = current_price - prev_close
        price_change_pct = (price_change / prev_close) * 100
        
        price_color = "#16C172" if price_change >= 0 else "#F05D5E"
        price_icon = "▲" if price_change >= 0 else "▼"
        
        if is_indian:
            formatted_price = format_utils.format_currency(current_price, is_indian=True)
            formatted_change = format_utils.format_currency(price_change, is_indian=True)
        else:
            formatted_price = format_utils.format_currency(current_price, is_indian=False)
            formatted_change = format_utils.format_currency(price_change, is_indian=False)
            
        formatted_change_pct = format_utils.format_percent(price_change_pct/100)
        
        st.markdown(f"""
        <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); text-align:center;">
            <p style="margin:0; font-size:0.8rem; color:#71717A;">Current Price</p>
            <h2 style="margin:5px 0; color:{price_color};">{formatted_price}</h2>
            <p style="margin:0; font-size:0.9rem; color:{price_color};">
                {price_icon} {formatted_change} ({formatted_change_pct})
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content tabs
    main_tabs = st.tabs([
        "📈 Overview", 
        "💰 Financial Metrics", 
        "📋 Income Statement", 
        "📊 Balance Sheet", 
        "💸 Cash Flow",
        "🔎 Peer Comparison", 
        "📰 News & Analysis",
        "📌 SWOT Analysis"
    ])
    
    # OVERVIEW TAB
    with main_tabs[0]:
        # Stock chart
        st.markdown("### Stock Price Chart")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Chart type selection
            chart_type = st.radio(
                "Select chart type:",
                ["Line", "Candlestick", "OHLC"],
                horizontal=True,
                key="chart_type"
            )
            
        with col2:
            # Add chart indicators
            indicators = st.multiselect(
                "Add indicators:",
                ["SMA (20)", "SMA (50)", "SMA (200)", "EMA (20)", "Bollinger Bands"],
                key="indicators"
            )
        
        # Create the chart based on user selection
        if chart_type == "Line":
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=stock_data.index,
                y=stock_data['Close'],
                mode='lines',
                name='Close Price',
                line=dict(color='royalblue', width=2)
            ))
            
        elif chart_type == "Candlestick":
            fig = go.Figure(go.Candlestick(
                x=stock_data.index,
                open=stock_data['Open'],
                high=stock_data['High'],
                low=stock_data['Low'],
                close=stock_data['Close'],
                increasing_line_color='#16C172', 
                decreasing_line_color='#F05D5E'
            ))
            
        elif chart_type == "OHLC":
            fig = go.Figure(go.Ohlc(
                x=stock_data.index,
                open=stock_data['Open'],
                high=stock_data['High'],
                low=stock_data['Low'],
                close=stock_data['Close'],
                increasing_line_color='#16C172', 
                decreasing_line_color='#F05D5E'
            ))
        
        # Add indicators if selected
        if "SMA (20)" in indicators:
            stock_data['SMA20'] = stock_data['Close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(
                x=stock_data.index,
                y=stock_data['SMA20'],
                mode='lines',
                name='SMA 20',
                line=dict(color='orange', width=1)
            ))
            
        if "SMA (50)" in indicators:
            stock_data['SMA50'] = stock_data['Close'].rolling(window=50).mean()
            fig.add_trace(go.Scatter(
                x=stock_data.index,
                y=stock_data['SMA50'],
                mode='lines',
                name='SMA 50',
                line=dict(color='purple', width=1)
            ))
            
        if "SMA (200)" in indicators:
            stock_data['SMA200'] = stock_data['Close'].rolling(window=200).mean()
            fig.add_trace(go.Scatter(
                x=stock_data.index,
                y=stock_data['SMA200'],
                mode='lines',
                name='SMA 200',
                line=dict(color='red', width=1)
            ))
            
        if "EMA (20)" in indicators:
            stock_data['EMA20'] = stock_data['Close'].ewm(span=20, adjust=False).mean()
            fig.add_trace(go.Scatter(
                x=stock_data.index,
                y=stock_data['EMA20'],
                mode='lines',
                name='EMA 20',
                line=dict(color='green', width=1)
            ))
            
        if "Bollinger Bands" in indicators:
            stock_data['SMA20'] = stock_data['Close'].rolling(window=20).mean()
            stock_data['Upper'] = stock_data['SMA20'] + (stock_data['Close'].rolling(window=20).std() * 2)
            stock_data['Lower'] = stock_data['SMA20'] - (stock_data['Close'].rolling(window=20).std() * 2)
            
            fig.add_trace(go.Scatter(
                x=stock_data.index,
                y=stock_data['Upper'],
                mode='lines',
                name='Upper Band',
                line=dict(color='rgba(0,128,0,0.3)', width=1)
            ))
            
            fig.add_trace(go.Scatter(
                x=stock_data.index,
                y=stock_data['Lower'],
                mode='lines',
                name='Lower Band',
                line=dict(color='rgba(0,128,0,0.3)', width=1),
                fill='tonexty',
                fillcolor='rgba(0,128,0,0.1)'
            ))
        
        # Update layout
        time_period_map = {
            '1mo': '1 Month', 
            '3mo': '3 Months', 
            '6mo': '6 Months', 
            '1y': '1 Year', 
            '2y': '2 Years', 
            '5y': '5 Years', 
            '10y': '10 Years', 
            'ytd': 'Year to Date', 
            'max': 'Maximum'
        }
        fig.update_layout(
            title=f"{company_name} ({stock_symbol}) - {time_period_map.get(time_period, time_period)}",
            xaxis_title="Date",
            yaxis_title=f"Price ({format_utils.format_currency(0, is_indian).strip('0')})",
            height=500,
            template="plotly_white",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Volume subplot
        st.markdown("### Trading Volume")
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=stock_data.index,
            y=stock_data['Volume'],
            name='Volume',
            marker=dict(color='rgba(58, 71, 80, 0.6)')
        ))
        
        fig.update_layout(
            title=f"Trading Volume - {company_name}",
            xaxis_title="Date",
            yaxis_title="Volume",
            height=250,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add benchmark comparison
        st.markdown("### Compare with Benchmark")
        
        if is_indian:
            # Indian benchmark indices
            benchmark_tabs = st.tabs(["NIFTY 50", "SENSEX"])
            
            with benchmark_tabs[0]:
                with st.spinner("Loading NIFTY 50 data..."):
                    try:
                        nifty_data = indian_markets.get_nifty_index_data(time_period)
                        if not nifty_data.empty:
                            # Create a comparison chart
                            fig = go.Figure()
                            
                            # Normalize data for comparison (start at 100)
                            stock_normalized = stock_data['Close'] / stock_data['Close'].iloc[0] * 100
                            nifty_normalized = nifty_data['Close'] / nifty_data['Close'].iloc[0] * 100
                            
                            # Add stock line
                            fig.add_trace(go.Scatter(
                                x=stock_data.index,
                                y=stock_normalized,
                                name=stock_symbol,
                                line=dict(color='royalblue')
                            ))
                            
                            # Add NIFTY line
                            fig.add_trace(go.Scatter(
                                x=nifty_data.index,
                                y=nifty_normalized,
                                name='NIFTY 50',
                                line=dict(color='orange')
                            ))
                            
                            # Update layout
                            fig.update_layout(
                                title=f"{company_name} vs NIFTY 50 (Normalized to 100)",
                                xaxis_title="Date",
                                yaxis_title="Normalized Price",
                                height=400,
                                template="plotly_white",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Calculate performance metrics
                            stock_return = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100
                            nifty_return = ((nifty_data['Close'].iloc[-1] / nifty_data['Close'].iloc[0]) - 1) * 100
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric(
                                    f"{stock_symbol} Return", 
                                    f"{format_utils.format_percent(stock_return/100)}", 
                                    f"{format_utils.format_percent((stock_return - nifty_return)/100)} vs NIFTY 50"
                                )
                                
                            with col2:
                                st.metric(
                                    "NIFTY 50 Return", 
                                    f"{format_utils.format_percent(nifty_return/100)}"
                                )
                        else:
                            st.warning("Could not load NIFTY 50 data for comparison.")
                    except Exception as e:
                        st.error(f"Error comparing with NIFTY 50: {str(e)}")
            
            with benchmark_tabs[1]:
                with st.spinner("Loading SENSEX data..."):
                    try:
                        sensex_data = indian_markets.get_sensex_index_data(time_period)
                        if not sensex_data.empty:
                            # Create a comparison chart
                            fig = go.Figure()
                            
                            # Normalize data for comparison (start at 100)
                            stock_normalized = stock_data['Close'] / stock_data['Close'].iloc[0] * 100
                            sensex_normalized = sensex_data['Close'] / sensex_data['Close'].iloc[0] * 100
                            
                            # Add stock line
                            fig.add_trace(go.Scatter(
                                x=stock_data.index,
                                y=stock_normalized,
                                name=stock_symbol,
                                line=dict(color='royalblue')
                            ))
                            
                            # Add SENSEX line
                            fig.add_trace(go.Scatter(
                                x=sensex_data.index,
                                y=sensex_normalized,
                                name='SENSEX',
                                line=dict(color='green')
                            ))
                            
                            # Update layout
                            fig.update_layout(
                                title=f"{company_name} vs SENSEX (Normalized to 100)",
                                xaxis_title="Date",
                                yaxis_title="Normalized Price",
                                height=400,
                                template="plotly_white",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Calculate performance metrics
                            stock_return = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100
                            sensex_return = ((sensex_data['Close'].iloc[-1] / sensex_data['Close'].iloc[0]) - 1) * 100
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric(
                                    f"{stock_symbol} Return", 
                                    f"{format_utils.format_percent(stock_return/100)}", 
                                    f"{format_utils.format_percent((stock_return - sensex_return)/100)} vs SENSEX"
                                )
                                
                            with col2:
                                st.metric(
                                    "SENSEX Return", 
                                    f"{format_utils.format_percent(sensex_return/100)}"
                                )
                        else:
                            st.warning("Could not load SENSEX data for comparison.")
                    except Exception as e:
                        st.error(f"Error comparing with SENSEX: {str(e)}")
        else:
            # International benchmark indices
            benchmark_tabs = st.tabs(["S&P 500", "NASDAQ"])
            
            with benchmark_tabs[0]:
                with st.spinner("Loading S&P 500 data..."):
                    try:
                        sp500_data = yf.download("^GSPC", period=time_period)
                        if not sp500_data.empty:
                            # Create a comparison chart
                            fig = go.Figure()
                            
                            # Normalize data for comparison (start at 100)
                            stock_normalized = stock_data['Close'] / stock_data['Close'].iloc[0] * 100
                            sp500_normalized = sp500_data['Close'] / sp500_data['Close'].iloc[0] * 100
                            
                            # Add stock line
                            fig.add_trace(go.Scatter(
                                x=stock_data.index,
                                y=stock_normalized,
                                name=stock_symbol,
                                line=dict(color='royalblue')
                            ))
                            
                            # Add S&P 500 line
                            fig.add_trace(go.Scatter(
                                x=sp500_data.index,
                                y=sp500_normalized,
                                name='S&P 500',
                                line=dict(color='orange')
                            ))
                            
                            # Update layout
                            fig.update_layout(
                                title=f"{company_name} vs S&P 500 (Normalized to 100)",
                                xaxis_title="Date",
                                yaxis_title="Normalized Price",
                                height=400,
                                template="plotly_white",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Calculate performance metrics
                            stock_return = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100
                            sp500_return = ((sp500_data['Close'].iloc[-1] / sp500_data['Close'].iloc[0]) - 1) * 100
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric(
                                    f"{stock_symbol} Return", 
                                    f"{format_utils.format_percent(stock_return/100)}", 
                                    f"{format_utils.format_percent((stock_return - sp500_return)/100)} vs S&P 500"
                                )
                                
                            with col2:
                                st.metric(
                                    "S&P 500 Return", 
                                    f"{format_utils.format_percent(sp500_return/100)}"
                                )
                        else:
                            st.warning("Could not load S&P 500 data for comparison.")
                    except Exception as e:
                        st.error(f"Error comparing with S&P 500: {str(e)}")
            
            with benchmark_tabs[1]:
                with st.spinner("Loading NASDAQ data..."):
                    try:
                        nasdaq_data = yf.download("^IXIC", period=time_period)
                        if not nasdaq_data.empty:
                            # Create a comparison chart
                            fig = go.Figure()
                            
                            # Normalize data for comparison (start at 100)
                            stock_normalized = stock_data['Close'] / stock_data['Close'].iloc[0] * 100
                            nasdaq_normalized = nasdaq_data['Close'] / nasdaq_data['Close'].iloc[0] * 100
                            
                            # Add stock line
                            fig.add_trace(go.Scatter(
                                x=stock_data.index,
                                y=stock_normalized,
                                name=stock_symbol,
                                line=dict(color='royalblue')
                            ))
                            
                            # Add NASDAQ line
                            fig.add_trace(go.Scatter(
                                x=nasdaq_data.index,
                                y=nasdaq_normalized,
                                name='NASDAQ',
                                line=dict(color='green')
                            ))
                            
                            # Update layout
                            fig.update_layout(
                                title=f"{company_name} vs NASDAQ (Normalized to 100)",
                                xaxis_title="Date",
                                yaxis_title="Normalized Price",
                                height=400,
                                template="plotly_white",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Calculate performance metrics
                            stock_return = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100
                            nasdaq_return = ((nasdaq_data['Close'].iloc[-1] / nasdaq_data['Close'].iloc[0]) - 1) * 100
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric(
                                    f"{stock_symbol} Return", 
                                    f"{format_utils.format_percent(stock_return/100)}", 
                                    f"{format_utils.format_percent((stock_return - nasdaq_return)/100)} vs NASDAQ"
                                )
                                
                            with col2:
                                st.metric(
                                    "NASDAQ Return", 
                                    f"{format_utils.format_percent(nasdaq_return/100)}"
                                )
                        else:
                            st.warning("Could not load NASDAQ data for comparison.")
                    except Exception as e:
                        st.error(f"Error comparing with NASDAQ: {str(e)}")
                        
    # FINANCIAL METRICS TAB
    with main_tabs[1]:
        with st.spinner("Loading financial metrics..."):
            try:
                metrics = financial_metrics.get_financial_metrics(stock_symbol)
                
                if metrics:
                    # Key ratios
                    st.markdown("### Key Financial Ratios")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("""
                        <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                            <h4 style="margin:0 0 10px 0; color:#FF6B1A; border-bottom:1px solid #eee; padding-bottom:8px;">Valuation</h4>
                        """, unsafe_allow_html=True)
                        
                        for key, value in metrics['valuation_metrics'].items():
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; margin:8px 0;">
                                <span style="color:#555;">{key}</span>
                                <span style="font-weight:600;">{value}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("""
                        <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                            <h4 style="margin:0 0 10px 0; color:#16C172; border-bottom:1px solid #eee; padding-bottom:8px;">Profitability</h4>
                        """, unsafe_allow_html=True)
                        
                        for key, value in metrics['profitability_ratios'].items():
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; margin:8px 0;">
                                <span style="color:#555;">{key}</span>
                                <span style="font-weight:600;">{value}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown("""
                        <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                            <h4 style="margin:0 0 10px 0; color:#1B998B; border-bottom:1px solid #eee; padding-bottom:8px;">Financial Health</h4>
                        """, unsafe_allow_html=True)
                        
                        for key, value in metrics['financial_health'].items():
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; margin:8px 0;">
                                <span style="color:#555;">{key}</span>
                                <span style="font-weight:600;">{value}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Performance metrics
                    st.markdown("### Performance Metrics")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("""
                        <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                            <h4 style="margin:0 0 10px 0; color:#2D3047; border-bottom:1px solid #eee; padding-bottom:8px;">Returns</h4>
                        """, unsafe_allow_html=True)
                        
                        for key, value in metrics['performance_metrics'].items():
                            if 'Return' in key:
                                st.markdown(f"""
                                <div style="display:flex; justify-content:space-between; margin:8px 0;">
                                    <span style="color:#555;">{key}</span>
                                    <span style="font-weight:600; color:{'#16C172' if float(value.strip('%')) > 0 else '#F05D5E'}">
                                        {value}
                                    </span>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("""
                        <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                            <h4 style="margin:0 0 10px 0; color:#2D3047; border-bottom:1px solid #eee; padding-bottom:8px;">Volatility</h4>
                        """, unsafe_allow_html=True)
                        
                        for key, value in metrics['performance_metrics'].items():
                            if 'Volatility' in key or 'Beta' in key:
                                st.markdown(f"""
                                <div style="display:flex; justify-content:space-between; margin:8px 0;">
                                    <span style="color:#555;">{key}</span>
                                    <span style="font-weight:600;">
                                        {value}
                                    </span>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown("""
                        <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                            <h4 style="margin:0 0 10px 0; color:#2D3047; border-bottom:1px solid #eee; padding-bottom:8px;">Technical</h4>
                        """, unsafe_allow_html=True)
                        
                        for key, value in metrics['technical_indicators'].items():
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; margin:8px 0;">
                                <span style="color:#555;">{key}</span>
                                <span style="font-weight:600;">
                                    {value}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Growth metrics
                    st.markdown("### Growth & Dividend")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("""
                        <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                            <h4 style="margin:0 0 10px 0; color:#FF6B1A; border-bottom:1px solid #eee; padding-bottom:8px;">Growth Metrics</h4>
                        """, unsafe_allow_html=True)
                        
                        for key, value in metrics['growth_metrics'].items():
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; margin:8px 0;">
                                <span style="color:#555;">{key}</span>
                                <span style="font-weight:600; color:{'#16C172' if value != 'N/A' and float(value.strip('%')) > 0 else ('#F05D5E' if value != 'N/A' and float(value.strip('%')) < 0 else '#555')}">
                                    {value}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("""
                        <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                            <h4 style="margin:0 0 10px 0; color:#16C172; border-bottom:1px solid #eee; padding-bottom:8px;">Dividend Information</h4>
                        """, unsafe_allow_html=True)
                        
                        for key, value in metrics['dividend_info'].items():
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; margin:8px 0;">
                                <span style="color:#555;">{key}</span>
                                <span style="font-weight:600;">
                                    {value}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Trading Information
                    st.markdown("### Trading Information")
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        st.markdown("""
                        <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                            <h4 style="margin:0 0 10px 0; color:#2D3047; border-bottom:1px solid #eee; padding-bottom:8px;">Price Info</h4>
                        """, unsafe_allow_html=True)
                        
                        for key, value in metrics['price_info'].items():
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; margin:8px 0;">
                                <span style="color:#555;">{key}</span>
                                <span style="font-weight:600;">
                                    {value}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("""
                        <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                            <h4 style="margin:0 0 10px 0; color:#2D3047; border-bottom:1px solid #eee; padding-bottom:8px;">Volume Info</h4>
                        """, unsafe_allow_html=True)
                        
                        for key, value in metrics['volume_info'].items():
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; margin:8px 0;">
                                <span style="color:#555;">{key}</span>
                                <span style="font-weight:600;">
                                    {value}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown("""
                        <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                            <h4 style="margin:0 0 10px 0; color:#2D3047; border-bottom:1px solid #eee; padding-bottom:8px;">Share Statistics</h4>
                        """, unsafe_allow_html=True)
                        
                        for key, value in metrics['share_statistics'].items():
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; margin:8px 0;">
                                <span style="color:#555;">{key}</span>
                                <span style="font-weight:600;">
                                    {value}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.warning("Financial metrics could not be loaded for this stock.")
            except Exception as e:
                st.error(f"Error loading financial metrics: {str(e)}")

    # INCOME STATEMENT TAB
    with main_tabs[2]:
        st.markdown("""
        <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:20px;">
            <h3 style="margin-top:0; color:#2D3047;">Income Statement (Profit & Loss)</h3>
            <p style="color:#71717A; font-size:0.9rem; margin-bottom:0;">
                Financial data shown in {currency} {unit}. Data source: Yahoo Finance.
            </p>
        </div>
        """.format(
            currency="₹" if is_indian else "$",
            unit="Crores" if is_indian else "Millions"
        ), unsafe_allow_html=True)
        
        with st.spinner("Loading income statement..."):
            try:
                # Get ticker object
                ticker = yf.Ticker(stock_symbol)
                
                # Get income statement data
                income_stmt = ticker.income_stmt
                
                if income_stmt is not None and not income_stmt.empty:
                    # Format dates
                    if isinstance(income_stmt.columns, pd.DatetimeIndex):
                        income_stmt.columns = income_stmt.columns.strftime('%b %Y')
                    
                    # Convert values to appropriate scale
                    formatted_income = income_stmt.copy()
                    
                    for col in formatted_income.columns:
                        formatted_income[col] = formatted_income[col].apply(
                            lambda x: x / 10000000 if is_indian else x / 1000000  # ₹ Crores for Indian, $ Millions for others
                        )
                    
                    # Create a standardized P&L format with key metrics
                    pl_items = [
                        "Total Revenue", 
                        "Cost of Revenue",
                        "Gross Profit",
                        "Operating Expense",
                        "Operating Income",
                        "Interest Expense", 
                        "Income Before Tax",
                        "Income Tax Expense", 
                        "Net Income",
                        "Basic EPS",
                        "Diluted EPS"
                    ]
                    
                    # Create a new DataFrame with our desired metrics
                    pl_data = pd.DataFrame(index=pl_items)
                    
                    # Map Yahoo Finance data to our format
                    mapping = {
                        "Total Revenue": ["Total Revenue", "Revenue"],
                        "Cost of Revenue": ["Cost Of Revenue", "Cost of Revenue"],
                        "Gross Profit": ["Gross Profit"],
                        "Operating Expense": ["Operating Expense", "Total Operating Expenses"],
                        "Operating Income": ["Operating Income", "EBIT"],
                        "Interest Expense": ["Interest Expense"],
                        "Income Before Tax": ["Income Before Tax", "Pretax Income"],
                        "Income Tax Expense": ["Income Tax Expense", "Tax Provision"],
                        "Net Income": ["Net Income", "Net Income Common Stockholders"],
                        "Basic EPS": ["Basic EPS"],
                        "Diluted EPS": ["Diluted EPS", "EPS - Earnings Per Share"]
                    }
                    
                    # Fill in our P&L DataFrame
                    for pl_item in pl_items:
                        for possible_key in mapping[pl_item]:
                            if possible_key in formatted_income.index:
                                pl_data.loc[pl_item] = formatted_income.loc[possible_key]
                                break
                    
                    # Display the data
                    st.dataframe(
                        pl_data,
                        use_container_width=True,
                        hide_index=False,
                        column_config={col: {"format": "%.2f"} for col in pl_data.columns}
                    )
                    
                    # Display visualization for key metrics
                    st.markdown("### Key Income Statement Trends")
                    
                    # Select key metrics to visualize
                    key_metrics = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income"]
                    metrics_to_plot = [metric for metric in key_metrics if metric in pl_data.index]
                    
                    if metrics_to_plot:
                        # Create visualization
                        fig = go.Figure()
                        
                        for metric in metrics_to_plot:
                            fig.add_trace(go.Bar(
                                x=pl_data.columns,
                                y=pl_data.loc[metric],
                                name=metric
                            ))
                        
                        # Update layout
                        fig.update_layout(
                            title="Key Financial Metrics Over Time",
                            xaxis_title="Reporting Period",
                            yaxis_title=f"Value ({format_utils.format_currency(0, is_indian).strip('0')} {'Crores' if is_indian else 'Millions'})",
                            legend_title="Metrics",
                            height=400,
                            template="plotly_white",
                            barmode='group'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Calculate and display growth rates
                        st.markdown("### Year-over-Year Growth Rates")
                        
                        growth_data = {}
                        for metric in metrics_to_plot:
                            values = pl_data.loc[metric].values
                            growth = []
                            for i in range(1, len(values)):
                                if values[i-1] != 0 and not pd.isna(values[i-1]) and not pd.isna(values[i]):
                                    growth.append((values[i] / values[i-1] - 1) * 100)
                                else:
                                    growth.append(None)
                            growth_data[metric] = [None] + growth  # Add None for the first period (no YoY growth)
                        
                        growth_df = pd.DataFrame(growth_data, index=pl_data.columns)
                        
                        # Create a formatted version for display
                        growth_df_display = growth_df.copy()
                        for col in growth_df_display.columns:
                            growth_df_display[col] = growth_df_display[col].apply(
                                lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
                            )
                        
                        st.dataframe(
                            growth_df_display,
                            use_container_width=True
                        )
                    else:
                        st.warning("Key metrics not available for visualization.")
                else:
                    st.warning("Income statement data not available for this stock.")
            except Exception as e:
                st.error(f"Error loading income statement: {str(e)}")

    # BALANCE SHEET TAB
    with main_tabs[3]:
        st.markdown("""
        <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:20px;">
            <h3 style="margin-top:0; color:#2D3047;">Balance Sheet</h3>
            <p style="color:#71717A; font-size:0.9rem; margin-bottom:0;">
                Financial data shown in {currency} {unit}. Data source: Yahoo Finance.
            </p>
        </div>
        """.format(
            currency="₹" if is_indian else "$",
            unit="Crores" if is_indian else "Millions"
        ), unsafe_allow_html=True)
        
        with st.spinner("Loading balance sheet..."):
            try:
                # Get ticker object
                ticker = yf.Ticker(stock_symbol)
                
                # Get balance sheet data
                balance_sheet = ticker.balance_sheet
                
                if balance_sheet is not None and not balance_sheet.empty:
                    # Format dates
                    if isinstance(balance_sheet.columns, pd.DatetimeIndex):
                        balance_sheet.columns = balance_sheet.columns.strftime('%b %Y')
                    
                    # Convert values to appropriate scale
                    formatted_bs = balance_sheet.copy()
                    
                    for col in formatted_bs.columns:
                        formatted_bs[col] = formatted_bs[col].apply(
                            lambda x: x / 10000000 if is_indian else x / 1000000  # ₹ Crores for Indian, $ Millions for others
                        )
                    
                    # Create a standardized balance sheet format with key metrics
                    bs_items = [
                        "Total Assets",
                        "Total Current Assets",
                        "Cash And Cash Equivalents",
                        "Inventory",
                        "Net Receivables",
                        "Total Non Current Assets",
                        "Property Plant & Equipment",
                        "Investments",
                        "Goodwill",
                        "Total Liabilities",
                        "Total Current Liabilities",
                        "Accounts Payable",
                        "Short Term Debt",
                        "Total Non Current Liabilities",
                        "Long Term Debt",
                        "Total Stockholder Equity",
                        "Retained Earnings",
                        "Common Stock",
                    ]
                    
                    # Create a new DataFrame with our desired metrics
                    bs_data = pd.DataFrame(index=bs_items)
                    
                    # Map Yahoo Finance data to our format
                    mapping = {
                        "Total Assets": ["Total Assets"],
                        "Total Current Assets": ["Total Current Assets"],
                        "Cash And Cash Equivalents": ["Cash And Cash Equivalents", "Cash"],
                        "Inventory": ["Inventory"],
                        "Net Receivables": ["Net Receivables"],
                        "Total Non Current Assets": ["Total Non Current Assets"],
                        "Property Plant & Equipment": ["Property Plant & Equipment", "Net PPE"],
                        "Investments": ["Investments", "Long Term Investments"],
                        "Goodwill": ["Goodwill"], 
                        "Total Liabilities": ["Total Liabilities"],
                        "Total Current Liabilities": ["Total Current Liabilities"],
                        "Accounts Payable": ["Accounts Payable"],
                        "Short Term Debt": ["Short Term Debt"],
                        "Total Non Current Liabilities": ["Total Non Current Liabilities", "Long Term Liabilities"],
                        "Long Term Debt": ["Long Term Debt"],
                        "Total Stockholder Equity": ["Total Stockholder Equity", "Stockholders Equity"],
                        "Retained Earnings": ["Retained Earnings"],
                        "Common Stock": ["Common Stock"]
                    }
                    
                    # Fill in our balance sheet DataFrame
                    for bs_item in bs_items:
                        for possible_key in mapping[bs_item]:
                            if possible_key in formatted_bs.index:
                                bs_data.loc[bs_item] = formatted_bs.loc[possible_key]
                                break
                    
                    # Display the data
                    st.dataframe(
                        bs_data,
                        use_container_width=True,
                        hide_index=False,
                        column_config={col: {"format": "%.2f"} for col in bs_data.columns}
                    )
                    
                    # Display visualization for key metrics
                    st.markdown("### Key Balance Sheet Categories")
                    
                    # Create visualization of asset and liability composition for the most recent period
                    latest_period = bs_data.columns[0]
                    
                    # Asset composition
                    st.markdown(f"#### Asset Composition ({latest_period})")
                    
                    asset_items = {
                        "Cash & Equivalents": bs_data.loc["Cash And Cash Equivalents", latest_period] if "Cash And Cash Equivalents" in bs_data.index else 0,
                        "Receivables": bs_data.loc["Net Receivables", latest_period] if "Net Receivables" in bs_data.index else 0,
                        "Inventory": bs_data.loc["Inventory", latest_period] if "Inventory" in bs_data.index else 0,
                        "Property & Equipment": bs_data.loc["Property Plant & Equipment", latest_period] if "Property Plant & Equipment" in bs_data.index else 0,
                        "Investments": bs_data.loc["Investments", latest_period] if "Investments" in bs_data.index else 0,
                        "Goodwill": bs_data.loc["Goodwill", latest_period] if "Goodwill" in bs_data.index else 0,
                        "Other Assets": bs_data.loc["Total Assets", latest_period] - sum([
                            bs_data.loc["Cash And Cash Equivalents", latest_period] if "Cash And Cash Equivalents" in bs_data.index else 0,
                            bs_data.loc["Net Receivables", latest_period] if "Net Receivables" in bs_data.index else 0,
                            bs_data.loc["Inventory", latest_period] if "Inventory" in bs_data.index else 0,
                            bs_data.loc["Property Plant & Equipment", latest_period] if "Property Plant & Equipment" in bs_data.index else 0,
                            bs_data.loc["Investments", latest_period] if "Investments" in bs_data.index else 0,
                            bs_data.loc["Goodwill", latest_period] if "Goodwill" in bs_data.index else 0
                        ])
                    }
                    
                    # Remove any negative values (can happen due to calculation errors)
                    asset_items = {k: max(0, v) if pd.notna(v) else 0 for k, v in asset_items.items()}
                    
                    # Create pie chart for assets
                    fig_assets = go.Figure(data=[go.Pie(
                        labels=list(asset_items.keys()),
                        values=list(asset_items.values()),
                        hole=.4,
                        marker=dict(colors=['#FF6B1A', '#16C172', '#1B998B', '#2D3047', '#F05D5E', '#E7C7B0', '#5F5AA2'])
                    )])
                    
                    fig_assets.update_layout(
                        title=f"Asset Composition - {latest_period}",
                        height=350,
                        template="plotly_white"
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.plotly_chart(fig_assets, use_container_width=True)
                    
                    # Liability & Equity composition
                    with col2:
                        st.markdown(f"#### Liability & Equity Composition ({latest_period})")
                        
                        liability_equity_items = {
                            "Short Term Debt": bs_data.loc["Short Term Debt", latest_period] if "Short Term Debt" in bs_data.index else 0,
                            "Accounts Payable": bs_data.loc["Accounts Payable", latest_period] if "Accounts Payable" in bs_data.index else 0,
                            "Long Term Debt": bs_data.loc["Long Term Debt", latest_period] if "Long Term Debt" in bs_data.index else 0,
                            "Other Liabilities": bs_data.loc["Total Liabilities", latest_period] - sum([
                                bs_data.loc["Short Term Debt", latest_period] if "Short Term Debt" in bs_data.index else 0,
                                bs_data.loc["Accounts Payable", latest_period] if "Accounts Payable" in bs_data.index else 0,
                                bs_data.loc["Long Term Debt", latest_period] if "Long Term Debt" in bs_data.index else 0
                            ]) if "Total Liabilities" in bs_data.index else 0,
                            "Total Equity": bs_data.loc["Total Stockholder Equity", latest_period] if "Total Stockholder Equity" in bs_data.index else 0
                        }
                        
                        # Remove any negative values
                        liability_equity_items = {k: max(0, v) if pd.notna(v) else 0 for k, v in liability_equity_items.items()}
                        
                        # Create pie chart for liabilities and equity
                        fig_liab_equity = go.Figure(data=[go.Pie(
                            labels=list(liability_equity_items.keys()),
                            values=list(liability_equity_items.values()),
                            hole=.4,
                            marker=dict(colors=['#F05D5E', '#2D3047', '#1B998B', '#FF6B1A', '#16C172'])
                        )])
                        
                        fig_liab_equity.update_layout(
                            title=f"Liability & Equity Composition - {latest_period}",
                            height=350,
                            template="plotly_white"
                        )
                        
                        st.plotly_chart(fig_liab_equity, use_container_width=True)
                else:
                    st.warning("Balance sheet data not available for this stock.")
            except Exception as e:
                st.error(f"Error loading balance sheet: {str(e)}")

    # CASH FLOW TAB
    with main_tabs[4]:
        st.markdown("""
        <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:20px;">
            <h3 style="margin-top:0; color:#2D3047;">Cash Flow Statement</h3>
            <p style="color:#71717A; font-size:0.9rem; margin-bottom:0;">
                Financial data shown in {currency} {unit}. Data source: Yahoo Finance.
            </p>
        </div>
        """.format(
            currency="₹" if is_indian else "$",
            unit="Crores" if is_indian else "Millions"
        ), unsafe_allow_html=True)
        
        with st.spinner("Loading cash flow statement..."):
            try:
                # Get ticker object
                ticker = yf.Ticker(stock_symbol)
                
                # Get cash flow data
                cash_flow = ticker.cashflow
                
                if cash_flow is not None and not cash_flow.empty:
                    # Format dates
                    if isinstance(cash_flow.columns, pd.DatetimeIndex):
                        cash_flow.columns = cash_flow.columns.strftime('%b %Y')
                    
                    # Convert values to appropriate scale
                    formatted_cf = cash_flow.copy()
                    
                    for col in formatted_cf.columns:
                        formatted_cf[col] = formatted_cf[col].apply(
                            lambda x: x / 10000000 if is_indian else x / 1000000  # ₹ Crores for Indian, $ Millions for others
                        )
                    
                    # Create a standardized cash flow format with key metrics
                    cf_items = [
                        "Operating Cash Flow",
                        "Net Income",
                        "Depreciation And Amortization",
                        "Change In Working Capital",
                        "Investing Cash Flow",
                        "Capital Expenditure",
                        "Acquisitions",
                        "Purchase Of Investment",
                        "Sale Of Investment",
                        "Financing Cash Flow",
                        "Dividend Payout",
                        "Stock Repurchase",
                        "Debt Repayment",
                        "Free Cash Flow"
                    ]
                    
                    # Create a new DataFrame with our desired metrics
                    cf_data = pd.DataFrame(index=cf_items)
                    
                    # Map Yahoo Finance data to our format
                    mapping = {
                        "Operating Cash Flow": ["Operating Cash Flow", "Total Cash From Operating Activities"],
                        "Net Income": ["Net Income", "Net Income From Continuing Operations"],
                        "Depreciation And Amortization": ["Depreciation And Amortization", "Depreciation"],
                        "Change In Working Capital": ["Change In Working Capital"],
                        "Investing Cash Flow": ["Investing Cash Flow", "Total Cash From Investing Activities"],
                        "Capital Expenditure": ["Capital Expenditure", "Capital Expenditures"],
                        "Acquisitions": ["Acquisitions", "Acquisitions Net"],
                        "Purchase Of Investment": ["Purchase Of Investment", "Investments In Property Plant And Equipment"],
                        "Sale Of Investment": ["Sale Of Investment", "Sale Of Investment Property"],
                        "Financing Cash Flow": ["Financing Cash Flow", "Total Cash From Financing Activities"],
                        "Dividend Payout": ["Dividend Payout", "Dividends Paid"],
                        "Stock Repurchase": ["Stock Repurchase", "Repurchase Of Stock"],
                        "Debt Repayment": ["Debt Repayment", "Repayments Of Long Term Debt"],
                        "Free Cash Flow": ["Free Cash Flow"]
                    }
                    
                    # Fill in our cash flow DataFrame
                    for cf_item in cf_items:
                        for possible_key in mapping[cf_item]:
                            if possible_key in formatted_cf.index:
                                cf_data.loc[cf_item] = formatted_cf.loc[possible_key]
                                break
                    
                    # Display the data
                    st.dataframe(
                        cf_data,
                        use_container_width=True,
                        hide_index=False,
                        column_config={col: {"format": "%.2f"} for col in cf_data.columns}
                    )
                    
                    # Visualize key cash flow metrics
                    st.markdown("### Cash Flow Trends")
                    
                    key_metrics = [
                        "Operating Cash Flow", 
                        "Investing Cash Flow", 
                        "Financing Cash Flow", 
                        "Free Cash Flow"
                    ]
                    
                    metrics_to_plot = [metric for metric in key_metrics if metric in cf_data.index]
                    
                    if metrics_to_plot:
                        # Prepare data for plotting
                        plot_data = {}
                        for metric in metrics_to_plot:
                            if metric in cf_data.index:
                                plot_data[metric] = cf_data.loc[metric].values
                        
                        if plot_data:
                            # Create figure with dual y-axes
                            fig = go.Figure()
                            
                            # Add bars for each metric
                            for metric, values in plot_data.items():
                                fig.add_trace(go.Bar(
                                    x=cf_data.columns,
                                    y=values,
                                    name=metric
                                ))
                            
                            # Update layout
                            fig.update_layout(
                                title="Cash Flow Trends Over Time",
                                xaxis_title="Reporting Period",
                                yaxis_title=f"Value ({format_utils.format_currency(0, is_indian).strip('0')} {'Crores' if is_indian else 'Millions'})",
                                height=400,
                                template="plotly_white",
                                barmode='group'
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("Cash flow metrics not available for visualization.")
                    
                    # Cash flow composition for the latest period
                    latest_period = cf_data.columns[0]
                    
                    st.markdown(f"### Cash Flow Composition ({latest_period})")
                    
                    try:
                        # Operating cash flow breakdown
                        if "Operating Cash Flow" in cf_data.index:
                            operating_items = {
                                "Net Income": cf_data.loc["Net Income", latest_period] if "Net Income" in cf_data.index else 0,
                                "Depreciation & Amortization": cf_data.loc["Depreciation And Amortization", latest_period] if "Depreciation And Amortization" in cf_data.index else 0,
                                "Working Capital Changes": cf_data.loc["Change In Working Capital", latest_period] if "Change In Working Capital" in cf_data.index else 0,
                                "Other Operating Activities": cf_data.loc["Operating Cash Flow", latest_period] - sum([
                                    cf_data.loc["Net Income", latest_period] if "Net Income" in cf_data.index and pd.notna(cf_data.loc["Net Income", latest_period]) else 0,
                                    cf_data.loc["Depreciation And Amortization", latest_period] if "Depreciation And Amortization" in cf_data.index and pd.notna(cf_data.loc["Depreciation And Amortization", latest_period]) else 0,
                                    cf_data.loc["Change In Working Capital", latest_period] if "Change In Working Capital" in cf_data.index and pd.notna(cf_data.loc["Change In Working Capital", latest_period]) else 0
                                ])
                            }
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### Operating Cash Flow Components")
                                
                                # Remove any negative values for the pie chart
                                operating_items_filtered = {k: v for k, v in operating_items.items() if pd.notna(v) and v > 0}
                                
                                if operating_items_filtered:
                                    fig_operating = go.Figure(data=[go.Pie(
                                        labels=list(operating_items_filtered.keys()),
                                        values=list(operating_items_filtered.values()),
                                        hole=.4,
                                        marker=dict(colors=['#16C172', '#1B998B', '#2D3047', '#FF6B1A'])
                                    )])
                                    
                                    fig_operating.update_layout(
                                        title="Operating Cash Flow Components",
                                        height=350,
                                        template="plotly_white"
                                    )
                                    
                                    st.plotly_chart(fig_operating, use_container_width=True)
                                else:
                                    st.warning("Not enough positive cash flow components to display.")
                            
                            with col2:
                                # Calculate cash flow coverage ratios
                                st.markdown("#### Cash Flow Coverage Ratios")
                                
                                operating_cf = cf_data.loc["Operating Cash Flow", latest_period] if "Operating Cash Flow" in cf_data.index else None
                                capex = abs(cf_data.loc["Capital Expenditure", latest_period]) if "Capital Expenditure" in cf_data.index else None
                                dividend = abs(cf_data.loc["Dividend Payout", latest_period]) if "Dividend Payout" in cf_data.index else None
                                long_term_debt = bs_data.loc["Long Term Debt", latest_period] if "Long Term Debt" in bs_data.index else None
                                
                                coverage_ratios = {}
                                
                                if operating_cf is not None and capex is not None and pd.notna(operating_cf) and pd.notna(capex) and capex != 0:
                                    coverage_ratios["CapEx Coverage Ratio"] = f"{operating_cf / capex:.2f}x"
                                else:
                                    coverage_ratios["CapEx Coverage Ratio"] = "N/A"
                                    
                                if operating_cf is not None and dividend is not None and pd.notna(operating_cf) and pd.notna(dividend) and dividend != 0:
                                    coverage_ratios["Dividend Coverage Ratio"] = f"{operating_cf / dividend:.2f}x"
                                else:
                                    coverage_ratios["Dividend Coverage Ratio"] = "N/A"
                                    
                                if operating_cf is not None and long_term_debt is not None and pd.notna(operating_cf) and pd.notna(long_term_debt) and long_term_debt != 0:
                                    coverage_ratios["Debt Service Coverage"] = f"{operating_cf / (long_term_debt * 0.1):.2f}x"  # Assuming 10% of debt serviced annually
                                else:
                                    coverage_ratios["Debt Service Coverage"] = "N/A"
                                
                                # Display ratios
                                st.markdown("""
                                <div style="background:#f8f9fa; padding:15px; border-radius:10px; margin-bottom:20px;">
                                """, unsafe_allow_html=True)
                                
                                for ratio, value in coverage_ratios.items():
                                    st.markdown(f"""
                                    <div style="display:flex; justify-content:space-between; margin:10px 0;">
                                        <span style="color:#555;">{ratio}</span>
                                        <span style="font-weight:600;">{value}</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                st.markdown("</div>", unsafe_allow_html=True)
                                
                                # Free Cash Flow trend
                                if "Free Cash Flow" in cf_data.index:
                                    st.markdown("#### Free Cash Flow Trend")
                                    
                                    fig_fcf = go.Figure()
                                    
                                    fig_fcf.add_trace(go.Scatter(
                                        x=cf_data.columns,
                                        y=cf_data.loc["Free Cash Flow"],
                                        mode='lines+markers',
                                        name='Free Cash Flow',
                                        line=dict(color='#16C172', width=3),
                                        marker=dict(size=8)
                                    ))
                                    
                                    fig_fcf.update_layout(
                                        title="Free Cash Flow Trend",
                                        xaxis_title="Reporting Period",
                                        yaxis_title=f"FCF ({format_utils.format_currency(0, is_indian).strip('0')} {'Crores' if is_indian else 'Millions'})",
                                        height=150,
                                        margin=dict(l=0, r=0, t=30, b=0),
                                        template="plotly_white"
                                    )
                                    
                                    st.plotly_chart(fig_fcf, use_container_width=True)
                                
                    except Exception as e:
                        st.error(f"Error creating cash flow visualizations: {str(e)}")
                else:
                    st.warning("Cash flow statement data not available for this stock.")
            except Exception as e:
                st.error(f"Error loading cash flow statement: {str(e)}")

    # PEER COMPARISON TAB
    with main_tabs[5]:
        st.markdown("### Peer Comparison")
        
        with st.spinner("Loading peer comparison data..."):
            try:
                # Get peer companies
                peers = get_peer_symbols(stock_symbol, company_sector, is_indian)
                
                # Get comparison data
                comparison_data = get_peer_comparison_data(stock_symbol, peers, is_indian)
                
                if not comparison_data.empty:
                    # Highlight the main stock in the table
                    st.markdown(f"#### {company_name} vs Industry Peers")
                    
                    # Style the dataframe with highlighting for the main stock
                    def highlight_main(x):
                        return ['background-color: #1B998B20; font-weight: bold' if x.name == stock_symbol else '' for i in x]
                    
                    st.dataframe(
                        comparison_data.style.apply(highlight_main, axis=1),
                        use_container_width=True
                    )
                    
                    # Visualize key metrics
                    st.markdown("### Key Metrics Comparison")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # P/E Ratio comparison
                        pe_data = {stock: data['_pe'] for stock, data in comparison_data.reset_index().set_index('Name')['P/E Ratio'].items()}
                        pe_data = {k: v for k, v in pe_data.items() if pd.notna(v)}
                        
                        if pe_data:
                            fig_pe = go.Figure(go.Bar(
                                x=list(pe_data.keys()),
                                y=list(pe_data.values()),
                                marker_color=['#FF6B1A' if stock == comparison_data.loc[stock_symbol, 'Name'] else '#1B998B' for stock in pe_data.keys()]
                            ))
                            
                            fig_pe.update_layout(
                                title="P/E Ratio Comparison",
                                xaxis_title="Company",
                                yaxis_title="P/E Ratio",
                                height=300,
                                template="plotly_white"
                            )
                            
                            st.plotly_chart(fig_pe, use_container_width=True)
                        else:
                            st.warning("P/E ratio data not available for comparison.")
                    
                    with col2:
                        # EPS comparison
                        eps_data = {stock: data['_eps'] for stock, data in comparison_data.reset_index().set_index('Name')['EPS'].items()}
                        eps_data = {k: v for k, v in eps_data.items() if pd.notna(v)}
                        
                        if eps_data:
                            fig_eps = go.Figure(go.Bar(
                                x=list(eps_data.keys()),
                                y=list(eps_data.values()),
                                marker_color=['#FF6B1A' if stock == comparison_data.loc[stock_symbol, 'Name'] else '#1B998B' for stock in eps_data.keys()]
                            ))
                            
                            fig_eps.update_layout(
                                title="EPS Comparison",
                                xaxis_title="Company",
                                yaxis_title=f"EPS ({format_utils.format_currency(0, is_indian).strip('0')})",
                                height=300,
                                template="plotly_white"
                            )
                            
                            st.plotly_chart(fig_eps, use_container_width=True)
                        else:
                            st.warning("EPS data not available for comparison.")
                    
                    # Market Cap Comparison
                    market_cap_data = {stock: data['_market_cap'] for stock, data in comparison_data.reset_index().set_index('Name')['Market Cap'].items()}
                    market_cap_data = {k: v for k, v in market_cap_data.items() if pd.notna(v)}
                    
                    if market_cap_data:
                        fig_mc = go.Figure(go.Bar(
                            x=list(market_cap_data.keys()),
                            y=list(market_cap_data.values()),
                            marker_color=['#FF6B1A' if stock == comparison_data.loc[stock_symbol, 'Name'] else '#1B998B' for stock in market_cap_data.keys()]
                        ))
                        
                        fig_mc.update_layout(
                            title=f"Market Cap Comparison ({format_utils.format_currency(0, is_indian).strip('0')} {'Cr' if is_indian else 'B'})",
                            xaxis_title="Company",
                            yaxis_title=f"Market Cap ({format_utils.format_currency(0, is_indian).strip('0')} {'Cr' if is_indian else 'B'})",
                            height=300,
                            template="plotly_white"
                        )
                        
                        st.plotly_chart(fig_mc, use_container_width=True)
                    else:
                        st.warning("Market cap data not available for comparison.")
                    
                    # Price Performance Comparison
                    st.markdown("### Price Performance Comparison")
                    
                    timeframes = ["1mo", "3mo", "6mo", "1y"]
                    selected_timeframe = st.select_slider("Select timeframe for comparison:", timeframes)
                    
                    with st.spinner(f"Loading {selected_timeframe} performance data..."):
                        # Get historical data for all symbols
                        all_hist_data = {}
                        valid_symbols = []
                        
                        for symbol in [stock_symbol] + peers:
                            try:
                                if is_indian:
                                    hist = indian_markets.get_indian_stock_data(symbol, period=selected_timeframe)
                                else:
                                    hist = yf.download(symbol, period=selected_timeframe)
                                    
                                if not hist.empty:
                                    all_hist_data[symbol] = hist
                                    valid_symbols.append(symbol)
                            except:
                                pass
                        
                        if all_hist_data:
                            # Create normalized chart
                            fig = go.Figure()
                            
                            for symbol in valid_symbols:
                                df = all_hist_data[symbol]
                                normalized = df['Close'] / df['Close'].iloc[0] * 100
                                
                                company_name = stock_symbol
                                if symbol in comparison_data.index:
                                    company_name = comparison_data.loc[symbol, 'Name']
                                
                                fig.add_trace(go.Scatter(
                                    x=df.index,
                                    y=normalized,
                                    name=company_name,
                                    line=dict(width=3 if symbol == stock_symbol else 2)
                                ))
                            
                            fig.update_layout(
                                title=f"Normalized Price Performance ({selected_timeframe})",
                                xaxis_title="Date",
                                yaxis_title="Normalized Price (Base=100)",
                                height=400,
                                template="plotly_white",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Calculate and show returns
                            returns = {}
                            
                            for symbol in valid_symbols:
                                df = all_hist_data[symbol]
                                ret = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
                                
                                company_name = symbol
                                if symbol in comparison_data.index:
                                    company_name = comparison_data.loc[symbol, 'Name']
                                    
                                returns[company_name] = ret
                            
                            # Sort by returns
                            returns = {k: v for k, v in sorted(returns.items(), key=lambda item: item[1], reverse=True)}
                            
                            # Create a DataFrame for returns
                            returns_df = pd.DataFrame(list(returns.items()), columns=['Company', f'Return ({selected_timeframe})'])
                            returns_df[f'Return ({selected_timeframe})'] = returns_df[f'Return ({selected_timeframe})'].apply(
                                lambda x: f"{x:.2f}%"
                            )
                            
                            st.markdown(f"#### Returns Over {selected_timeframe}")
                            st.dataframe(returns_df, use_container_width=True, hide_index=True)
                        else:
                            st.warning("Could not retrieve historical data for peer comparison.")
                else:
                    st.warning("Peer comparison data not available.")
            except Exception as e:
                st.error(f"Error loading peer comparison: {str(e)}")

    # NEWS & ANALYSIS TAB
    with main_tabs[6]:
        st.markdown("### Financial News & Analysis")
        
        with st.spinner("Fetching latest news..."):
            try:
                # Get news articles
                articles = stock_news.get_stock_news(stock_symbol, company_name)
                
                if articles:
                    # Display the news with modern styling
                    for article in articles[:6]:  # Limit to 6 articles
                        with st.container():
                            st.markdown(f"""
                            <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05); margin-bottom:15px;">
                                <h4 style="margin:0 0 5px 0;">{article['title']}</h4>
                                <p style="color:#71717A; font-size:0.8rem; margin:0 0 10px 0;">
                                    {article['source']} | {article['date']}
                                </p>
                                <p style="font-size:0.95rem; margin-bottom:15px;">
                                    {article['summary']}
                                </p>
                                <a href="{article['url']}" target="_blank" style="background:#1B998B; color:white; padding:5px 10px; 
                                    text-decoration:none; border-radius:4px; font-size:0.8rem;">
                                    Read Full Article
                                </a>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("No recent news articles found for this stock.")
            except Exception as e:
                st.error(f"Error fetching news: {str(e)}")
                
        # Sentiment tracker
        st.markdown("### Market Sentiment Tracker")
        
        # Create a simple sentiment tracker for demonstrating interactivity
        sentiment_options = {
            "Very Bullish": "📈 Very Bullish - Expecting significant upward movement",
            "Bullish": "🚀 Bullish - Expecting some upward movement",
            "Neutral": "⚖️ Neutral - No strong directional bias",
            "Bearish": "🔻 Bearish - Expecting some downward movement",
            "Very Bearish": "📉 Very Bearish - Expecting significant downward movement"
        }
        
        selected_sentiment = st.select_slider(
            "What's your sentiment on this stock?",
            options=list(sentiment_options.keys())
        )
        
        st.info(sentiment_options[selected_sentiment])
        
        # Sentiment distribution visualization (dummy data for demo)
        st.markdown("### Community Sentiment Distribution")
        
        sentiment_distribution = {
            "Very Bullish": 25,
            "Bullish": 40,
            "Neutral": 15,
            "Bearish": 12,
            "Very Bearish": 8
        }
        
        fig = go.Figure(go.Bar(
            x=list(sentiment_distribution.keys()),
            y=list(sentiment_distribution.values()),
            marker_color=['#16C172', '#1B998B', '#CCCCCC', '#F05D5E', '#CC0000']
        ))
        
        fig.update_layout(
            title="Community Sentiment Distribution",
            xaxis_title="Sentiment",
            yaxis_title="Number of Votes",
            height=300,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add a notes section
        st.markdown("### Your Analysis Notes")
        
        notes = st.text_area("Add your own analysis notes here:", height=100)
        
        if st.button("Save Notes"):
            st.success("Notes saved successfully!")
            
    # SWOT ANALYSIS TAB
    with main_tabs[7]:
        st.markdown("### SWOT Analysis")
        st.markdown("Strategic analysis of strengths, weaknesses, opportunities, and threats")
        
        # Dynamically generate a basic SWOT based on the sector
        sector = company_info.get('sector', 'General')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Strengths**")
            if sector == "Technology":
                st.write("- Strong innovation pipeline")
                st.write("- Scalable business model")
                st.write("- High gross margins")
            else:
                st.write("- Established market presence")
                st.write("- Diversified revenue streams")
                st.write("- Experienced management team")
        
        with col2:
            st.write("**Weaknesses**")
            if sector == "Technology":
                st.write("- High dependency on specific markets")
                st.write("- Intense competition")
                st.write("- Product lifecycle challenges")
            else:
                st.write("- Market volatility exposure")
                st.write("- Regulatory challenges")
                st.write("- Resource constraints")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Opportunities**")
            if sector == "Technology":
                st.write("- Emerging markets expansion")
                st.write("- New technology adoption")
                st.write("- Strategic partnerships")
            else:
                st.write("- Market expansion potential")
                st.write("- Innovation opportunities")
                st.write("- Strategic acquisition targets")
        
        with col2:
            st.write("**Threats**")
            if sector == "Technology":
                st.write("- Rapid technological changes")
                st.write("- Increasing regulatory scrutiny")
                st.write("- Global economic uncertainties")
            else:
                st.write("- Competitive pressures")
                st.write("- Economic downturn risks")
                st.write("- Supply chain vulnerabilities")

# Add a download button for the data
if not stock_data.empty:
    st.sidebar.markdown("### Download Data")
    csv = stock_data.to_csv().encode('utf-8')
    st.sidebar.download_button(
        label="Download Stock Data (CSV)",
        data=csv,
        file_name=f"{stock_symbol}_data.csv",
        mime="text/csv",
    )

    # Add a button to add to watchlist
    st.sidebar.markdown("### Watchlist Actions")
    if st.sidebar.button(f"Add {stock_symbol} to Watchlist"):
        simple_watchlist.add_to_watchlist(stock_symbol)
        st.sidebar.success(f"{stock_symbol} added to your watchlist!")

# Footer
st.markdown("""
<div style="margin-top:50px; padding:20px; border-top:1px solid #eee; text-align:center; color:#71717A; font-size:0.8rem;">
    MoneyMitra Stock Analysis Dashboard | Data provided by Yahoo Finance | Not financial advice
</div>
""", unsafe_allow_html=True)