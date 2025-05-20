# Set page configuration - must be the first Streamlit command
import streamlit as st
st.set_page_config(
    page_title="MoneyMitra - Your Financial Mitra",
    page_icon="💰",
    layout="centered",  # Using centered layout for medium mode
    initial_sidebar_state="expanded",
)

# Then import other libraries
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
import sentiment_tracker

# Load custom CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

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
    # Define peer stocks for different sectors (focusing on Indian markets)
    peers = {
        "Technology": ["INFY.NS", "TECHM.NS", "WIPRO.NS", "HCLTECH.NS"],  # Fixed TCS to TECHM
        "Financial Services": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS"],
        "Consumer Goods": ["HINDUNILVR.NS", "ITC.NS", "DABUR.NS", "MARICO.NS"],
        "Automotive": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "HEROMOTOCO.NS"],
        "Pharmaceuticals": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS"],
        "Energy": ["RELIANCE.NS", "ONGC.NS", "IOC.NS", "BPCL.NS"],
        "Manufacturing": ["LT.NS", "ADANIENT.NS", "SIEMENS.NS", "ABB.NS"]
    }
    
    # Handle US stocks (simplified example with popular tickers in each sector)
    us_peers = {
        "Technology": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
        "Financial Services": ["JPM", "BAC", "C", "WFC", "GS"],
        "Healthcare": ["JNJ", "PFE", "MRK", "ABBV", "UNH"],
        "Consumer Goods": ["PG", "KO", "PEP", "WMT", "COST"],
        "Energy": ["XOM", "CVX", "COP", "EOG", "SLB"]
    }
    
    if is_indian:
        # For Indian stocks
        if sector in peers:
            # Return only peers that are not the current stock
            return [peer for peer in peers[sector] if peer != symbol]
        else:
            # Return default Indian peers if sector not found
            return ["RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "TCS.NS", "HINDUNILVR.NS"]
    else:
        # For US stocks
        if sector in us_peers:
            return [peer for peer in us_peers[sector] if peer != symbol]
        else:
            # Return default US peers if sector not found
            return ["AAPL", "MSFT", "AMZN", "GOOGL", "JPM"]

# Page configuration
st.set_page_config(
    page_title="MoneyMitra - Smart Finance",
    page_icon="📈",
    layout="wide"
)

# Initialize session state for watchlist integration
if 'selected_stock' not in st.session_state:
    st.session_state['selected_stock'] = None

# Load custom CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Modern futuristic title and description
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="font-size: 3rem; font-weight: 800; background: linear-gradient(90deg, #FF6B1A, #FF3864); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
               text-transform: uppercase; letter-spacing: -0.05em; margin-bottom: 0.5rem;">
        MoneyMitra
    </h1>
    <p style="font-size: 1.2rem; color: #2D3047; font-weight: 400; max-width: 800px; margin: 0 auto;">
        Your financial companion for smart investing decisions - quick, easy & informed
    </p>
</div>
""", unsafe_allow_html=True)

# Modern header with futuristic design
st.markdown("""
<div style="background: linear-gradient(90deg, rgba(255,107,26,0.05) 0%, rgba(45,48,71,0.05) 100%); 
            padding: 20px; border-radius: 15px; margin-bottom: 20px;">
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="flex: 1;">
            <h3 style="margin:0; color:#2D3047; font-weight:600;">Real-Time Market Intelligence</h3>
            <p style="margin-top:5px; color:#71717a; font-size:0.9rem;">
                Powered by advanced financial data algorithms and multiple sources
            </p>
        </div>
        <div style="background:#FF6B1A; color:white; padding:8px 16px; border-radius:40px; font-weight:600; font-size:0.8rem;">
            LIVE DATA
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

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
    
    # Custom styled input
    st.markdown('<p style="font-weight:600; font-size:0.9rem; margin-bottom:8px;">Stock Symbol</p>', unsafe_allow_html=True)
    stock_symbol = st.text_input("", initial_value, placeholder="e.g., RELIANCE.NS, TATAMOTORS.NS, INFY.NS").upper()
    # Reset the selected stock after use
    if st.session_state.get('selected_stock'):
        st.session_state['selected_stock'] = None

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
        is_indian = indian_markets.is_indian_symbol(stock_symbol) or '.NS' in stock_symbol or '.BO' in stock_symbol
        
        if is_indian:
            # Get Indian stock data
            stock_data = indian_markets.get_indian_stock_data(stock_symbol, time_period)
            if stock_data is not None and not stock_data.empty:
                company_info = indian_markets.get_indian_company_info(stock_symbol)
            else:
                st.error(f"Unable to fetch data for {stock_symbol}. Please check the symbol and try again.")
                st.stop()
        else:
            # For non-Indian stocks
            ticker = yf.Ticker(stock_symbol)
            stock_data = ticker.history(period=time_period)
            if stock_data is not None and not stock_data.empty:
                company_info = ticker.info
            else:
                st.error(f"Unable to fetch data for {stock_symbol}. Please check the symbol and try again.")
                st.stop()
        
        # Ensure we have enough data for analysis (at least 10 data points)
        if len(stock_data) < 10:
            st.warning(f"Limited data available for {stock_symbol} over the selected time period. Some analyses may be incomplete.")
        
        # Extract sector for peer comparison
        sector = company_info.get('sector', 'Unknown')
        
        # Get list of peer symbols
        peer_symbols = get_peer_symbols(stock_symbol, sector, is_indian)
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

# Main dashboard container with tabs
main_tabs = st.tabs([
    "📊 Overview", 
    "📈 Price Analysis", 
    "🧠 Mood Tracker",  # New emoji-based sentiment tab
    "📃 Financial Statements", 
    "📰 News & Sentiment", 
    "🔮 Predictions", 
    "👥 Peer Comparison", 
    "📋 SWOT Analysis"
])

# Dashboard Overview Tab
with main_tabs[0]:
    # Overview section
    st.header("Company Overview")
    
    overview_col1, overview_col2 = st.columns([2, 1])
    
    with overview_col1:
        if 'longName' in company_info:
            st.subheader(company_info.get('longName', stock_symbol))
            
        st.write(company_info.get('longBusinessSummary', 'No company description available.'))
        
        # Metrics row
        metrics_row = st.columns(4)
        with metrics_row[0]:
            if is_indian:
                # For Indian stocks, show price in Rupees
                price_value = stock_data['Close'].iloc[-1]
                price_change = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100
                st.metric("Current Price", f"₹{price_value:.2f}", f"{price_change:.2f}%")
            else:
                st.metric("Current Price", f"${stock_data['Close'].iloc[-1]:.2f}", 
                        f"{((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100:.2f}%")
        with metrics_row[1]:
            if is_indian:
                # Format market cap in Indian style (Cr, L)
                market_cap = company_info.get('marketCap')
                if market_cap is not None:
                    st.metric("Market Cap", indian_markets.format_inr(market_cap))
                else:
                    st.metric("Market Cap", "N/A")
            else:
                st.metric("Market Cap", utils.format_large_number(company_info.get('marketCap', 'N/A')))
        with metrics_row[2]:
            pe_ratio = company_info.get('trailingPE')
            st.metric("P/E Ratio", f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A")
        with metrics_row[3]:
            if is_indian:
                low = company_info.get('fiftyTwoWeekLow')
                high = company_info.get('fiftyTwoWeekHigh')
                if all(isinstance(val, (int, float)) for val in [low, high] if val is not None):
                    st.metric("52W Range", f"₹{low:.2f} - ₹{high:.2f}")
                else:
                    st.metric("52W Range", "N/A")
            else:
                low = company_info.get('fiftyTwoWeekLow')
                high = company_info.get('fiftyTwoWeekHigh')
                if all(isinstance(val, (int, float)) for val in [low, high] if val is not None):
                    st.metric("52W Range", f"${low:.2f} - ${high:.2f}")
                else:
                    st.metric("52W Range", "N/A")
    
    with overview_col2:
        # Display stock chart
        fig = utils.create_price_chart(stock_data, company_info.get('shortName', stock_symbol), is_indian=is_indian)
        st.plotly_chart(fig, use_container_width=True)
        
        # Quick actions section
        st.markdown("### Quick Actions")
        button_cols = st.columns(2)
        with button_cols[0]:
            if st.button("📥 Add to Watchlist", key="add_to_watchlist"):
                # Render the watchlist functionality
                st.session_state['show_watchlist'] = True
        
        with button_cols[1]:
            if st.button("📊 Download Data", key="download_data"):
                csv = stock_data.to_csv()
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{stock_symbol}_data.csv",
                    mime="text/csv",
                )
    
    # Render watchlist section if needed
    if st.session_state.get('show_watchlist', False):
        simple_watchlist.render_watchlist_section(stock_symbol)
    
    # Financial metrics section in overview tab
    st.header("Key Financial Metrics")
    
    try:
        # Get financial metrics
        metrics = financial_metrics.get_financial_metrics(stock_symbol)
        
        # Create tabs for different metric categories
        metric_tabs = st.tabs(["Key Ratios", "Performance", "Valuation", "Growth", "Efficiency"])
        
        # Key Ratios Tab
        with metric_tabs[0]:
            if 'key_ratios' in metrics and metrics['key_ratios']:
                utils.display_metrics_cards(metrics['key_ratios'], "Key Financial Ratios", is_indian=is_indian)
            else:
                st.info("Key ratio data is not available for this stock.")
        
        # Performance Tab
        with metric_tabs[1]:
            if 'performance' in metrics and metrics['performance']:
                utils.display_metrics_cards(metrics['performance'], "Performance Metrics", is_indian=is_indian)
            else:
                st.info("Performance metrics are not available for this stock.")
                
        # Valuation Tab
        with metric_tabs[2]:
            if 'valuation' in metrics and metrics['valuation']:
                utils.display_metrics_cards(metrics['valuation'], "Valuation Metrics", is_indian=is_indian)
            else:
                st.info("Valuation metrics are not available for this stock.")
                
        # Growth Tab
        with metric_tabs[3]:
            if 'growth' in metrics and metrics['growth']:
                utils.display_metrics_cards(metrics['growth'], "Growth Metrics")
            else:
                st.info("Growth metrics are not available for this stock.")
                
        # Efficiency Tab
        with metric_tabs[4]:
            if 'efficiency' in metrics and metrics['efficiency']:
                utils.display_metrics_cards(metrics['efficiency'], "Efficiency Metrics")
            else:
                st.info("Efficiency metrics are not available for this stock.")
    
    except Exception as e:
        st.error(f"Error loading financial metrics: {str(e)}")

# Price Analysis Tab
with main_tabs[1]:
    # Price Analysis section
    st.header("Price Analysis")
    
    # Chart options
    chart_col1, chart_col2, chart_col3 = st.columns([1, 1, 1])
    
    with chart_col1:
        chart_type = st.selectbox(
            "Chart Type",
            ["Candlestick", "Line", "OHLC", "Area"]
        )
    
    with chart_col2:
        indicators = st.multiselect(
            "Technical Indicators",
            ["Moving Average", "Bollinger Bands", "RSI", "MACD", "Volume"],
            default=["Moving Average", "Volume"]
        )
    
    with chart_col3:
        if "Moving Average" in indicators:
            ma_periods = st.multiselect(
                "MA Periods",
                [5, 10, 20, 50, 100, 200],
                default=[20, 50]
            )
        else:
            ma_periods = []
    
    # Display the selected chart
    try:
        fig = utils.create_technical_chart(
            stock_data, 
            chart_title=f"{company_info.get('shortName', stock_symbol)} - {chart_type} Chart",
            chart_type=chart_type.lower(),
            indicators=indicators,
            ma_periods=ma_periods,
            is_indian=is_indian
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
    
    # Statistics section
    st.subheader("Price Statistics")
    
    stats_col1, stats_col2 = st.columns(2)
    
    with stats_col1:
        # Calculate basic statistics
        stats = stock_data['Close'].describe()
        
        # Format values based on currency
        currency = "₹" if is_indian else "$"
        
        st.write("**Basic Statistics**")
        metrics_data = {
            "Mean": f"{currency}{stats['mean']:.2f}",
            "Median": f"{currency}{stock_data['Close'].median():.2f}",
            "Std Dev": f"{currency}{stats['std']:.2f}",
            "Min": f"{currency}{stats['min']:.2f}",
            "Max": f"{currency}{stats['max']:.2f}"
        }
        utils.display_metrics_cards(metrics_data, "")
    
    with stats_col2:
        # Calculate returns statistics
        daily_returns = stock_data['Close'].pct_change().dropna()
        
        st.write("**Returns Analysis**")
        metrics_data = {
            "Daily Avg Return": f"{daily_returns.mean()*100:.2f}%",
            "Daily Volatility": f"{daily_returns.std()*100:.2f}%",
            "Max Daily Gain": f"{daily_returns.max()*100:.2f}%",
            "Max Daily Loss": f"{daily_returns.min()*100:.2f}%",
            "Positive Days": f"{(daily_returns > 0).sum()} ({(daily_returns > 0).mean()*100:.1f}%)"
        }
        utils.display_metrics_cards(metrics_data, "")

# Financial Statements Tab
with main_tabs[2]:
    # Financial statements section
    st.header("Financial Statements")
    
    statement_tabs = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
    
    with statement_tabs[0]:
        income_statement = utils.get_income_statement(stock_symbol)
        if not income_statement.empty:
            st.write("All figures in millions USD")
            st.dataframe(income_statement)
        else:
            st.write("Income statement data not available for this stock.")
    
    with statement_tabs[1]:
        balance_sheet = utils.get_balance_sheet(stock_symbol)
        if not balance_sheet.empty:
            st.write("All figures in millions USD")
            st.dataframe(balance_sheet)
        else:
            st.write("Balance sheet data not available for this stock.")
    
    with statement_tabs[2]:
        cash_flow = utils.get_cash_flow(stock_symbol)
        if not cash_flow.empty:
            st.write("All figures in millions USD")
            st.dataframe(cash_flow)
        else:
            st.write("Cash flow data not available for this stock.")

# News & Sentiment Tab
with main_tabs[3]:
    # News section
    stock_news.display_news(stock_symbol)

# Predictions Tab
with main_tabs[4]:
    # Price prediction section
    stock_prediction.display_prediction_section(
        stock_symbol,
        stock_data,
        company_info.get('shortName', stock_symbol),
        is_indian
    )

# Peer Comparison Tab
with main_tabs[5]:
    # Peer comparison section
    st.header("Peer Comparison")
    
    # Display sector information
    st.subheader(f"Sector: {sector}")
    st.write(f"Comparing {company_info.get('shortName', stock_symbol)} with similar companies in the {sector} sector.")
    
    # Get peer comparison data
    try:
        # Get peer comparison data
        all_symbols = [stock_symbol] + peer_symbols
        
        # Initialize an empty DataFrame
        comparison_data = pd.DataFrame()
        
        # Define metrics to fetch
        metrics = [
            'shortName', 'currentPrice', 'marketCap', 'trailingPE', 
            'priceToBook', 'profitMargins', 'returnOnEquity',
            'dividendYield', 'beta'
        ]
        
        # Fetch data for each symbol
        for symbol in all_symbols:
            try:
                if is_indian and (symbol.endswith('.NS') or symbol.endswith('.BO')):
                    # Use indian_markets module for Indian stocks
                    info = indian_markets.get_indian_company_info(symbol)
                else:
                    # Use yfinance for other stocks
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                
                # Extract metrics
                data = {}
                data['Symbol'] = symbol
                data['Company'] = info.get('shortName', symbol)
                
                # Market data
                data['Price'] = info.get('currentPrice', info.get('regularMarketPrice', None))
                
                # Market cap (with Indian notation if needed)
                market_cap = info.get('marketCap', None)
                if is_indian and market_cap:
                    data['Market Cap'] = indian_markets.format_inr(market_cap)
                else:
                    data['Market Cap'] = utils.format_large_number(market_cap) if market_cap else None
                
                # Other metrics
                data['P/E Ratio'] = info.get('trailingPE', None)
                data['P/B Ratio'] = info.get('priceToBook', None)
                data['Profit Margin'] = info.get('profitMargins', None) * 100 if info.get('profitMargins') else None
                data['ROE'] = info.get('returnOnEquity', None) * 100 if info.get('returnOnEquity') else None
                data['Dividend Yield'] = info.get('dividendYield', None) * 100 if info.get('dividendYield') else None
                data['Beta'] = info.get('beta', None)
                
                # Append to DataFrame
                comparison_data = pd.concat([comparison_data, pd.DataFrame([data])], ignore_index=True)
                
            except Exception as e:
                st.warning(f"Error fetching data for {symbol}: {str(e)}")
        
        # Format percentages
        for col in ['Profit Margin', 'ROE', 'Dividend Yield']:
            if col in comparison_data.columns:
                comparison_data[col] = comparison_data[col].apply(
                    lambda x: f"{x:.2f}%" if pd.notnull(x) else None
                )
        
        # Format other numeric columns
        for col in ['P/E Ratio', 'P/B Ratio', 'Beta']:
            if col in comparison_data.columns:
                comparison_data[col] = comparison_data[col].apply(
                    lambda x: f"{x:.2f}" if pd.notnull(x) else None
                )
        
        # Format price with currency symbol
        comparison_data['Price'] = comparison_data['Price'].apply(
            lambda x: f"₹{x:.2f}" if pd.notnull(x) and is_indian else f"${x:.2f}" if pd.notnull(x) else None
        )
        
        # Display peer comparison with styled dataframe
        if not comparison_data.empty:
            st.dataframe(
                comparison_data,
                column_config={
                    "Symbol": st.column_config.TextColumn("Symbol", width="medium"),
                    "Company": st.column_config.TextColumn("Company", width="large"),
                    "Price": st.column_config.TextColumn("Price", width="medium"),
                    "Market Cap": st.column_config.TextColumn("Market Cap", width="medium"),
                    "P/E Ratio": st.column_config.TextColumn("P/E Ratio", width="medium"),
                    "P/B Ratio": st.column_config.TextColumn("P/B Ratio", width="medium"),
                    "Profit Margin": st.column_config.TextColumn("Profit Margin", width="medium"),
                    "ROE": st.column_config.TextColumn("ROE", width="medium"),
                    "Dividend Yield": st.column_config.TextColumn("Dividend Yield", width="medium"),
                    "Beta": st.column_config.TextColumn("Beta", width="medium"),
                },
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("Could not fetch peer comparison data.")
    except Exception as e:
        st.error(f"Error generating peer comparison: {str(e)}")

# SWOT Analysis Tab
with main_tabs[6]:
    # SWOT Analysis section
    st.header("SWOT Analysis")
    st.write(f"Strategic analysis for {company_info.get('shortName', stock_symbol)}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Strengths**")
        if sector == "Technology":
            st.write("- Strong R&D capabilities")
            st.write("- Diverse product portfolio")
            st.write("- Global market presence")
        else:
            st.write("- Established market position")
            st.write("- Strong financial performance")
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
    
    # Initialize an empty DataFrame
    comparison_data = pd.DataFrame()
    
    # Define metrics to fetch
    metrics = [
        'shortName', 'currentPrice', 'marketCap', 'trailingPE', 
        'priceToBook', 'profitMargins', 'returnOnEquity',
        'dividendYield', 'beta'
    ]
    
    # Fetch data for each symbol
    for symbol in all_symbols:
        try:
            if is_indian and (symbol.endswith('.NS') or symbol.endswith('.BO')):
                # Use indian_markets module for Indian stocks
                info = indian_markets.get_indian_company_info(symbol)
            else:
                # Use yfinance for other stocks
                ticker = yf.Ticker(symbol)
                info = ticker.info
            
            # Extract metrics
            data = {}
            data['Symbol'] = symbol
            data['Company'] = info.get('shortName', symbol)
            
            # Market data
            data['Price'] = info.get('currentPrice', info.get('regularMarketPrice', None))
            
            # Market cap (with Indian notation if needed)
            market_cap = info.get('marketCap', None)
            if is_indian and market_cap:
                data['Market Cap'] = indian_markets.format_inr(market_cap)
            else:
                data['Market Cap'] = utils.format_large_number(market_cap) if market_cap else None
            
            # Other metrics
            data['P/E Ratio'] = info.get('trailingPE', None)
            data['P/B Ratio'] = info.get('priceToBook', None)
            data['Profit Margin'] = info.get('profitMargins', None) * 100 if info.get('profitMargins') else None
            data['ROE'] = info.get('returnOnEquity', None) * 100 if info.get('returnOnEquity') else None
            data['Dividend Yield'] = info.get('dividendYield', None) * 100 if info.get('dividendYield') else None
            data['Beta'] = info.get('beta', None)
            
            # Append to DataFrame
            comparison_data = comparison_data.append(data, ignore_index=True)
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
    
    # Format percentages
    for col in ['Profit Margin', 'ROE', 'Dividend Yield']:
        if col in comparison_data.columns:
            comparison_data[col] = comparison_data[col].apply(
                lambda x: f"{x:.2f}%" if pd.notnull(x) else None
            )
    
    # Format other numeric columns
    for col in ['P/E Ratio', 'P/B Ratio', 'Beta']:
        if col in comparison_data.columns:
            comparison_data[col] = comparison_data[col].apply(
                lambda x: f"{x:.2f}" if pd.notnull(x) else None
            )
    
    # Format price with currency symbol
    comparison_data['Price'] = comparison_data['Price'].apply(
        lambda x: f"₹{x:.2f}" if pd.notnull(x) and is_indian else f"${x:.2f}" if pd.notnull(x) else None
    )
    
    return comparison_data

# Add a modern footer with futuristic design
st.markdown("""
<div style="background: linear-gradient(90deg, rgba(255,107,26,0.03) 0%, rgba(45,48,71,0.03) 100%); 
            padding: 15px; border-radius: 10px; text-align: center; margin-top: 30px;">
    <p style="margin:0; color:#71717a; font-size:0.8rem;">
        MoneyMitra - Real-time financial analytics platform for smart investing decisions
    </p>
    <p style="margin:5px 0 0 0; color:#71717a; font-size:0.7rem;">
        Powered by advanced data analysis and multi-source intelligence
    </p>
</div>
""", unsafe_allow_html=True)