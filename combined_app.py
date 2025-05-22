import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Set pandas options to avoid pyarrow dependency
pd.options.mode.use_inf_as_na = True
# Disable pyarrow usage
os.environ['ARROW_PRE_0_15_IPC_FORMAT'] = '1'

# EODHD API key from environment variable
DEFAULT_EODHD_API_KEY = os.environ.get("EODHD_API_KEY", "")

# Page configuration
st.set_page_config(
    page_title="Money-Mitra - Finance Dashboard",
    page_icon="💰",
    layout="wide"
)

# Custom CSS to style the app
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1E88E5;
    text-align: center;
    margin-bottom: 1rem;
}
.subheader {
    font-size: 1.5rem;
    color: #424242;
    margin-bottom: 1rem;
}
.data-source {
    background-color: #f0f2f6;
    border-radius: 5px;
    padding: 10px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state for API key
if 'eodhd_api_key' not in st.session_state:
    st.session_state['eodhd_api_key'] = DEFAULT_EODHD_API_KEY

# Data source functions
def get_yfinance_data(symbol, period="1y"):
    """Get stock data using yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period)
        info = ticker.info
        
        # Get additional data
        recommendations = ticker.recommendations
        calendar = ticker.calendar
        news = ticker.news
        
        return {
            "history": history,
            "info": info,
            "recommendations": recommendations,
            "calendar": calendar,
            "news": news
        }
    except Exception as e:
        st.error(f"Error fetching data from Yahoo Finance: {e}")
        return None

def get_eodhd_data(symbol, period="1y", api_key=None):
    """Get stock data using EODHD API"""
    if not api_key:
        api_key = st.session_state['eodhd_api_key']
        
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Calculate start date based on period
    if period == "1mo":
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    elif period == "3mo":
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    elif period == "6mo":
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    elif period == "1y":
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    elif period == "2y":
        start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    elif period == "5y":
        start_date = (datetime.now() - timedelta(days=1825)).strftime('%Y-%m-%d')
    else:
        start_date = "2000-01-01"  # For "max" period
    
    try:
        # Historical price data
        price_url = f"https://eodhistoricaldata.com/api/eod/{symbol}?api_token={api_key}&period=d&from={start_date}&to={end_date}&fmt=json"
        price_response = requests.get(price_url)
        
        if price_response.status_code != 200:
            st.error(f"Error fetching price data from EODHD: {price_response.text}")
            return None
        
        price_data = price_response.json()
        
        # Convert to DataFrame
        df = pd.DataFrame(price_data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            # Rename columns to match yfinance
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
        
        # Fundamentals data
        fundamentals_url = f"https://eodhistoricaldata.com/api/fundamentals/{symbol}?api_token={api_key}&fmt=json"
        fundamentals_response = requests.get(fundamentals_url)
        
        if fundamentals_response.status_code != 200:
            st.warning(f"Error fetching fundamentals data from EODHD: {fundamentals_response.text}")
            fundamentals_data = {}
        else:
            fundamentals_data = fundamentals_response.json()
        
        # Create a structure similar to yfinance for compatibility
        return {
            "history": df,
            "info": fundamentals_data,
            "recommendations": pd.DataFrame(),  # EODHD doesn't provide this
            "calendar": None,
            "news": []  # EODHD doesn't provide this in the same format
        }
    
    except Exception as e:
        st.error(f"Error fetching data from EODHD: {str(e)}")
        return None

# Visualization functions
def plot_stock_chart(ticker_data):
    """Create interactive stock price chart"""
    if ticker_data is None or ticker_data['history'].empty:
        st.error("No data available for chart")
        return None
    
    history = ticker_data['history']
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Candlestick(
            x=history.index,
            open=history['Open'],
            high=history['High'],
            low=history['Low'],
            close=history['Close'],
            name="Price"
        )
    )
    
    # Add moving averages
    if len(history) >= 20:
        fig.add_trace(
            go.Scatter(
                x=history.index,
                y=history['Close'].rolling(window=20).mean(),
                line=dict(color='orange', width=1),
                name="20-day MA"
            )
        )
    
    if len(history) >= 50:
        fig.add_trace(
            go.Scatter(
                x=history.index,
                y=history['Close'].rolling(window=50).mean(),
                line=dict(color='green', width=1),
                name="50-day MA"
            )
        )
    
    fig.update_layout(
        title="Stock Price Chart",
        xaxis_title="Date",
        yaxis_title="Price",
        height=600,
        xaxis_rangeslider_visible=False
    )
    
    return fig

def display_stock_info_yfinance(ticker_data):
    """Display basic stock information from Yahoo Finance"""
    if ticker_data is None:
        st.error("No data available")
        return
    
    info = ticker_data['info']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Company:** {info.get('longName', 'N/A')}")
        st.write(f"**Sector:** {info.get('sector', 'N/A')}")
        st.write(f"**Industry:** {info.get('industry', 'N/A')}")
        st.write(f"**Country:** {info.get('country', 'N/A')}")
    
    with col2:
        market_cap = info.get('marketCap', 0)
        market_cap_str = f"${market_cap/1e9:.2f} B" if market_cap else "N/A"
        st.write(f"**Market Cap:** {market_cap_str}")
        st.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
        st.write(f"**Dividend Yield:** {info.get('dividendYield', 0)*100:.2f}%")
        st.write(f"**52 Week Range:** ${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}")

def display_stock_info_eodhd(ticker_data):
    """Display basic stock information from EODHD"""
    if ticker_data is None:
        st.error("No data available")
        return
    
    info = ticker_data['info']
    general_info = info.get('General', {})
    highlights = info.get('Highlights', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Company:** {general_info.get('Name', 'N/A')}")
        st.write(f"**Sector:** {general_info.get('Sector', 'N/A')}")
        st.write(f"**Industry:** {general_info.get('Industry', 'N/A')}")
        st.write(f"**Country:** {general_info.get('Country', 'N/A')}")
    
    with col2:
        st.write(f"**Market Cap:** ${highlights.get('MarketCapitalization', 0)/1e9:.2f} B")
        st.write(f"**P/E Ratio:** {highlights.get('PERatio', 'N/A')}")
        st.write(f"**Dividend Yield:** {highlights.get('DividendYield', 0)*100:.2f}%")
        st.write(f"**52 Week Range:** ${highlights.get('52WeekLow', 0):.2f} - ${highlights.get('52WeekHigh', 0):.2f}")

def display_news(ticker_data):
    """Display recent news from Yahoo Finance"""
    if ticker_data is None or 'news' not in ticker_data or not ticker_data['news']:
        st.info("No news available")
        return
    
    news = ticker_data['news']
    
    for article in news[:5]:  # Show 5 most recent articles
        try:
            title = article.get('title', 'No title')
            publisher = article.get('publisher', 'Unknown publisher')
            article_url = article.get('link', '#')
            publish_time = datetime.fromtimestamp(article.get('providerPublishTime', 0))
            
            st.markdown(f"**[{title}]({article_url})**")
            st.caption(f"{publisher} • {publish_time.strftime('%Y-%m-%d %H:%M')}")
            st.write("---")
        except Exception as e:
            st.warning(f"Could not display article: {str(e)}")

def display_recommendations(ticker_data):
    """Display analyst recommendations from Yahoo Finance"""
    if ticker_data is None or 'recommendations' not in ticker_data or ticker_data['recommendations'] is None:
        st.info("No recommendations available")
        return
    
    recommendations = ticker_data['recommendations']
    
    if recommendations is not None and not recommendations.empty:
        st.markdown(recommendations.tail(5).to_html(), unsafe_allow_html=True)
    else:
        st.info("No recommendations available")

def display_financials(ticker_data, data_source):
    """Display company financials without using pyarrow-dependent functions"""
    if ticker_data is None:
        st.error("No financial data available")
        return
    
    if data_source == "Yahoo Finance":
        try:
            ticker_symbol = ticker_data['info'].get('symbol', '')
            
            ticker = yf.Ticker(ticker_symbol)
            income_stmt = ticker.income_stmt
            balance_sheet = ticker.balance_sheet
            cash_flow = ticker.cashflow
            
            # Display Income Statement
            if not income_stmt.empty:
                st.subheader("Income Statement")
                st.markdown(income_stmt.head(5).to_html(), unsafe_allow_html=True)
            
            # Display Balance Sheet
            if not balance_sheet.empty:
                st.subheader("Balance Sheet")
                st.markdown(balance_sheet.head(5).to_html(), unsafe_allow_html=True)
            
            # Display Cash Flow
            if not cash_flow.empty:
                st.subheader("Cash Flow")
                st.markdown(cash_flow.head(5).to_html(), unsafe_allow_html=True)
                
        except Exception as e:
            st.warning(f"Unable to format financial data: {str(e)}")
    
    elif data_source == "EODHD":
        try:
            # Get financial statements
            income_data = ticker_data['info'].get('Financials', {}).get('Income_Statement', {}).get('yearly', {})
            balance_data = ticker_data['info'].get('Financials', {}).get('Balance_Sheet', {}).get('yearly', {})
            cashflow_data = ticker_data['info'].get('Financials', {}).get('Cash_Flow', {}).get('yearly', {})
            
            # Display financials directly without using DataFrames
            if income_data:
                st.subheader("Income Statement")
                # Get the most recent year's data
                recent_year = list(income_data.keys())[0] if income_data else None
                if recent_year:
                    recent_data = income_data[recent_year]
                    st.write(f"**Year:** {recent_year}")
                    for key, value in list(recent_data.items())[:10]:  # Show first 10 items
                        st.write(f"**{key}:** {value}")
            
            if balance_data:
                st.subheader("Balance Sheet")
                # Get the most recent year's data
                recent_year = list(balance_data.keys())[0] if balance_data else None
                if recent_year:
                    recent_data = balance_data[recent_year]
                    st.write(f"**Year:** {recent_year}")
                    for key, value in list(recent_data.items())[:10]:  # Show first 10 items
                        st.write(f"**{key}:** {value}")
            
            if cashflow_data:
                st.subheader("Cash Flow")
                # Get the most recent year's data
                recent_year = list(cashflow_data.keys())[0] if cashflow_data else None
                if recent_year:
                    recent_data = cashflow_data[recent_year]
                    st.write(f"**Year:** {recent_year}")
                    for key, value in list(recent_data.items())[:10]:  # Show first 10 items
                        st.write(f"**{key}:** {value}")
                
        except Exception as e:
            st.warning(f"Unable to format financial data: {str(e)}")

# Main App
st.markdown("<h1 class='main-header'>Money-Mitra Finance Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Your Financial Analysis Assistant</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Navigation")
    
    # Data source selection
    st.subheader("Data Source")
    data_source = st.radio("Select Data Source:", ["Yahoo Finance", "EODHD"], horizontal=True)
    
    if data_source == "EODHD":
        api_key_msg = """
        **API Key Required**
        Enter your EODHD API key below. For security, this key is not stored permanently.
        """
        st.markdown(api_key_msg)
        eodhd_api_key = st.text_input("EODHD API Key", value=st.session_state['eodhd_api_key'], type="password")
        if eodhd_api_key:
            st.session_state['eodhd_api_key'] = eodhd_api_key
        if not eodhd_api_key:
            st.warning("⚠️ Please enter your EODHD API key to use this data source")
    
    # Stock Symbol input
    st.subheader("Stock Information")
    stock_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT, AMZN)", value="AAPL")
    
    # Help text for different exchanges
    if data_source == "Yahoo Finance":
        st.caption("For NSE Stocks, add .NS (e.g. RELIANCE.NS)")
        st.caption("For BSE Stocks, add .BO (e.g. RELIANCE.BO)")
    else:  # EODHD
        st.caption("For NSE Stocks, add .NSE (e.g. RELIANCE.NSE)")
        st.caption("For BSE Stocks, add .BSE (e.g. RELIANCE.BSE)")
    
    time_period = st.selectbox(
        "Select Time Period",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
        index=3
    )
    
    if st.button("Analyze"):
        st.session_state['analyze_clicked'] = True
        st.session_state['stock_symbol'] = stock_symbol
        st.session_state['time_period'] = time_period
        st.session_state['data_source'] = data_source

# Main content
if 'analyze_clicked' not in st.session_state:
    st.session_state['analyze_clicked'] = False
    st.session_state['data_source'] = data_source

# Data source indicator
st.markdown(f"<div class='data-source'>📊 Data Source: <b>{st.session_state['data_source']}</b></div>", unsafe_allow_html=True)

if st.session_state['analyze_clicked']:
    try:
        with st.spinner(f"Analyzing {st.session_state['stock_symbol']}..."):
            # Get data based on selected source
            if st.session_state['data_source'] == "Yahoo Finance":
                data = get_yfinance_data(
                    st.session_state['stock_symbol'],
                    st.session_state['time_period']
                )
            else:  # EODHD
                data = get_eodhd_data(
                    st.session_state['stock_symbol'],
                    st.session_state['time_period']
                )
            
            if data is None or data['history'].empty:
                st.error(f"No data found for {st.session_state['stock_symbol']}. Please check the symbol and try again.")
            else:
                # Stock Overview
                st.markdown("<h2 class='subheader'>Stock Overview</h2>", unsafe_allow_html=True)
                if st.session_state['data_source'] == "Yahoo Finance":
                    display_stock_info_yfinance(data)
                else:  # EODHD
                    display_stock_info_eodhd(data)
                
                # Stock Chart
                st.markdown("<h2 class='subheader'>Stock Chart</h2>", unsafe_allow_html=True)
                fig = plot_stock_chart(data)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # Display News (Yahoo Finance only)
                if st.session_state['data_source'] == "Yahoo Finance":
                    st.markdown("<h2 class='subheader'>Recent News</h2>", unsafe_allow_html=True)
                    display_news(data)
                    
                    # Display Recommendations (Yahoo Finance only)
                    st.markdown("<h2 class='subheader'>Analyst Recommendations</h2>", unsafe_allow_html=True)
                    display_recommendations(data)
                
                # Financials
                st.markdown("<h2 class='subheader'>Financial Statements</h2>", unsafe_allow_html=True)
                display_financials(data, st.session_state['data_source'])
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
else:
    st.info("Enter a stock symbol in the sidebar and click 'Analyze' to get started.")

# Footer
st.markdown("---")
st.caption("Money-Mitra - A Financial Analysis Platform") 