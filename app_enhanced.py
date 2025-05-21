# Set page configuration - must be the first Streamlit command
import streamlit as st
st.set_page_config(
    page_title="MoneyMitra - Your Financial Mitra",
    page_icon="💰",
    layout="wide",  # Using wide layout for full screen use
    initial_sidebar_state="expanded",
)

# Then import other libraries
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import utils
import financial_metrics
import simple_watchlist
import indian_markets
import stock_news
import format_utils
import sentiment_tracker
import peer_comparison

# Load custom CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Additional customization for better layout
st.markdown("""
<style>
    /* Make container use full width */
    .main .block-container {
        max-width: 100%;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Full-width inputs */
    div.stDateInput, div.stNumberInput > div > div, div.stSelectbox > div > div {
        width: 100%;
    }
    
    /* Hide hamburger menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
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
    # Define peer stocks for different sectors (focusing on Indian markets)
    peers = {
        "Technology": ["INFY.NS", "TECHM.NS", "WIPRO.NS", "HCLTECH.NS"],
        "Financial Services": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS"],
        "Consumer Goods": ["HINDUNILVR.NS", "ITC.NS", "DABUR.NS", "MARICO.NS"],
        "Automotive": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "HEROMOTOCO.NS"],
        "Pharmaceuticals": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS"],
        "Energy": ["RELIANCE.NS", "ONGC.NS", "IOC.NS", "BPCL.NS"],
        "Manufacturing": ["LT.NS", "ADANIENT.NS", "SIEMENS.NS", "ABB.NS"]
    }
    
    # Handle US stocks
    us_peers = {
        "Technology": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
        "Financial Services": ["JPM", "BAC", "C", "WFC", "GS"],
        "Healthcare": ["JNJ", "PFE", "MRK", "ABBV", "UNH"],
        "Consumer Goods": ["PG", "KO", "PEP", "WMT", "COST"],
        "Energy": ["XOM", "CVX", "COP", "EOG", "SLB"]
    }
    
    # Select appropriate peer list
    if is_indian:
        if sector in peers:
            # Filter out the current symbol
            return [p for p in peers[sector] if p != symbol]
        else:
            # Return some major Indian stocks as default
            return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"]
    else:
        if sector in us_peers:
            # Filter out the current symbol
            return [p for p in us_peers[sector] if p != symbol]
        else:
            # Return some major US stocks as default
            return ["AAPL", "MSFT", "GOOGL", "AMZN"]

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
    # Try using the peer_comparison module function first
    try:
        return peer_comparison.get_peer_data(main_symbol, peer_symbols, is_indian)
    except:
        # Fallback to direct implementation
        all_symbols = [main_symbol] + peer_symbols
        comparison_data = []
        
        for symbol in all_symbols:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract key metrics
            try:
                market_cap = info.get('marketCap', 0)
                pe_ratio = info.get('trailingPE', info.get('forwardPE', 0))
                price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
                
                # Get short name or use symbol if not available
                name = info.get('shortName', symbol)
                
                # For Indian stocks, convert currency if needed
                if is_indian and ".NS" in symbol:
                    price_currency = "₹"
                else:
                    price_currency = "$"
                
                # Add to comparison data
                comparison_data.append({
                    'Symbol': symbol,
                    'Name': name,
                    'Price': price,
                    'Currency': price_currency,
                    'Market Cap': market_cap,
                    'P/E Ratio': pe_ratio,
                    'Dividend Yield (%)': dividend_yield,
                    'Is Main': symbol == main_symbol
                })
            except:
                # Skip on error
                continue
                
        return pd.DataFrame(comparison_data)

# Sidebar with enhanced styling
st.sidebar.markdown("<div class='dashboard-title'>MoneyMitra</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='dashboard-subtitle'>Your Financial Mitra for Informed Investment Decisions</div>", unsafe_allow_html=True)

# Create a search box with proper styling
st.sidebar.markdown("### 🔍 Stock Search")
stock_symbol = st.sidebar.text_input("Enter Stock Symbol", value="RELIANCE.NS", 
                                     help="For Indian stocks, add .NS (NSE) or .BO (BSE) suffix")

# Add quick selection for popular stocks
popular_stocks = {
    "Indian Stocks": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "HDFC.NS"],
    "US Stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META"]
}

st.sidebar.markdown("### 📋 Quick Selection")
stock_category = st.sidebar.radio("Select Market", ["Indian Stocks", "US Stocks"])
quick_pick = st.sidebar.selectbox("Popular Stocks", popular_stocks[stock_category])

if st.sidebar.button("Load Selected Stock", key="quick_pick_button"):
    stock_symbol = quick_pick

# Detect if it's an Indian stock
is_indian = indian_markets.is_indian_symbol(stock_symbol)

# Time period selection with more intuitive options
st.sidebar.markdown("### ⏱️ Time Period")
time_period_options = {
    "1 Month": "1mo", 
    "3 Months": "3mo", 
    "6 Months": "6mo", 
    "1 Year": "1y", 
    "2 Years": "2y", 
    "5 Years": "5y", 
    "Max": "max"
}
time_period_selection = st.sidebar.selectbox("Select Time Period", options=list(time_period_options.keys()), index=3)
time_period = time_period_options[time_period_selection]

# Add a watchlist section to sidebar
st.sidebar.markdown("### 📌 Watchlist")
watchlist_symbols = simple_watchlist.render_watchlist_section(stock_symbol)

# Add a "Quick Analysis" section
st.sidebar.markdown("### 🔍 Quick Analysis")
show_financial_ratios = st.sidebar.checkbox("Show Financial Ratios", True)
show_sentiment = st.sidebar.checkbox("Show Sentiment Analysis", True)
show_news = st.sidebar.checkbox("Show Latest News", True)

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
    "📃 Financial Statements", 
    "📰 News & Sentiment", 
    "👥 Peer Comparison", 
    "📋 SWOT Analysis"
])

# Dashboard Overview Tab
with main_tabs[0]:
    # Overview section with more modern and spacious layout
    st.markdown("<div class='dashboard-title'>{}</div>".format(company_info.get('longName', stock_symbol)), unsafe_allow_html=True)
    
    # Create a more balanced 3-column layout for key metrics
    metrics_row = st.columns(3)
    
    # Current Price in first column with large font and color
    with metrics_row[0]:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        current_price = stock_data['Close'].iloc[-1]
        price_change = stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[-2]
        price_change_pct = (price_change / stock_data['Close'].iloc[-2]) * 100
        
        price_color = "positive-value" if price_change >= 0 else "negative-value"
        price_symbol = "▲" if price_change >= 0 else "▼"
        
        formatted_price = format_utils.format_currency(current_price, is_indian)
        formatted_change = format_utils.format_currency(abs(price_change), is_indian)
        
        st.markdown(f"<p class='metric-label'>Current Price</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='metric-value {price_color}'>{formatted_price}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='{price_color}'>{price_symbol} {formatted_change} ({price_change_pct:.2f}%)</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Market Cap in second column
    with metrics_row[1]:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        market_cap = company_info.get('marketCap', 0)
        if is_indian:
            # Convert to crores for Indian stocks
            market_cap_str = format_utils.format_large_number(market_cap, is_indian=True)
        else:
            market_cap_str = format_utils.format_large_number(market_cap)
            
        st.markdown(f"<p class='metric-label'>Market Cap</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='metric-value'>{market_cap_str}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # P/E Ratio in third column
    with metrics_row[2]:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        pe_ratio = company_info.get('trailingPE', company_info.get('forwardPE', 0))
        
        # Add a visual indicator of P/E ratio compared to industry average
        industry_pe = company_info.get('industryPE', 20)  # default industry PE if not available
        pe_status = ""
        if pe_ratio > 0:
            if pe_ratio < industry_pe * 0.8:
                pe_status = "👍 Below industry average"
            elif pe_ratio > industry_pe * 1.2:
                pe_status = "⚠️ Above industry average"
            else:
                pe_status = "Near industry average"
                
        st.markdown(f"<p class='metric-label'>P/E Ratio</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='metric-value'>{pe_ratio:.2f}</p>", unsafe_allow_html=True)
        st.markdown(f"<p>{pe_status}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Create second row of metrics for additional key data
    metrics_row2 = st.columns(3)
    
    # 52-Week Range
    with metrics_row2[0]:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        
        try:
            yearly_data = stock_data.loc[stock_data.index >= (datetime.now() - timedelta(days=365))]
            if not yearly_data.empty:
                low_52_week = yearly_data['Low'].min()
                high_52_week = yearly_data['High'].max()
                current = stock_data['Close'].iloc[-1]
                
                # Calculate where current price falls in the 52-week range (0-100%)
                range_percent = ((current - low_52_week) / (high_52_week - low_52_week)) * 100
                
                # Format values
                low_str = format_utils.format_currency(low_52_week, is_indian)
                high_str = format_utils.format_currency(high_52_week, is_indian)
                
                st.markdown(f"<p class='metric-label'>52-Week Range</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='metric-value'>{low_str} - {high_str}</p>", unsafe_allow_html=True)
                
                # Add a simple visual indicator showing where current price is in the range
                st.progress(min(max(range_percent, 0), 100)/100)
        except:
            st.markdown(f"<p class='metric-label'>52-Week Range</p>", unsafe_allow_html=True)
            st.markdown("<p class='metric-value'>Data unavailable</p>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Volume
    with metrics_row2[1]:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        
        try:
            avg_volume = company_info.get('averageVolume', 0)
            recent_volume = stock_data['Volume'].iloc[-1]
            
            volume_str = format_utils.format_large_number(recent_volume)
            avg_volume_str = format_utils.format_large_number(avg_volume)
            
            # Calculate volume comparison to average
            volume_ratio = (recent_volume / avg_volume) if avg_volume > 0 else 0
            volume_status = ""
            
            if volume_ratio > 1.5:
                volume_status = "📈 High volume"
            elif volume_ratio < 0.5:
                volume_status = "📉 Low volume"
            else:
                volume_status = "Average volume"
                
            st.markdown(f"<p class='metric-label'>Recent Volume</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='metric-value'>{volume_str}</p>", unsafe_allow_html=True)
            st.markdown(f"<p>{volume_status} ({volume_ratio:.1f}x avg)</p>", unsafe_allow_html=True)
        except:
            st.markdown(f"<p class='metric-label'>Volume</p>", unsafe_allow_html=True)
            st.markdown("<p class='metric-value'>Data unavailable</p>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Dividend Yield
    with metrics_row2[2]:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        
        dividend_yield = company_info.get('dividendYield', 0)
        if dividend_yield:
            dividend_yield = dividend_yield * 100  # Convert to percentage
            st.markdown(f"<p class='metric-label'>Dividend Yield</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='metric-value'>{dividend_yield:.2f}%</p>", unsafe_allow_html=True)
            
            # Add dividend comparison to industry
            industry_yield = company_info.get('industry_dividend_yield', 2.0)  # default value
            if dividend_yield > industry_yield * 1.5:
                st.markdown("<p>💰 High yield stock</p>", unsafe_allow_html=True)
            elif dividend_yield > 0:
                st.markdown("<p>Pays dividends</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p>No dividend</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p class='metric-label'>Dividend Yield</p>", unsafe_allow_html=True)
            st.markdown("<p class='metric-value'>No dividend</p>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Company description in expandable section
    with st.expander("📝 Company Description", expanded=False):
        st.write(company_info.get('longBusinessSummary', 'No company description available.'))
    
    # Stock price chart and info section - use full width
    st.markdown("### 📈 Price Performance")
    
    # Create a professional interactive chart
    fig = go.Figure()
    
    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=stock_data.index,
            open=stock_data['Open'],
            high=stock_data['High'],
            low=stock_data['Low'],
            close=stock_data['Close'],
            name='Price',
            increasing_line_color='green',
            decreasing_line_color='red'
        )
    )
    
    # Add 20-day and 50-day moving averages
    fig.add_trace(
        go.Scatter(
            x=stock_data.index,
            y=stock_data['Close'].rolling(window=20).mean(),
            name='20-day MA',
            line=dict(color='blue', width=1.5)
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=stock_data.index,
            y=stock_data['Close'].rolling(window=50).mean(),
            name='50-day MA',
            line=dict(color='orange', width=1.5)
        )
    )
    
    # Add volume as a bar chart at the bottom
    fig.add_trace(
        go.Bar(
            x=stock_data.index,
            y=stock_data['Volume'],
            name='Volume',
            marker_color='rgba(0, 0, 255, 0.3)',
            opacity=0.5,
            yaxis='y2'
        )
    )
    
    # Layout styling
    price_title = f"{company_info.get('shortName', stock_symbol)} Price Chart"
    fig.update_layout(
        title=price_title,
        xaxis_title='Date',
        yaxis_title='Price',
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_rangeslider_visible=False
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Financial highlights section
    st.markdown("### 💹 Financial Highlights")
    
    # Get financial metrics
    metrics = financial_metrics.get_financial_metrics(stock_symbol)
    
    # Display the financial metrics in a clean 3-column layout
    finance_cols = st.columns(3)
    
    # First column - Valuation metrics
    with finance_cols[0]:
        st.markdown("#### Valuation Metrics")
        valuation = metrics.get('valuation', {})
        for key, value in valuation.items():
            if isinstance(value, (int, float)):
                # Format based on type
                if 'ratio' in key.lower() or 'multiple' in key.lower():
                    # Format as decimal
                    st.markdown(f"**{key}**: {value:.2f}")
                elif 'percent' in key.lower() or 'yield' in key.lower():
                    # Format as percentage
                    st.markdown(f"**{key}**: {value:.2f}%")
                else:
                    # Format as large number with commas
                    if is_indian:
                        st.markdown(f"**{key}**: {format_utils.format_indian_numbers(value)}")
                    else:
                        st.markdown(f"**{key}**: {format_utils.format_number(value)}")
            else:
                st.markdown(f"**{key}**: {value}")
    
    # Second column - Profitability metrics
    with finance_cols[1]:
        st.markdown("#### Profitability Metrics")
        profitability = metrics.get('profitability', {})
        for key, value in profitability.items():
            if 'margin' in key.lower() or 'percent' in key.lower() or 'return' in key.lower():
                # Format as percentage
                if isinstance(value, (int, float)):
                    st.markdown(f"**{key}**: {value:.2f}%")
                else:
                    st.markdown(f"**{key}**: {value}")
            else:
                st.markdown(f"**{key}**: {value}")
    
    # Third column - Growth metrics
    with finance_cols[2]:
        st.markdown("#### Growth & Performance")
        growth = metrics.get('growth', {})
        for key, value in growth.items():
            if isinstance(value, (int, float)):
                if 'growth' in key.lower() or 'change' in key.lower():
                    # Format as percentage
                    st.markdown(f"**{key}**: {value:.2f}%")
                else:
                    st.markdown(f"**{key}**: {value}")
            else:
                st.markdown(f"**{key}**: {value}")
    
    # Latest news in the overview section
    if show_news:
        st.markdown("### 📰 Latest News")
        
        # Get news with summaries
        news_items = stock_news.get_stock_news(stock_symbol, max_items=3, with_summaries=True)
        
        # Display the news in an enhanced format
        if news_items:
            news_cols = st.columns(3)
            
            for i, news in enumerate(news_items[:3]):
                with news_cols[i % 3]:
                    st.markdown(f"<div class='news-container'>", unsafe_allow_html=True)
                    st.markdown(f"<p class='news-date'>{news.get('published_date', 'Recent')}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p class='news-title'>{news.get('title', 'No title')}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p class='news-summary'>{news.get('summary', news.get('description', 'No summary available.'))[:150]}...</p>", unsafe_allow_html=True)
                    if news.get('link'):
                        st.markdown(f"<a href='{news['link']}' target='_blank'>Read more</a>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No recent news available for this stock.")
    
    # Display sentiment analysis
    if show_sentiment:
        st.markdown("### 😊 Market Sentiment")
        
        # Create sentiment metrics
        sent_cols = st.columns(4)
        with sent_cols[0]:
            price_sentiment = sentiment_tracker.analyze_price_sentiment(stock_data)
            emoji = price_sentiment.get('emoji', '😐')
            mood = price_sentiment.get('mood', 'Neutral')
            
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.markdown(f"<p class='metric-label'>Price Sentiment</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='sentiment-emoji'>{emoji}</p>", unsafe_allow_html=True)
            st.markdown(f"<p>{mood}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with sent_cols[1]:
            volume_sentiment = sentiment_tracker.analyze_volume_sentiment(stock_data)
            emoji = volume_sentiment.get('emoji', '😐')
            mood = volume_sentiment.get('mood', 'Neutral')
            
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.markdown(f"<p class='metric-label'>Volume Sentiment</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='sentiment-emoji'>{emoji}</p>", unsafe_allow_html=True)
            st.markdown(f"<p>{mood}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with sent_cols[2]:
            news_sentiment = sentiment_tracker.analyze_news_sentiment(stock_symbol)
            emoji = news_sentiment.get('emoji', '😐')
            mood = news_sentiment.get('mood', 'Neutral')
            
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.markdown(f"<p class='metric-label'>News Sentiment</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='sentiment-emoji'>{emoji}</p>", unsafe_allow_html=True)
            st.markdown(f"<p>{mood}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with sent_cols[3]:
            # Overall market mood
            market_mood = sentiment_tracker.get_market_mood_index(price_sentiment, volume_sentiment, news_sentiment)
            
            # Determine emoji based on market mood
            mood_emoji = "😐"
            mood_text = "Neutral"
            
            if market_mood > 75:
                mood_emoji = "🤩"
                mood_text = "Extremely Bullish"
            elif market_mood > 50:
                mood_emoji = "😊"
                mood_text = "Bullish"
            elif market_mood > 25:
                mood_emoji = "🙂"
                mood_text = "Slightly Bullish"
            elif market_mood > 0:
                mood_emoji = "😐"
                mood_text = "Neutral"
            elif market_mood > -25:
                mood_emoji = "🙁"
                mood_text = "Slightly Bearish"
            elif market_mood > -50:
                mood_emoji = "😟"
                mood_text = "Bearish"
            else:
                mood_emoji = "😨"
                mood_text = "Extremely Bearish"
            
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.markdown(f"<p class='metric-label'>Overall Sentiment</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='sentiment-emoji'>{mood_emoji}</p>", unsafe_allow_html=True)
            st.markdown(f"<p>{mood_text}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# Price Analysis Tab
with main_tabs[1]:
    st.header("Price Analysis")
    
    # Create a layout with 3 columns for chart controls
    chart_controls = st.columns(3)
    
    with chart_controls[0]:
        chart_type = st.selectbox("Chart Type", options=["Candlestick", "Line", "OHLC", "Area"])
    
    with chart_controls[1]:
        indicators = st.multiselect("Technical Indicators", 
                                options=["SMA", "EMA", "Bollinger Bands", "RSI", "MACD", "Volume"],
                                default=["SMA", "Volume"])
    
    with chart_controls[2]:
        ma_periods = st.multiselect("Moving Average Periods", 
                              options=[9, 20, 50, 100, 200],
                              default=[20, 50])
    
    # Create advanced interactive chart
    try:
        fig = utils.create_stock_chart(stock_data, company_info, chart_type, indicators, ma_periods, is_indian)
        
        # Set height based on screen
        fig.update_layout(height=600)
        
        # Render chart full width
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
    
    # Add trading statistics section
    st.markdown("### Trading Statistics")
    
    # Create two columns for stats
    stats_col1, stats_col2 = st.columns(2)
    
    with stats_col1:
        # Calculate recent trading stats
        recent_data = stock_data.tail(30)
        
        st.markdown("#### Recent Price Statistics (30 Days)")
        
        # Create a clean table of statistics
        stats = utils.get_price_statistics(recent_data)
        st.markdown(f"**Latest Close Price**: {format_utils.format_currency(stock_data['Close'].iloc[-1], is_indian)}")
        st.markdown(f"**Highest Price**: {format_utils.format_currency(stats['high'], is_indian)}")
        st.markdown(f"**Lowest Price**: {format_utils.format_currency(stats['low'], is_indian)}")
        st.markdown(f"**Price Range**: {format_utils.format_currency(stats['range'], is_indian)}")
        st.markdown(f"**Average Price**: {format_utils.format_currency(stats['avg'], is_indian)}")
        st.markdown(f"**Average Volume**: {format_utils.format_large_number(stats['avg_volume'])}")
    
    with stats_col2:
        st.markdown("#### Return Analysis")
        
        # Calculate daily returns
        daily_returns = stock_data['Close'].pct_change() * 100
        weekly_returns = stock_data['Close'].pct_change(5) * 100
        monthly_returns = stock_data['Close'].pct_change(21) * 100
        yearly_returns = stock_data['Close'].pct_change(252) * 100
        
        # Calculate volatility (standard deviation of returns)
        volatility = daily_returns.std()
        
        # Format returns with colors
        def format_return_html(return_value):
            if pd.isna(return_value):
                return "N/A"
            elif return_value >= 0:
                return f"<span class='positive-value'>+{return_value:.2f}%</span>"
            else:
                return f"<span class='negative-value'>{return_value:.2f}%</span>"
        
        # Display return metrics
        st.markdown(f"**Daily Return**: {format_return_html(daily_returns.iloc[-1])}", unsafe_allow_html=True)
        st.markdown(f"**Weekly Return**: {format_return_html(weekly_returns.iloc[-1])}", unsafe_allow_html=True)
        st.markdown(f"**Monthly Return**: {format_return_html(monthly_returns.iloc[-1])}", unsafe_allow_html=True)
        st.markdown(f"**Yearly Return**: {format_return_html(yearly_returns.iloc[-1])}", unsafe_allow_html=True)
        st.markdown(f"**Volatility (Daily)**: {volatility:.2f}%")
        
        # Calculate Sharpe ratio (if applicable)
        try:
            risk_free_rate = 0.03  # 3% risk-free rate (adjust as needed)
            excess_return = (daily_returns.mean() * 252) - risk_free_rate
            sharpe_ratio = excess_return / (volatility * (252 ** 0.5))
            st.markdown(f"**Sharpe Ratio**: {sharpe_ratio:.2f}")
        except:
            pass

# Financial Statements Tab
with main_tabs[2]:
    st.header("Financial Statements")
    
    # Create subtabs for different statements
    statement_tabs = st.tabs(["Balance Sheet", "Income Statement", "Cash Flow", "Profit & Loss"])
    
    # Balance Sheet Tab
    with statement_tabs[0]:
        st.subheader("Balance Sheet")
        
        # Display subtitle for Balance Sheet
        if is_indian:
            st.write("Consolidated Figures in Rs. Crores")
        else:
            st.write("Consolidated Figures in $ Millions")
            
        try:
            # Get balance sheet data
            balance_sheet = utils.get_balance_sheet(stock_symbol)
            
            if not balance_sheet.empty:
                # Format values for display
                for col in balance_sheet.columns:
                    balance_sheet[col] = balance_sheet[col].apply(
                        lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) and pd.notnull(x) else "N/A"
                    )
                
                # Display the balance sheet
                st.dataframe(balance_sheet, use_container_width=True)
            else:
                st.write("Balance sheet data not available for this stock.")
                
        except Exception as e:
            st.error(f"Error displaying balance sheet: {str(e)}")
            
            # Try to display raw balance sheet data
            try:
                ticker = yf.Ticker(stock_symbol)
                raw_balance = ticker.balance_sheet
                if not raw_balance.empty:
                    # Format values for display
                    for col in raw_balance.columns:
                        raw_balance[col] = raw_balance[col].apply(
                            lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) and pd.notnull(x) else "N/A"
                        )
                    st.dataframe(raw_balance, use_container_width=True)
                else:
                    st.write("Balance sheet data not available for this stock.")
            except:
                st.write("Balance sheet data not available for this stock.")
    
    # Income Statement Tab
    with statement_tabs[1]:
        st.subheader("Income Statement")
        
        # Display subtitle for Income Statement
        if is_indian:
            st.write("Consolidated Figures in Rs. Crores")
        else:
            st.write("Consolidated Figures in $ Millions")
            
        try:
            # Get income statement data
            income_statement = utils.get_income_statement(stock_symbol)
            
            if not income_statement.empty:
                # Format values for display
                for col in income_statement.columns:
                    income_statement[col] = income_statement[col].apply(
                        lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) and pd.notnull(x) else "N/A"
                    )
                
                # Display the income statement
                st.dataframe(income_statement, use_container_width=True)
            else:
                st.write("Income statement data not available for this stock.")
                
        except Exception as e:
            st.error(f"Error displaying income statement: {str(e)}")
            
            # Try to display raw income statement data
            try:
                ticker = yf.Ticker(stock_symbol)
                raw_income = ticker.income_stmt
                if not raw_income.empty:
                    # Format values for display
                    for col in raw_income.columns:
                        raw_income[col] = raw_income[col].apply(
                            lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) and pd.notnull(x) else "N/A"
                        )
                    st.dataframe(raw_income, use_container_width=True)
                else:
                    st.write("Income statement data not available for this stock.")
            except:
                st.write("Income statement data not available for this stock.")
    
    # Cash Flow Tab
    with statement_tabs[2]:
        st.subheader("Cash Flow Statement")
        
        # Display subtitle for Cash Flow Statement
        if is_indian:
            st.write("Consolidated Figures in Rs. Crores")
        else:
            st.write("Consolidated Figures in $ Millions")
            
        try:
            # Get cash flow data
            cash_flow = utils.get_cash_flow(stock_symbol)
            
            if not cash_flow.empty:
                # Format values for display
                for col in cash_flow.columns:
                    cash_flow[col] = cash_flow[col].apply(
                        lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) and pd.notnull(x) else "N/A"
                    )
                
                # Display the cash flow statement
                st.dataframe(cash_flow, use_container_width=True)
            else:
                st.write("Cash flow data not available for this stock.")
                
        except Exception as e:
            st.error(f"Error displaying cash flow statement: {str(e)}")
            
            # Try to display raw cash flow data
            try:
                ticker = yf.Ticker(stock_symbol)
                raw_cash_flow = ticker.cashflow
                if not raw_cash_flow.empty:
                    # Format values for display
                    for col in raw_cash_flow.columns:
                        raw_cash_flow[col] = raw_cash_flow[col].apply(
                            lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) and pd.notnull(x) else "N/A"
                        )
                    st.dataframe(raw_cash_flow, use_container_width=True)
                else:
                    st.write("Cash flow data not available for this stock.")
            except:
                st.write("Cash flow data not available for this stock.")
                
    with statement_tabs[3]:
        st.subheader("Profit & Loss")
        
        # Display subtitle for P&L Statement
        if is_indian:
            st.write("Consolidated Figures in Rs. Crores")
        else:
            st.write("Consolidated Figures in $ Millions")
            
        # Create a simple function to display P&L data
        def display_pl_statement(stock_symbol):
            try:
                # Get stock data
                ticker = yf.Ticker(stock_symbol)
                
                # For proper P&L table, we need to gather info from different sources
                income_data = ticker.income_stmt
                info = ticker.info  # Company general info
                
                # If no income statement is available, fallback to financials
                if income_data is None or income_data.empty:
                    income_data = ticker.financials
                
                # If still no data, show a message and return
                if income_data is None or income_data.empty:
                    st.warning("No financial data available for this stock.")
                    return
                
                # Units conversion factor - Millions for USD, Crores for INR
                divisor = 10000000 if is_indian else 1000000
                currency = "₹" if is_indian else "$"
                
                # Format column names to be more readable (e.g., Sep 2024 instead of 2024-09-30)
                if isinstance(income_data.columns, pd.DatetimeIndex):
                    income_data.columns = [col.strftime('%b %Y') for col in income_data.columns]
                
                # Sort columns to show most recent first
                income_data = income_data.sort_index(axis=1, ascending=False)
                
                # Create our P&L structure with the rows we want to display
                pl_rows = [
                    "Sales",
                    "Expenses",
                    "Operating Profit",
                    "OPM %",
                    "Other Income",
                    "Interest",
                    "Depreciation",
                    "Profit before tax",
                    "Tax %",
                    "Net Profit",
                    "EPS in Rs",
                    "Dividend Payout %"
                ]
                
                # Build a mapping dictionary from Yahoo Finance keys to our P&L rows
                key_mapping = {
                    # Standard keys
                    "Total Revenue": "Sales",
                    "Operating Revenue": "Sales",
                    "Cost Of Revenue": "Expenses",
                    "Total Expenses": "Expenses",
                    "Operating Income": "Operating Profit",
                    "EBIT": "Operating Profit",
                    "Gross Profit": "Operating Profit",
                    "Other Income Expense": "Other Income",
                    "Other Non Operating Income Expenses": "Other Income",
                    "Interest Expense": "Interest",
                    "Interest Expense Non Operating": "Interest",
                    "Reconciled Depreciation": "Depreciation",
                    "Depreciation And Amortization": "Depreciation",
                    "Pretax Income": "Profit before tax",
                    "Income Before Tax": "Profit before tax",
                    "Tax Provision": "Tax %",
                    "Income Tax Expense": "Tax %",
                    "Net Income": "Net Profit",
                    "Net Income Common Stockholders": "Net Profit",
                    "Basic EPS": "EPS in Rs",
                    "Diluted EPS": "EPS in Rs"
                }
                
                # Create a DataFrame to display our formatted P&L statement
                result_df = pd.DataFrame(index=pl_rows)
                
                # Process each year column
                for col in income_data.columns:
                    # Create an empty column 
                    result_df[col] = None
                    
                    # Map values from income statement to our P&L rows
                    for source_key, target_row in key_mapping.items():
                        if source_key in income_data.index:
                            # Get the value
                            value = income_data.loc[source_key, col]
                            
                            # Skip if it's NaN
                            if pd.isna(value):
                                continue
                                
                            # Convert to millions/crores
                            if target_row != "EPS in Rs" and target_row != "OPM %" and target_row != "Tax %" and target_row != "Dividend Payout %":
                                value = value / divisor
                            
                            # Store in our result DataFrame
                            result_df.loc[target_row, col] = value
                    
                    # Calculate any missing values
                    
                    # If we have Sales but no Operating Profit, calculate it
                    if result_df.loc["Sales", col] is not None and result_df.loc["Operating Profit", col] is None:
                        if result_df.loc["Expenses", col] is not None:
                            result_df.loc["Operating Profit", col] = result_df.loc["Sales", col] - result_df.loc["Expenses", col]
                    
                    # If we have Sales and Operating Profit but no Expenses, calculate it
                    if result_df.loc["Sales", col] is not None and result_df.loc["Operating Profit", col] is not None:
                        if result_df.loc["Expenses", col] is None:
                            result_df.loc["Expenses", col] = result_df.loc["Sales", col] - result_df.loc["Operating Profit", col]
                    
                    # Calculate OPM % if we have both Sales and Operating Profit
                    if result_df.loc["Sales", col] is not None and result_df.loc["Operating Profit", col] is not None:
                        if result_df.loc["Sales", col] != 0:
                            result_df.loc["OPM %", col] = (result_df.loc["Operating Profit", col] / result_df.loc["Sales", col]) * 100
                    
                    # Calculate Tax % if we have both Tax and Profit before tax
                    if result_df.loc["Tax %", col] is not None and result_df.loc["Profit before tax", col] is not None:
                        if isinstance(result_df.loc["Tax %", col], (int, float)) and isinstance(result_df.loc["Profit before tax", col], (int, float)):
                            if result_df.loc["Profit before tax", col] != 0:
                                # Calculate actual tax percentage
                                result_df.loc["Tax %", col] = abs(result_df.loc["Tax %", col] / result_df.loc["Profit before tax", col] * 100)
                
                # Format values for display
                display_df = result_df.copy()
                for col in display_df.columns:
                    for idx in display_df.index:
                        value = display_df.loc[idx, col]
                        
                        # Format based on what type of value it is
                        if pd.isna(value) or value is None:
                            display_df.loc[idx, col] = "N/A"
                        elif idx in ["OPM %", "Tax %", "Dividend Payout %"]:
                            # Format percentages
                            try:
                                display_df.loc[idx, col] = f"{int(round(value))}%"
                            except:
                                display_df.loc[idx, col] = "N/A"
                        elif idx == "EPS in Rs":
                            # Format EPS with 2 decimal places
                            try:
                                display_df.loc[idx, col] = f"{value:.2f}"
                            except:
                                display_df.loc[idx, col] = "N/A"
                        else:
                            # Format financial values with commas
                            try:
                                display_df.loc[idx, col] = f"{int(round(value)):,}"
                            except:
                                display_df.loc[idx, col] = "N/A"
                
                # Create HTML for the P&L table with styling
                st.markdown("""
                <style>
                .dataframe {
                    width: 100%;
                    border-collapse: collapse;
                    font-family: Arial, sans-serif;
                }
                .dataframe th, .dataframe td {
                    text-align: right;
                    padding: 8px;
                    border: 1px solid #ddd;
                }
                .dataframe th {
                    background-color: #f5f5f5;
                }
                .dataframe tr:nth-child(3), .dataframe tr:nth-child(8), .dataframe tr:nth-child(10) {
                    font-weight: bold;
                    background-color: #f0f7ff;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Display the P&L table with real data
                st.write(display_df.to_html(classes='dataframe', escape=False), unsafe_allow_html=True)
                
                # If the display_df doesn't have much data, show the raw data as well
                real_data_count = 0
                for col in display_df.columns:
                    for idx in display_df.index:
                        if display_df.loc[idx, col] != "N/A":
                            real_data_count += 1
                
                if real_data_count < 10:
                    st.write("Showing raw financial data for reference:")
                    
                    # Format raw income data for display
                    display_income = income_data.copy()
                    for col in display_income.columns:
                        display_income[col] = display_income[col].apply(
                            lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) and pd.notnull(x) else "N/A"
                        )
                    st.dataframe(display_income, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error displaying P&L statement: {str(e)}")
                
                try:
                    # Fallback to displaying raw income statement
                    ticker = yf.Ticker(stock_symbol)
                    raw_income = ticker.financials
                    
                    if raw_income is not None and not raw_income.empty:
                        st.write("Showing raw financial data:")
                        for col in raw_income.columns:
                            raw_income[col] = raw_income[col].apply(
                                lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) and pd.notnull(x) else "N/A"
                            )
                        st.dataframe(raw_income, use_container_width=True)
                    else:
                        st.warning("No financial data available for this stock.")
                except:
                    st.warning("No financial data available for this stock.")
        
        # Display the P&L statement
        display_pl_statement(stock_symbol)

# News & Sentiment Tab
with main_tabs[3]:
    # Create subtabs for Sentiment Analysis and News
    news_tabs = st.tabs(["Sentiment Analysis", "Latest News"])
    
    # Sentiment Analysis tab
    with news_tabs[0]:
        st.subheader("Market Sentiment Analysis")
        
        # Display sentiment dashboard
        try:
            sentiment_tracker.display_sentiment_dashboard(stock_symbol, stock_data)
        except Exception as e:
            st.error(f"Error displaying sentiment dashboard: {str(e)}")
    
    # News tab
    with news_tabs[1]:
        st.subheader("Latest News & Analysis")
        
        # Get news with summaries
        max_news = st.slider("Number of news articles to display", min_value=3, max_value=20, value=10)
        news_items = stock_news.get_stock_news(stock_symbol, max_items=max_news, with_summaries=True)
        
        # Display news in a clean, card-based format
        if news_items:
            for news in news_items:
                st.markdown("<div class='news-container'>", unsafe_allow_html=True)
                
                # News metadata - date and source
                st.markdown(f"<p class='news-date'>{news.get('published_date', 'Recent')} | {news.get('source', 'Unknown Source')}</p>", unsafe_allow_html=True)
                
                # News title
                st.markdown(f"<p class='news-title'>{news.get('title', 'No title')}</p>", unsafe_allow_html=True)
                
                # News summary or description
                st.markdown(f"<p class='news-summary'>{news.get('summary', news.get('description', 'No summary available.'))}</p>", unsafe_allow_html=True)
                
                # Link to full article
                if news.get('link'):
                    st.markdown(f"<a href='{news['link']}' target='_blank'>Read full article</a>", unsafe_allow_html=True)
                
                # Show sentiment (if available)
                if 'sentiment' in news:
                    sentiment = news['sentiment']
                    if sentiment > 0.2:
                        st.markdown("<span style='color:green'>Positive sentiment</span>", unsafe_allow_html=True)
                    elif sentiment < -0.2:
                        st.markdown("<span style='color:red'>Negative sentiment</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color:grey'>Neutral sentiment</span>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No recent news available for this stock.")

# Peer Comparison Tab
with main_tabs[4]:
    st.header("Peer Comparison")
    
    if not sector or sector == "Unknown":
        st.info(f"Sector information not available for {stock_symbol}. Using default peer group.")
        
    # Get peer comparison data
    comparison_data = get_peer_comparison_data(stock_symbol, peer_symbols, is_indian)
    
    # Display the peer comparison data in a visually appealing way
    if not comparison_data.empty:
        # Create first row of visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Market Cap Comparison Chart
            st.subheader("Market Cap Comparison")
            
            # Create a horizontal bar chart for market cap
            fig = go.Figure()
            
            # Add market cap bars
            for idx, row in comparison_data.iterrows():
                color = 'rgba(0, 102, 204, 0.8)' if row['Symbol'] == stock_symbol else 'rgba(0, 102, 204, 0.4)'
                
                fig.add_trace(go.Bar(
                    y=[row['Name']],
                    x=[row['Market Cap']],
                    orientation='h',
                    marker_color=color,
                    name=row['Symbol'],
                    text=format_utils.format_large_number(row['Market Cap'], is_indian=is_indian),
                    textposition='outside',
                ))
            
            fig.update_layout(
                title="Market Capitalization",
                xaxis_title="Market Cap",
                margin=dict(l=20, r=20, t=40, b=20),
                height=300,
                showlegend=False,
                xaxis=dict(
                    showticklabels=False
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # P/E Ratio Comparison Chart
            st.subheader("P/E Ratio Comparison")
            
            # Create a horizontal bar chart for P/E ratio
            fig = go.Figure()
            
            # Add P/E ratio bars
            for idx, row in comparison_data.iterrows():
                if row['P/E Ratio'] > 0:  # Only show positive P/E ratios
                    color = 'rgba(0, 102, 204, 0.8)' if row['Symbol'] == stock_symbol else 'rgba(0, 102, 204, 0.4)'
                    
                    fig.add_trace(go.Bar(
                        y=[row['Name']],
                        x=[row['P/E Ratio']],
                        orientation='h',
                        marker_color=color,
                        name=row['Symbol'],
                        text=f"{row['P/E Ratio']:.2f}",
                        textposition='outside',
                    ))
            
            fig.update_layout(
                title="Price to Earnings Ratio",
                xaxis_title="P/E Ratio",
                margin=dict(l=20, r=20, t=40, b=20),
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Create second row of visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Price Performance Comparison
            st.subheader("Price Performance")
            
            # Create dict to store performance data
            performance_data = {}
            
            # Get historical data for each stock over the last year
            for symbol in [stock_symbol] + peer_symbols:
                try:
                    if indian_markets.is_indian_symbol(symbol):
                        hist = indian_markets.get_indian_stock_data(symbol, "1y")
                    else:
                        ticker = yf.Ticker(symbol)
                        hist = ticker.history(period="1y")
                    
                    if not hist.empty:
                        # Calculate percentage change from start
                        initial_price = hist['Close'].iloc[0]
                        performance_data[symbol] = [(price / initial_price - 1) * 100 for price in hist['Close']]
                        
                        # Also store the dates
                        if 'dates' not in performance_data:
                            performance_data['dates'] = hist.index
                except:
                    continue
            
            # Create line chart for performance comparison
            if 'dates' in performance_data:
                fig = go.Figure()
                
                for symbol in performance_data:
                    if symbol != 'dates':
                        # Determine if this is the main stock
                        is_main = symbol == stock_symbol
                        
                        # Set line properties based on whether it's the main stock
                        line_width = 3 if is_main else 1.5
                        line_dash = None if is_main else 'dot'
                        
                        # Get the company name from comparison data
                        company_name = symbol
                        for idx, row in comparison_data.iterrows():
                            if row['Symbol'] == symbol:
                                company_name = row['Name']
                                break
                        
                        # Add performance line
                        fig.add_trace(go.Scatter(
                            x=performance_data['dates'],
                            y=performance_data[symbol],
                            mode='lines',
                            name=company_name,
                            line=dict(width=line_width, dash=line_dash)
                        ))
                
                fig.update_layout(
                    title="1-Year Performance (%)",
                    xaxis_title="Date",
                    yaxis_title="Price Change (%)",
                    height=400,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    margin=dict(l=20, r=20, t=60, b=20)
                )
                
                # Add a horizontal line at 0%
                fig.add_shape(
                    type="line",
                    x0=performance_data['dates'].min(),
                    x1=performance_data['dates'].max(),
                    y0=0,
                    y1=0,
                    line=dict(color="grey", width=1, dash="dash")
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough historical data available for performance comparison.")
        
        with col2:
            # Dividend Yield Comparison
            st.subheader("Dividend Yield Comparison")
            
            # Create a horizontal bar chart for dividend yield
            fig = go.Figure()
            
            # Add dividend yield bars
            for idx, row in comparison_data.iterrows():
                if row['Dividend Yield (%)'] > 0:  # Only show positive dividend yields
                    color = 'rgba(0, 102, 204, 0.8)' if row['Symbol'] == stock_symbol else 'rgba(0, 102, 204, 0.4)'
                    
                    fig.add_trace(go.Bar(
                        y=[row['Name']],
                        x=[row['Dividend Yield (%)']],
                        orientation='h',
                        marker_color=color,
                        name=row['Symbol'],
                        text=f"{row['Dividend Yield (%)']:.2f}%",
                        textposition='outside',
                    ))
            
            fig.update_layout(
                title="Dividend Yield (%)",
                xaxis_title="Dividend Yield",
                margin=dict(l=20, r=20, t=40, b=20),
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Display the peer comparison table with good formatting
        st.subheader("Peer Comparison Details")
        
        # Format the data for better display
        formatted_data = comparison_data.copy()
        
        # Format market cap as large numbers
        formatted_data['Market Cap'] = formatted_data['Market Cap'].apply(
            lambda x: format_utils.format_large_number(x, is_indian=is_indian)
        )
        
        # Format P/E ratio with 2 decimal places
        formatted_data['P/E Ratio'] = formatted_data['P/E Ratio'].apply(
            lambda x: f"{x:.2f}" if x > 0 else "N/A"
        )
        
        # Format price with currency
        formatted_data['Formatted Price'] = formatted_data.apply(
            lambda row: f"{row['Currency']}{row['Price']:.2f}", axis=1
        )
        
        # Format dividend yield with percentage
        formatted_data['Dividend Yield (%)'] = formatted_data['Dividend Yield (%)'].apply(
            lambda x: f"{x:.2f}%" if x > 0 else "N/A"
        )
        
        # Display the formatted table
        display_cols = ['Symbol', 'Name', 'Formatted Price', 'Market Cap', 'P/E Ratio', 'Dividend Yield (%)']
        
        # Highlight the selected stock
        def highlight_selected(df):
            return ['background-color: #e6f2ff' if df.loc[i, 'Is Main'] else '' for i in range(len(df))]
        
        st.dataframe(
            formatted_data[display_cols].style.apply(highlight_selected, axis=1),
            use_container_width=True
        )
    else:
        st.error("Unable to retrieve peer comparison data.")

# SWOT Analysis Tab
with main_tabs[5]:
    st.header("SWOT Analysis")
    
    # Create a 2x2 grid for SWOT analysis
    swot_col1, swot_col2 = st.columns(2)
    
    with swot_col1:
        # Strengths section
        st.markdown("""
        <div style='background-color: #e8f4f8; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='color: #0066CC;'>Strengths</h3>
        """, unsafe_allow_html=True)
        
        # List strengths based on the available data
        strengths = []
        
        try:
            # Check financial metrics for strengths
            
            # 1. Strong profit margins compared to industry
            if 'profitMargins' in company_info and company_info['profitMargins'] > 0.15:
                strengths.append("Strong profit margins (above 15%)")
            
            # 2. Low P/E ratio could be a value opportunity
            if 'trailingPE' in company_info and 'forwardPE' in company_info:
                if company_info['trailingPE'] < 15:
                    strengths.append("Attractive valuation with P/E ratio below 15")
                if company_info['forwardPE'] < company_info['trailingPE']:
                    strengths.append("Forward P/E lower than trailing P/E, suggesting expected earnings growth")
            
            # 3. Dividend yield as strength
            if 'dividendYield' in company_info and company_info['dividendYield'] > 0.03:
                strengths.append(f"Strong dividend yield of {company_info['dividendYield']*100:.2f}%")
            
            # 4. Low debt to equity is a strength
            if 'debtToEquity' in company_info and company_info['debtToEquity'] < 50:
                strengths.append("Low debt-to-equity ratio, indicating strong balance sheet")
            
            # 5. Market position
            if 'marketCap' in company_info and company_info['marketCap'] > 10000000000:
                strengths.append("Large market capitalization suggests strong market position")
            
            # 6. Price performance
            if len(stock_data) > 30:
                recent_perf = (stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[-30] - 1) * 100
                if recent_perf > 10:
                    strengths.append(f"Strong recent price performance (+{recent_perf:.1f}% in last month)")
            
            # If we found less than 3 strengths, add placeholders
            if len(strengths) < 3:
                default_strengths = [
                    "Established market presence",
                    "Diversified revenue streams",
                    "Strong brand recognition",
                    "Innovative product/service offerings",
                    "Experienced management team"
                ]
                strengths.extend(default_strengths[:(3-len(strengths))])
        except:
            # Fallback strengths if calculations fail
            strengths = [
                "Established market presence",
                "Diversified revenue streams",
                "Strong brand recognition"
            ]
        
        # Display the strengths as bullet points
        for strength in strengths:
            st.markdown(f"• {strength}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Weaknesses section
        st.markdown("""
        <div style='background-color: #fff4e6; padding: 20px; border-radius: 10px;'>
            <h3 style='color: #FF9933;'>Weaknesses</h3>
        """, unsafe_allow_html=True)
        
        # List weaknesses based on the available data
        weaknesses = []
        
        try:
            # Check financial metrics for weaknesses
            
            # 1. Low profit margins could be a weakness
            if 'profitMargins' in company_info and company_info['profitMargins'] < 0.05:
                weaknesses.append("Low profit margins (below 5%)")
            
            # 2. High P/E ratio could indicate overvaluation
            if 'trailingPE' in company_info and company_info['trailingPE'] > 30:
                weaknesses.append("High P/E ratio may indicate overvaluation")
            
            # 3. High debt is a weakness
            if 'debtToEquity' in company_info and company_info['debtToEquity'] > 100:
                weaknesses.append("High debt-to-equity ratio, increasing financial risk")
            
            # 4. Negative earnings
            if 'returnOnEquity' in company_info and company_info['returnOnEquity'] < 0:
                weaknesses.append("Negative return on equity")
            
            # 5. Price performance
            if len(stock_data) > 30:
                recent_perf = (stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[-30] - 1) * 100
                if recent_perf < -10:
                    weaknesses.append(f"Poor recent price performance ({recent_perf:.1f}% in last month)")
            
            # 6. Volatility
            if len(stock_data) > 20:
                daily_returns = stock_data['Close'].pct_change()
                if daily_returns.std() * 100 > 3:  # High volatility
                    weaknesses.append("High price volatility may indicate uncertainty")
            
            # If we found less than 3 weaknesses, add placeholders
            if len(weaknesses) < 3:
                default_weaknesses = [
                    "Exposure to competitive pressures",
                    "Higher costs compared to peers",
                    "Regulatory challenges in key markets",
                    "Limited product/market diversification",
                    "Potential margin pressure"
                ]
                weaknesses.extend(default_weaknesses[:(3-len(weaknesses))])
        except:
            # Fallback weaknesses if calculations fail
            weaknesses = [
                "Exposure to competitive pressures",
                "Higher costs compared to peers",
                "Regulatory challenges in key markets"
            ]
        
        # Display the weaknesses as bullet points
        for weakness in weaknesses:
            st.markdown(f"• {weakness}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with swot_col2:
        # Opportunities section
        st.markdown("""
        <div style='background-color: #e8f8e8; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='color: #118811;'>Opportunities</h3>
        """, unsafe_allow_html=True)
        
        # List opportunities based on the available data
        opportunities = []
        
        try:
            # Check financial and market data for opportunities
            
            # 1. Industry growth - if sector info is available
            if sector and sector in ["Technology", "Healthcare", "Renewable Energy"]:
                opportunities.append(f"Growth potential in the expanding {sector} sector")
            
            # 2. Forward P/E lower than trailing might suggest growth expectations
            if 'trailingPE' in company_info and 'forwardPE' in company_info:
                if 0 < company_info['forwardPE'] < company_info['trailingPE'] * 0.9:
                    opportunities.append("Analysts projecting improved future earnings")
            
            # 3. Recent price drop might present buying opportunity
            if len(stock_data) > 90:
                recent_3m_perf = (stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[-90] - 1) * 100
                if -20 < recent_3m_perf < -5:
                    opportunities.append("Recent price correction may present entry opportunity")
            
            # 4. Low market share with room to grow
            if 'marketCap' in company_info and company_info['marketCap'] < 5000000000 and sector:
                opportunities.append(f"Room for market share expansion in the {sector} sector")
            
            # If we found less than 3 opportunities, add placeholders
            if len(opportunities) < 3:
                default_opportunities = [
                    "Potential for international expansion",
                    "New product development opportunities",
                    "Strategic acquisition possibilities",
                    "Digital transformation initiatives",
                    "Emerging market penetration"
                ]
                opportunities.extend(default_opportunities[:(3-len(opportunities))])
        except:
            # Fallback opportunities if calculations fail
            opportunities = [
                "Potential for international expansion",
                "New product development opportunities",
                "Strategic acquisition possibilities"
            ]
        
        # Display the opportunities as bullet points
        for opportunity in opportunities:
            st.markdown(f"• {opportunity}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Threats section
        st.markdown("""
        <div style='background-color: #fee8e8; padding: 20px; border-radius: 10px;'>
            <h3 style='color: #cc0000;'>Threats</h3>
        """, unsafe_allow_html=True)
        
        # List threats based on the available data
        threats = []
        
        try:
            # Check financial and market data for threats
            
            # 1. Market volatility
            if len(stock_data) > 30:
                daily_returns = stock_data['Close'].pct_change()
                market_volatility = daily_returns.std() * 100
                if market_volatility > 2.5:
                    threats.append("High market volatility may impact predictability")
            
            # 2. Industry competition
            if sector:
                threats.append(f"Intense competition in the {sector} sector")
            
            # 3. Debt obligations
            if 'debtToEquity' in company_info and company_info['debtToEquity'] > 80:
                threats.append("Significant debt obligations may limit financial flexibility")
            
            # 4. Regulatory risks by sector
            if sector in ["Financial Services", "Healthcare", "Energy"]:
                threats.append(f"Potential regulatory changes affecting the {sector} sector")
            
            # 5. Economic sensitivity
            if sector in ["Consumer Cyclical", "Real Estate", "Industrials"]:
                threats.append("Sensitivity to economic downturns")
            
            # If we found less than 3 threats, add placeholders
            if len(threats) < 3:
                default_threats = [
                    "Increasing competitive pressure",
                    "Potential regulatory challenges",
                    "Economic slowdown risks",
                    "Changing consumer preferences",
                    "Supply chain disruptions"
                ]
                threats.extend(default_threats[:(3-len(threats))])
        except:
            # Fallback threats if calculations fail
            threats = [
                "Increasing competitive pressure",
                "Potential regulatory challenges",
                "Economic slowdown risks"
            ]
        
        # Display the threats as bullet points
        for threat in threats:
            st.markdown(f"• {threat}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Add a disclaimer section
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 15px; border-radius: 8px; margin-top: 20px; font-size: 0.8em;'>
        <p><strong>Disclaimer:</strong> This SWOT analysis is generated based on available financial data and general industry knowledge.
        It is provided for informational purposes only and should not be considered as financial advice. 
        Always conduct your own thorough research before making investment decisions.</p>
    </div>
    """, unsafe_allow_html=True)

# Add footer
st.markdown("""
<div style='background-color: #f5f7fa; padding: 15px; border-radius: 10px; margin-top: 30px; text-align: center;'>
    <p style='font-size: 0.8em; color: #666;'>
        Data provided by Yahoo Finance. MoneyMitra is your financial partner for informed investment decisions.
        <br>Last updated: {}
    </p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)