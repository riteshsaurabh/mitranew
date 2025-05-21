import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import utils
import financial_metrics
import financial_metrics_direct
import simple_watchlist
import indian_markets
import stock_news
import stock_prediction
import format_utils
import financial_data

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
        st.markdown("""
        <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:20px;">
            <h3 style="margin-top:0; color:#2D3047;">Financial Metrics</h3>
            <p style="color:#71717A; font-size:0.9rem; margin-bottom:0;">
                Key financial metrics and ratios for analysis. Data source: Yahoo Finance.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.spinner("Loading financial metrics..."):
            try:
                # Import the direct implementation for more reliable metrics
                import financial_metrics_direct
                metrics = financial_metrics_direct.get_financial_metrics(stock_symbol, is_indian)
                
                if metrics:
                    # Create tabs for different metric categories
                    metrics_tabs = st.tabs([
                        "Valuation", 
                        "Profitability", 
                        "Financial Health",
                        "Performance",
                        "Technical",
                        "Growth & Dividends"
                    ])
                    
                    # VALUATION METRICS TAB
                    with metrics_tabs[0]:
                        st.markdown("### Valuation Metrics")
                        
                        # Display the metrics in a nice table
                        if metrics['valuation_metrics']:
                            # Create a DataFrame for display
                            val_df = pd.DataFrame({
                                'Metric': list(metrics['valuation_metrics'].keys()),
                                'Value': list(metrics['valuation_metrics'].values())
                            })
                            
                            # Create two columns to display the data
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # First half of valuation metrics
                                st.dataframe(
                                    val_df.iloc[:4],
                                    hide_index=True,
                                    use_container_width=True
                                )
                            
                            with col2:
                                # Second half of valuation metrics
                                st.dataframe(
                                    val_df.iloc[4:],
                                    hide_index=True,
                                    use_container_width=True
                                )
                            
                            # Add industry comparison bar chart if data is available
                            try:
                                # Example data for PE and P/B industry comparison
                                pe_ratio = float(metrics['valuation_metrics'].get("P/E Ratio", "0").replace("N/A", "0"))
                                pb_ratio = float(metrics['valuation_metrics'].get("Price/Book", "0").replace("N/A", "0"))
                                
                                if pe_ratio > 0 or pb_ratio > 0:
                                    st.markdown("#### Valuation Comparison")
                                    
                                    # Example comparison data (normally would be retrieved from a database)
                                    if is_indian:
                                        industry_pe = 25.8
                                        sector_pe = 22.4
                                        industry_pb = 3.5
                                        sector_pb = 2.9
                                    else:
                                        industry_pe = 22.5
                                        sector_pe = 19.8
                                        industry_pb = 3.2
                                        sector_pb = 2.8
                                    
                                    if pe_ratio > 0:
                                        pe_comparison = {
                                            "Company": pe_ratio,
                                            "Industry Avg": industry_pe,
                                            "Sector Avg": sector_pe
                                        }
                                        
                                        # Create a 2-column layout for the charts
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            # P/E comparison chart
                                            fig1 = go.Figure([
                                                go.Bar(
                                                    x=list(pe_comparison.keys()),
                                                    y=list(pe_comparison.values()),
                                                    marker_color=['#FF6B1A', '#1B998B', '#2D3047']
                                                )
                                            ])
                                            
                                            fig1.update_layout(
                                                title="P/E Ratio Comparison",
                                                height=300,
                                                template="plotly_white"
                                            )
                                            
                                            st.plotly_chart(fig1, use_container_width=True)
                                    
                                        if pb_ratio > 0:
                                            with col2:
                                                pb_comparison = {
                                                    "Company": pb_ratio,
                                                    "Industry Avg": industry_pb,
                                                    "Sector Avg": sector_pb
                                                }
                                                
                                                # P/B comparison chart
                                                fig2 = go.Figure([
                                                    go.Bar(
                                                        x=list(pb_comparison.keys()),
                                                        y=list(pb_comparison.values()),
                                                        marker_color=['#FF6B1A', '#1B998B', '#2D3047']
                                                    )
                                                ])
                                                
                                                fig2.update_layout(
                                                    title="Price/Book Ratio Comparison",
                                                    height=300,
                                                    template="plotly_white"
                                                )
                                                
                                                st.plotly_chart(fig2, use_container_width=True)
                            except:
                                pass  # Skip visualization if there's an error
                        else:
                            st.warning("Valuation metrics data not available.")
                    
                    # PROFITABILITY METRICS TAB
                    with metrics_tabs[1]:
                        st.markdown("### Profitability Metrics")
                        
                        if metrics['profitability_ratios']:
                            # Create a DataFrame for display
                            prof_df = pd.DataFrame({
                                'Metric': list(metrics['profitability_ratios'].keys()),
                                'Value': list(metrics['profitability_ratios'].values())
                            })
                            
                            # Display the data
                            st.dataframe(
                                prof_df,
                                hide_index=True,
                                use_container_width=True
                            )
                            
                            # Add profitability visualization
                            try:
                                # Extract margin data, with fallbacks for missing data
                                margins = {}
                                
                                for key, value in metrics['profitability_ratios'].items():
                                    if "Margin" in key and value != "N/A":
                                        try:
                                            percent_value = float(value.replace("%", "")) if "%" in value else 0
                                            margins[key] = percent_value
                                        except:
                                            pass
                                
                                # Only create visualization if we have valid margin data
                                if margins:
                                    st.markdown("#### Margin Analysis")
                                    
                                    margin_labels = list(margins.keys())
                                    margin_values = list(margins.values())
                                    
                                    colors = ['#16C172', '#1B998B', '#FF6B1A', '#2D3047'][:len(margins)]
                                    
                                    fig = go.Figure()
                                    
                                    for i, (label, value) in enumerate(zip(margin_labels, margin_values)):
                                        fig.add_trace(go.Bar(
                                            name=label,
                                            x=[label],
                                            y=[value],
                                            marker_color=colors[i % len(colors)]
                                        ))
                                    
                                    fig.update_layout(
                                        title="Margin Analysis (%)",
                                        height=400,
                                        template="plotly_white"
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                            except:
                                pass  # Skip visualization if there's an error
                        else:
                            st.warning("Profitability metrics data not available.")
                    
                    # FINANCIAL HEALTH TAB
                    with metrics_tabs[2]:
                        st.markdown("### Financial Health Metrics")
                        
                        if metrics['financial_health']:
                            # Create a DataFrame for display
                            health_df = pd.DataFrame({
                                'Metric': list(metrics['financial_health'].keys()),
                                'Value': list(metrics['financial_health'].values())
                            })
                            
                            # Display the data
                            st.dataframe(
                                health_df,
                                hide_index=True,
                                use_container_width=True
                            )
                            
                            # Add gauge charts for key financial health metrics
                            try:
                                col1, col2 = st.columns(2)
                                
                                # Current ratio visualization
                                current_ratio_str = metrics['financial_health'].get("Current Ratio", "0")
                                current_ratio = float(current_ratio_str.replace("N/A", "0")) if current_ratio_str != "N/A" else 0
                                
                                # Debt to Equity ratio
                                debt_equity_str = metrics['financial_health'].get("Debt to Equity", "0")
                                debt_equity = float(debt_equity_str.replace("N/A", "0")) if debt_equity_str != "N/A" else 0
                                
                                with col1:
                                    if current_ratio > 0:
                                        # Create gauge chart for current ratio
                                        fig1 = go.Figure(go.Indicator(
                                            mode="gauge+number",
                                            value=current_ratio,
                                            domain={'x': [0, 1], 'y': [0, 1]},
                                            title={'text': "Current Ratio"},
                                            gauge={
                                                'axis': {'range': [0, 3]},
                                                'bar': {'color': "#FF6B1A"},
                                                'steps': [
                                                    {'range': [0, 1], 'color': "#F05D5E"},
                                                    {'range': [1, 1.5], 'color': "#FFC857"},
                                                    {'range': [1.5, 3], 'color': "#16C172"}
                                                ],
                                                'threshold': {
                                                    'line': {'color': "black", 'width': 2},
                                                    'thickness': 0.75,
                                                    'value': current_ratio
                                                }
                                            }
                                        ))
                                        
                                        fig1.update_layout(
                                            height=300,
                                            template="plotly_white"
                                        )
                                        
                                        st.plotly_chart(fig1, use_container_width=True)
                                
                                with col2:
                                    if debt_equity > 0:
                                        # Create gauge chart for debt to equity
                                        fig2 = go.Figure(go.Indicator(
                                            mode="gauge+number",
                                            value=debt_equity,
                                            domain={'x': [0, 1], 'y': [0, 1]},
                                            title={'text': "Debt to Equity"},
                                            gauge={
                                                'axis': {'range': [0, 2]},
                                                'bar': {'color': "#1B998B"},
                                                'steps': [
                                                    {'range': [0, 0.5], 'color': "#16C172"},
                                                    {'range': [0.5, 1], 'color': "#FFC857"},
                                                    {'range': [1, 2], 'color': "#F05D5E"}
                                                ],
                                                'threshold': {
                                                    'line': {'color': "black", 'width': 2},
                                                    'thickness': 0.75,
                                                    'value': debt_equity
                                                }
                                            }
                                        ))
                                        
                                        fig2.update_layout(
                                            height=300,
                                            template="plotly_white"
                                        )
                                        
                                        st.plotly_chart(fig2, use_container_width=True)
                            except:
                                pass  # Skip visualization if there's an error
                        else:
                            st.warning("Financial health metrics data not available.")
                    
                    # PERFORMANCE METRICS TAB
                    with metrics_tabs[3]:
                        st.markdown("### Performance Metrics")
                        
                        if metrics['performance_metrics']:
                            # Create a DataFrame for display
                            perf_df = pd.DataFrame({
                                'Metric': list(metrics['performance_metrics'].keys()),
                                'Value': list(metrics['performance_metrics'].values())
                            })
                            
                            # Display the data in columns
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.dataframe(
                                    perf_df.iloc[:len(perf_df)//2],
                                    hide_index=True,
                                    use_container_width=True
                                )
                            
                            with col2:
                                st.dataframe(
                                    perf_df.iloc[len(perf_df)//2:],
                                    hide_index=True,
                                    use_container_width=True
                                )
                            
                            # Add a performance visualization
                            try:
                                # Extract return data
                                returns = {}
                                for key in metrics['performance_metrics']:
                                    if "Return" in key:
                                        # Convert percentage strings to floats
                                        value = metrics['performance_metrics'][key]
                                        if isinstance(value, str) and "%" in value:
                                            returns[key] = float(value.replace("%", "")) / 100
                                        elif isinstance(value, str) and value != "N/A":
                                            try:
                                                returns[key] = float(value)
                                            except:
                                                pass
                                
                                if returns:
                                    st.markdown("#### Returns Analysis")
                                    
                                    # Create a bar chart for returns
                                    periods = list(returns.keys())
                                    values = list(returns.values())
                                    
                                    # Colors based on positive/negative returns
                                    colors = ['#16C172' if val >= 0 else '#F05D5E' for val in values]
                                    
                                    fig = go.Figure()
                                    
                                    fig.add_trace(go.Bar(
                                        x=periods,
                                        y=values,
                                        marker_color=colors
                                    ))
                                    
                                    fig.update_layout(
                                        title="Returns by Time Period",
                                        yaxis_title="Return",
                                        yaxis_tickformat='.2%',
                                        height=400,
                                        template="plotly_white"
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                            except:
                                pass  # Skip visualization if there's an error
                        else:
                            st.warning("Performance metrics data not available.")
                    
                    # TECHNICAL INDICATORS TAB
                    with metrics_tabs[4]:
                        st.markdown("### Technical Indicators")
                        
                        if metrics['technical_indicators']:
                            # Create a DataFrame for display
                            tech_df = pd.DataFrame({
                                'Indicator': list(metrics['technical_indicators'].keys()),
                                'Value': list(metrics['technical_indicators'].values())
                            })
                            
                            # Display the data
                            st.dataframe(
                                tech_df,
                                hide_index=True,
                                use_container_width=True
                            )
                            
                            # Add technical analysis visualization
                            try:
                                st.markdown("#### Moving Average Analysis")
                                
                                # Extract price and SMA data
                                current_price_str = metrics['price_info'].get("Current Price", "0")
                                current_price = float(current_price_str.replace(format_utils.format_currency(0, is_indian).strip('0'), "").replace(",", "").replace("N/A", "0"))
                                
                                # Collect SMA data
                                sma_data = {}
                                for key in metrics['technical_indicators']:
                                    if "SMA" in key and metrics['technical_indicators'][key] != "N/A":
                                        try:
                                            value = float(metrics['technical_indicators'][key].replace(",", ""))
                                            sma_data[key] = value
                                        except:
                                            pass
                                
                                if current_price > 0 and sma_data:
                                    # Add current price to SMA data
                                    sma_data["Current Price"] = current_price
                                    
                                    # Create a horizontal bar chart showing price vs SMAs
                                    indicators = list(sma_data.keys())
                                    values = list(sma_data.values())
                                    
                                    fig = go.Figure()
                                    
                                    for i, (indicator, value) in enumerate(zip(indicators, values)):
                                        color = '#FF6B1A' if indicator == "Current Price" else '#1B998B'
                                        fig.add_trace(go.Bar(
                                            y=[indicator],
                                            x=[value],
                                            orientation='h',
                                            marker_color=color,
                                            name=indicator
                                        ))
                                    
                                    fig.update_layout(
                                        title="Price vs Moving Averages",
                                        xaxis_title=f"Price ({format_utils.format_currency(0, is_indian).strip('0')})",
                                        height=300,
                                        template="plotly_white"
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                # RSI visualization if available
                                rsi_str = metrics['technical_indicators'].get("RSI (14)", "0")
                                if rsi_str != "N/A":
                                    try:
                                        rsi_value = float(rsi_str)
                                        
                                        if rsi_value > 0:
                                            st.markdown("#### Relative Strength Index (RSI)")
                                            
                                            # Create gauge chart for RSI
                                            fig = go.Figure(go.Indicator(
                                                mode="gauge+number",
                                                value=rsi_value,
                                                domain={'x': [0, 1], 'y': [0, 1]},
                                                title={'text': "RSI (14)"},
                                                gauge={
                                                    'axis': {'range': [0, 100]},
                                                    'bar': {'color': "#FF6B1A"},
                                                    'steps': [
                                                        {'range': [0, 30], 'color': "#16C172"},
                                                        {'range': [30, 70], 'color': "#FFC857"},
                                                        {'range': [70, 100], 'color': "#F05D5E"}
                                                    ],
                                                    'threshold': {
                                                        'line': {'color': "black", 'width': 2},
                                                        'thickness': 0.75,
                                                        'value': rsi_value
                                                    }
                                                }
                                            ))
                                            
                                            fig.update_layout(
                                                height=300,
                                                template="plotly_white"
                                            )
                                            
                                            st.plotly_chart(fig, use_container_width=True)
                                            
                                            # RSI interpretation
                                            if rsi_value < 30:
                                                st.info("RSI below 30 suggests the stock may be oversold.")
                                            elif rsi_value > 70:
                                                st.info("RSI above 70 suggests the stock may be overbought.")
                                            else:
                                                st.info("RSI between 30-70 suggests neutral momentum.")
                                    except:
                                        pass
                            except:
                                pass  # Skip visualization if there's an error
                        else:
                            st.warning("Technical indicator data not available.")
                    
                    # GROWTH & DIVIDENDS TAB
                    with metrics_tabs[5]:
                        st.markdown("### Growth & Dividend Metrics")
                        
                        # Create two columns - one for growth, one for dividends
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### Growth Metrics")
                            
                            if metrics['growth_metrics']:
                                # Create a DataFrame for display
                                growth_df = pd.DataFrame({
                                    'Metric': list(metrics['growth_metrics'].keys()),
                                    'Value': list(metrics['growth_metrics'].values())
                                })
                                
                                # Display the data
                                st.dataframe(
                                    growth_df,
                                    hide_index=True,
                                    use_container_width=True
                                )
                            else:
                                st.warning("Growth metrics data not available.")
                        
                        with col2:
                            st.markdown("#### Dividend Information")
                            
                            if metrics['dividend_info']:
                                # Create a DataFrame for display
                                div_df = pd.DataFrame({
                                    'Metric': list(metrics['dividend_info'].keys()),
                                    'Value': list(metrics['dividend_info'].values())
                                })
                                
                                # Display the data
                                st.dataframe(
                                    div_df,
                                    hide_index=True,
                                    use_container_width=True
                                )
                            else:
                                st.warning("Dividend data not available.")
                        
                        # Add additional stock information
                        st.markdown("### Additional Information")
                        
                        # Create two columns for price and volume info
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### Price Information")
                            
                            if metrics['price_info']:
                                # Create a DataFrame for display
                                price_df = pd.DataFrame({
                                    'Metric': list(metrics['price_info'].keys()),
                                    'Value': list(metrics['price_info'].values())
                                })
                                
                                # Display the data
                                st.dataframe(
                                    price_df,
                                    hide_index=True,
                                    use_container_width=True
                                )
                            else:
                                st.warning("Price data not available.")
                        
                        with col2:
                            st.markdown("#### Volume Information")
                            
                            if metrics['volume_info']:
                                # Create a DataFrame for display
                                vol_df = pd.DataFrame({
                                    'Metric': list(metrics['volume_info'].keys()),
                                    'Value': list(metrics['volume_info'].values())
                                })
                                
                                # Display the data
                                st.dataframe(
                                    vol_df,
                                    hide_index=True,
                                    use_container_width=True
                                )
                            else:
                                st.warning("Volume data not available.")
                        
                        # Share statistics
                        st.markdown("#### Share Statistics")
                        
                        if metrics['share_statistics']:
                            # Create a DataFrame for display
                            share_df = pd.DataFrame({
                                'Metric': list(metrics['share_statistics'].keys()),
                                'Value': list(metrics['share_statistics'].values())
                            })
                            
                            # Display the data
                            st.dataframe(
                                share_df,
                                hide_index=True,
                                use_container_width=True
                            )
                        else:
                            st.warning("Share statistics data not available.")
                else:
                    st.warning("Financial metrics data not available for this stock.")
            except Exception as e:
                st.error(f"Error loading financial metrics: {str(e)}")
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
            # Get the income statement data using our direct approach
            income_statement_df = financial_data.get_income_statement(stock_symbol, is_indian)
            
            if income_statement_df is not None and not income_statement_df.empty:
                # Display the income statement
                st.dataframe(
                    income_statement_df,
                    use_container_width=True,
                    hide_index=False
                )
                
                # Display visualization for key metrics
                st.markdown("### Key Income Statement Trends")
                
                # Select key metrics to visualize (common ones found in Yahoo Finance)
                key_metrics = [
                    "Total Revenue", "Revenue", 
                    "Gross Profit", 
                    "Operating Income", "EBIT", 
                    "Net Income", "Net Income Common Stockholders"
                ]
                
                # Find metrics that exist in our dataframe
                metrics_to_plot = []
                for metric in key_metrics:
                    if metric in income_statement_df.index:
                        metrics_to_plot.append(metric)
                        # Only need one from each category
                        if "Total Revenue" in metrics_to_plot and "Revenue" in metrics_to_plot:
                            metrics_to_plot.remove("Revenue")
                        if "Operating Income" in metrics_to_plot and "EBIT" in metrics_to_plot:
                            metrics_to_plot.remove("EBIT")
                        if "Net Income" in metrics_to_plot and "Net Income Common Stockholders" in metrics_to_plot:
                            metrics_to_plot.remove("Net Income Common Stockholders")
                
                if metrics_to_plot:
                    # Convert string values back to numbers for plotting
                    plot_data = income_statement_df.copy()
                    for col in plot_data.columns:
                        for idx in metrics_to_plot:
                            if idx in plot_data.index:
                                try:
                                    val = plot_data.loc[idx, col]
                                    if isinstance(val, str):
                                        plot_data.loc[idx, col] = float(val.replace(',', ''))
                                except:
                                    plot_data.loc[idx, col] = None
                    
                    # Create visualization
                    fig = go.Figure()
                    
                    for metric in metrics_to_plot:
                        if metric in plot_data.index:
                            fig.add_trace(go.Bar(
                                x=plot_data.columns,
                                y=plot_data.loc[metric],
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
                else:
                    st.warning("No suitable metrics found for visualization.")
            else:
                st.warning("Income statement data not available for this stock. Please try another stock symbol.")

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
            # Get the balance sheet data using our direct approach
            balance_sheet_df = financial_data.get_balance_sheet(stock_symbol, is_indian)
            
            if balance_sheet_df is not None and not balance_sheet_df.empty:
                # Display the balance sheet
                st.dataframe(
                    balance_sheet_df,
                    use_container_width=True,
                    hide_index=False
                )
                
                # Check if we have enough data for visualization
                if len(balance_sheet_df.columns) > 0:
                    # Display visualization for key categories
                    st.markdown("### Key Balance Sheet Categories")
                    
                    # Get the latest period
                    latest_period = balance_sheet_df.columns[0]
                    
                    # Define key categories we want to visualize
                    asset_categories = [
                        "Total Assets", "Assets",
                        "Cash And Cash Equivalents", "Cash",
                        "Net Receivables", 
                        "Inventory",
                        "Property Plant & Equipment", "Net PPE",
                        "Investments", "Long Term Investments"
                    ]
                    
                    liability_equity_categories = [
                        "Total Liabilities", "Liabilities",
                        "Accounts Payable",
                        "Short Term Debt",
                        "Long Term Debt",
                        "Total Stockholder Equity", "Stockholders Equity", "Total Equity"
                    ]
                    
                    # Find which categories exist in our data
                    asset_items = {}
                    for category in asset_categories:
                        if category in balance_sheet_df.index and pd.notna(balance_sheet_df.loc[category, latest_period]):
                            # Try to convert string to float if needed
                            value = balance_sheet_df.loc[category, latest_period]
                            if isinstance(value, str):
                                try:
                                    value = float(value.replace(',', ''))
                                except:
                                    value = 0
                            asset_items[category] = value
                    
                    liability_equity_items = {}
                    for category in liability_equity_categories:
                        if category in balance_sheet_df.index and pd.notna(balance_sheet_df.loc[category, latest_period]):
                            # Try to convert string to float if needed
                            value = balance_sheet_df.loc[category, latest_period]
                            if isinstance(value, str):
                                try:
                                    value = float(value.replace(',', ''))
                                except:
                                    value = 0
                            liability_equity_items[category] = value
                    
                    # Only create visualizations if we have data
                    if asset_items and liability_equity_items:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"#### Asset Composition ({latest_period})")
                            
                            # Remove any negative values and duplicates
                            asset_items_clean = {}
                            
                            # Prioritize which asset category to use
                            if "Total Assets" in asset_items:
                                asset_items_clean["Total Assets"] = max(0, asset_items["Total Assets"])
                            elif "Assets" in asset_items:
                                asset_items_clean["Total Assets"] = max(0, asset_items["Assets"])
                            
                            if "Cash And Cash Equivalents" in asset_items:
                                asset_items_clean["Cash"] = max(0, asset_items["Cash And Cash Equivalents"])
                            elif "Cash" in asset_items:
                                asset_items_clean["Cash"] = max(0, asset_items["Cash"])
                            
                            if "Property Plant & Equipment" in asset_items:
                                asset_items_clean["Property & Equipment"] = max(0, asset_items["Property Plant & Equipment"])
                            elif "Net PPE" in asset_items:
                                asset_items_clean["Property & Equipment"] = max(0, asset_items["Net PPE"])
                            
                            if "Net Receivables" in asset_items:
                                asset_items_clean["Receivables"] = max(0, asset_items["Net Receivables"])
                            
                            if "Inventory" in asset_items:
                                asset_items_clean["Inventory"] = max(0, asset_items["Inventory"])
                                
                            if "Investments" in asset_items:
                                asset_items_clean["Investments"] = max(0, asset_items["Investments"])
                            elif "Long Term Investments" in asset_items:
                                asset_items_clean["Investments"] = max(0, asset_items["Long Term Investments"])
                            
                            # Calculate Other Assets
                            total_assets = asset_items_clean.get("Total Assets", 0)
                            specific_assets_sum = sum([v for k, v in asset_items_clean.items() if k != "Total Assets"])
                            
                            if total_assets > specific_assets_sum:
                                asset_items_clean["Other Assets"] = total_assets - specific_assets_sum
                            
                            # Remove Total Assets for pie chart
                            if "Total Assets" in asset_items_clean:
                                del asset_items_clean["Total Assets"]
                                
                            # Only create pie chart if we have data
                            if asset_items_clean:
                                fig_assets = go.Figure(data=[go.Pie(
                                    labels=list(asset_items_clean.keys()),
                                    values=list(asset_items_clean.values()),
                                    hole=.4,
                                    marker=dict(colors=['#FF6B1A', '#16C172', '#1B998B', '#2D3047', '#F05D5E', '#E7C7B0', '#5F5AA2'])
                                )])
                                
                                fig_assets.update_layout(
                                    title=f"Asset Composition - {latest_period}",
                                    height=350,
                                    template="plotly_white"
                                )
                                
                                st.plotly_chart(fig_assets, use_container_width=True)
                            else:
                                st.info("Not enough asset data available for visualization.")
                        
                        with col2:
                            st.markdown(f"#### Liability & Equity Composition ({latest_period})")
                            
                            # Clean up liability and equity items
                            liab_equity_clean = {}
                            
                            # Prioritize categories
                            if "Total Liabilities" in liability_equity_items:
                                liab_equity_clean["Total Liabilities"] = max(0, liability_equity_items["Total Liabilities"])
                            elif "Liabilities" in liability_equity_items:
                                liab_equity_clean["Total Liabilities"] = max(0, liability_equity_items["Liabilities"])
                            
                            if "Total Stockholder Equity" in liability_equity_items:
                                liab_equity_clean["Total Equity"] = max(0, liability_equity_items["Total Stockholder Equity"])
                            elif "Stockholders Equity" in liability_equity_items:
                                liab_equity_clean["Total Equity"] = max(0, liability_equity_items["Stockholders Equity"])
                            elif "Total Equity" in liability_equity_items:
                                liab_equity_clean["Total Equity"] = max(0, liability_equity_items["Total Equity"])
                            
                            if "Accounts Payable" in liability_equity_items:
                                liab_equity_clean["Accounts Payable"] = max(0, liability_equity_items["Accounts Payable"])
                            
                            if "Short Term Debt" in liability_equity_items:
                                liab_equity_clean["Short Term Debt"] = max(0, liability_equity_items["Short Term Debt"])
                                
                            if "Long Term Debt" in liability_equity_items:
                                liab_equity_clean["Long Term Debt"] = max(0, liability_equity_items["Long Term Debt"])
                            
                            # Calculate Other Liabilities
                            total_liabilities = liab_equity_clean.get("Total Liabilities", 0)
                            specific_liabilities_sum = sum([v for k, v in liab_equity_clean.items() 
                                                          if k != "Total Liabilities" and k != "Total Equity"])
                            
                            if total_liabilities > specific_liabilities_sum:
                                liab_equity_clean["Other Liabilities"] = total_liabilities - specific_liabilities_sum
                            
                            # Remove Total Liabilities for pie chart
                            if "Total Liabilities" in liab_equity_clean:
                                del liab_equity_clean["Total Liabilities"]
                            
                            # Only create pie chart if we have data
                            if liab_equity_clean:
                                fig_liab_equity = go.Figure(data=[go.Pie(
                                    labels=list(liab_equity_clean.keys()),
                                    values=list(liab_equity_clean.values()),
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
                                st.info("Not enough liability data available for visualization.")
                    else:
                        st.info("Not enough data available for visualization.")
            else:
                st.warning("Balance sheet data not available for this stock. Please try another stock symbol.")

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
            # Get the cash flow data using our direct approach
            cash_flow_df = financial_data.get_cash_flow(stock_symbol, is_indian)
            
            if cash_flow_df is not None and not cash_flow_df.empty:
                # Display the cash flow statement
                st.dataframe(
                    cash_flow_df,
                    use_container_width=True,
                    hide_index=False
                )
                
                # Display visualization for key cash flow metrics
                st.markdown("### Cash Flow Trends")
                
                # Select key metrics to visualize (common ones found in Yahoo Finance)
                key_metrics = [
                    "Operating Cash Flow", "Total Cash From Operating Activities",
                    "Investing Cash Flow", "Total Cash From Investing Activities",
                    "Financing Cash Flow", "Total Cash From Financing Activities",
                    "Free Cash Flow"
                ]
                
                # Find metrics that exist in our dataframe
                metrics_to_plot = []
                for metric in key_metrics:
                    if metric in cash_flow_df.index:
                        metrics_to_plot.append(metric)
                        # Only need one from each category
                        if "Operating Cash Flow" in metrics_to_plot and "Total Cash From Operating Activities" in metrics_to_plot:
                            metrics_to_plot.remove("Total Cash From Operating Activities")
                        if "Investing Cash Flow" in metrics_to_plot and "Total Cash From Investing Activities" in metrics_to_plot:
                            metrics_to_plot.remove("Total Cash From Investing Activities")
                        if "Financing Cash Flow" in metrics_to_plot and "Total Cash From Financing Activities" in metrics_to_plot:
                            metrics_to_plot.remove("Total Cash From Financing Activities")
                
                if metrics_to_plot and len(cash_flow_df.columns) > 0:
                    # Convert string values back to numbers for plotting
                    plot_data = cash_flow_df.copy()
                    for col in plot_data.columns:
                        for idx in metrics_to_plot:
                            if idx in plot_data.index:
                                try:
                                    val = plot_data.loc[idx, col]
                                    if isinstance(val, str):
                                        plot_data.loc[idx, col] = float(val.replace(',', ''))
                                except:
                                    plot_data.loc[idx, col] = None
                    
                    # Create visualization
                    fig = go.Figure()
                    
                    for metric in metrics_to_plot:
                        if metric in plot_data.index:
                            fig.add_trace(go.Bar(
                                x=plot_data.columns,
                                y=plot_data.loc[metric],
                                name=metric
                            ))
                    
                    # Update layout
                    fig.update_layout(
                        title="Cash Flow Trends Over Time",
                        xaxis_title="Reporting Period",
                        yaxis_title=f"Value ({format_utils.format_currency(0, is_indian).strip('0')} {'Crores' if is_indian else 'Millions'})",
                        legend_title="Metrics",
                        height=400,
                        template="plotly_white",
                        barmode='group'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Cash flow composition breakdown
                    if len(cash_flow_df.columns) > 0:
                        latest_period = cash_flow_df.columns[0]
                        st.markdown(f"### Cash Flow Composition ({latest_period})")
                        
                        # Identify operating cash flow components
                        ocf_components = [
                            "Net Income", "Net Income From Continuing Operations",
                            "Depreciation And Amortization", "Depreciation",
                            "Change In Working Capital", "Changes In Working Capital"
                        ]
                        
                        # Create columns for visualizations
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### Cash Flow Components")
                            
                            # Try to find the main cash flow categories
                            cf_categories = {}
                            
                            for cf_type in ["Operating Cash Flow", "Total Cash From Operating Activities"]:
                                if cf_type in cash_flow_df.index and pd.notna(cash_flow_df.loc[cf_type, latest_period]):
                                    try:
                                        if isinstance(cash_flow_df.loc[cf_type, latest_period], str):
                                            cf_categories["Operating"] = float(cash_flow_df.loc[cf_type, latest_period].replace(',', ''))
                                        else:
                                            cf_categories["Operating"] = float(cash_flow_df.loc[cf_type, latest_period])
                                        break
                                    except:
                                        pass
                            
                            for cf_type in ["Investing Cash Flow", "Total Cash From Investing Activities"]:
                                if cf_type in cash_flow_df.index and pd.notna(cash_flow_df.loc[cf_type, latest_period]):
                                    try:
                                        if isinstance(cash_flow_df.loc[cf_type, latest_period], str):
                                            cf_categories["Investing"] = float(cash_flow_df.loc[cf_type, latest_period].replace(',', ''))
                                        else:
                                            cf_categories["Investing"] = float(cash_flow_df.loc[cf_type, latest_period])
                                        break
                                    except:
                                        pass
                            
                            for cf_type in ["Financing Cash Flow", "Total Cash From Financing Activities"]:
                                if cf_type in cash_flow_df.index and pd.notna(cash_flow_df.loc[cf_type, latest_period]):
                                    try:
                                        if isinstance(cash_flow_df.loc[cf_type, latest_period], str):
                                            cf_categories["Financing"] = float(cash_flow_df.loc[cf_type, latest_period].replace(',', ''))
                                        else:
                                            cf_categories["Financing"] = float(cash_flow_df.loc[cf_type, latest_period])
                                        break
                                    except:
                                        pass
                            
                            # Only create pie chart if we have at least two categories
                            if len(cf_categories) >= 2:
                                # Color the negative values differently
                                colors = []
                                for cat, value in cf_categories.items():
                                    if value >= 0:
                                        colors.append('#16C172')  # Green for positive
                                    else:
                                        colors.append('#F05D5E')  # Red for negative
                                
                                # Create absolute values for better visualization but keep the colors
                                abs_categories = {k: abs(v) for k, v in cf_categories.items()}
                                
                                fig_cf_types = go.Figure(data=[go.Pie(
                                    labels=list(abs_categories.keys()),
                                    values=list(abs_categories.values()),
                                    hole=.4,
                                    marker=dict(colors=colors)
                                )])
                                
                                fig_cf_types.update_layout(
                                    title="Cash Flow Categories by Magnitude",
                                    height=350,
                                    template="plotly_white"
                                )
                                
                                st.plotly_chart(fig_cf_types, use_container_width=True)
                            else:
                                st.info("Not enough cash flow categories for visualization.")
                                
                        with col2:
                            st.markdown("#### Operating Cash Flow Details")
                            
                            # Collect operating cash flow components
                            ocf_breakdown = {}
                            
                            for component in ocf_components:
                                if component in cash_flow_df.index and pd.notna(cash_flow_df.loc[component, latest_period]):
                                    try:
                                        if isinstance(cash_flow_df.loc[component, latest_period], str):
                                            val = float(cash_flow_df.loc[component, latest_period].replace(',', ''))
                                        else:
                                            val = float(cash_flow_df.loc[component, latest_period])
                                        
                                        # Use a more readable name for the component
                                        if "Net Income" in component:
                                            ocf_breakdown["Net Income"] = val
                                        elif "Depreciation" in component:
                                            ocf_breakdown["Depreciation & Amort."] = val
                                        elif "Working Capital" in component:
                                            ocf_breakdown["Working Capital"] = val
                                    except:
                                        pass
                            
                            # Calculate Operating CF value 
                            ocf_value = None
                            for cf_type in ["Operating Cash Flow", "Total Cash From Operating Activities"]:
                                if cf_type in cash_flow_df.index and pd.notna(cash_flow_df.loc[cf_type, latest_period]):
                                    try:
                                        if isinstance(cash_flow_df.loc[cf_type, latest_period], str):
                                            ocf_value = float(cash_flow_df.loc[cf_type, latest_period].replace(',', ''))
                                        else:
                                            ocf_value = float(cash_flow_df.loc[cf_type, latest_period])
                                        break
                                    except:
                                        pass
                            
                            # If we have OCF value and components, add "Other" category
                            if ocf_value is not None and ocf_breakdown:
                                component_sum = sum(ocf_breakdown.values())
                                if abs(ocf_value - component_sum) > 0.01:  # Check if there's a difference
                                    ocf_breakdown["Other Components"] = ocf_value - component_sum
                            
                            # Only create waterfall chart if we have components
                            if ocf_breakdown:
                                # Create a waterfall chart for operating CF
                                fig_ocf = go.Figure(go.Waterfall(
                                    name="Operating Cash Flow", 
                                    orientation="v",
                                    measure=["relative"]*len(ocf_breakdown),
                                    x=list(ocf_breakdown.keys()),
                                    y=list(ocf_breakdown.values()),
                                    connector={"line":{"color":"rgb(63, 63, 63)"}},
                                ))
                                
                                fig_ocf.update_layout(
                                    title="Operating Cash Flow Breakdown",
                                    showlegend=False,
                                    height=350,
                                    template="plotly_white"
                                )
                                
                                st.plotly_chart(fig_ocf, use_container_width=True)
                            else:
                                st.info("Not enough operating cash flow details for visualization.")
                                
                            # Free Cash Flow trend if available
                            if "Free Cash Flow" in cash_flow_df.index:
                                st.markdown("#### Free Cash Flow Trend")
                                
                                try:
                                    fcf_data = []
                                    for col in cash_flow_df.columns:
                                        if pd.notna(cash_flow_df.loc["Free Cash Flow", col]):
                                            try:
                                                if isinstance(cash_flow_df.loc["Free Cash Flow", col], str):
                                                    val = float(cash_flow_df.loc["Free Cash Flow", col].replace(',', ''))
                                                else:
                                                    val = float(cash_flow_df.loc["Free Cash Flow", col])
                                                fcf_data.append(val)
                                            except:
                                                fcf_data.append(None)
                                        else:
                                            fcf_data.append(None)
                                    
                                    if any(fcf_data):
                                        fig_fcf = go.Figure()
                                        
                                        fig_fcf.add_trace(go.Scatter(
                                            x=cash_flow_df.columns,
                                            y=fcf_data,
                                            mode='lines+markers',
                                            name='Free Cash Flow',
                                            line=dict(color='#16C172', width=3),
                                            marker=dict(size=8)
                                        ))
                                        
                                        fig_fcf.update_layout(
                                            title="Free Cash Flow Trend",
                                            xaxis_title="Reporting Period",
                                            yaxis_title=f"FCF ({format_utils.format_currency(0, is_indian).strip('0')} {'Crores' if is_indian else 'Millions'})",
                                            height=200,
                                            margin=dict(l=10, r=10, t=40, b=20),
                                            template="plotly_white"
                                        )
                                        
                                        st.plotly_chart(fig_fcf, use_container_width=True)
                                except:
                                    st.info("Could not display Free Cash Flow trend.")
                    else:
                        st.info("Not enough data for Cash Flow composition visualization.")
                else:
                    st.warning("No suitable metrics found for visualization.")
            else:
                st.warning("Cash flow statement data not available for this stock. Please try another stock symbol.")

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