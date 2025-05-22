import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Set your EODHD API key here
API_KEY = "682d76fa5c4b17.85025825"  # Replace with your actual API key

# Page configuration
st.set_page_config(
    page_title="Money-Mitra - EODHD Version",
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
</style>
""", unsafe_allow_html=True)

def get_stock_data(symbol, period="1y"):
    """Get stock data using EODHD API"""
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
    
    # Historical price data
    price_url = f"https://eodhistoricaldata.com/api/eod/{symbol}?api_token={API_KEY}&period=d&from={start_date}&to={end_date}&fmt=json"
    price_response = requests.get(price_url)
    
    if price_response.status_code != 200:
        st.error(f"Error fetching price data: {price_response.text}")
        return None, None
    
    price_data = price_response.json()
    
    # Convert to DataFrame
    df = pd.DataFrame(price_data)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    
    # Fundamentals data
    fundamentals_url = f"https://eodhistoricaldata.com/api/fundamentals/{symbol}?api_token={API_KEY}&fmt=json"
    fundamentals_response = requests.get(fundamentals_url)
    
    if fundamentals_response.status_code != 200:
        st.warning(f"Error fetching fundamentals data: {fundamentals_response.text}")
        fundamentals_data = {}
    else:
        fundamentals_data = fundamentals_response.json()
    
    return df, fundamentals_data

def plot_stock_chart(ticker_data):
    """Create interactive stock price chart"""
    if ticker_data is None or ticker_data.empty:
        st.error("No data available for chart")
        return None
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Candlestick(
            x=ticker_data.index,
            open=ticker_data['open'],
            high=ticker_data['high'],
            low=ticker_data['low'],
            close=ticker_data['close'],
            name="Price"
        )
    )
    
    # Add moving averages
    if len(ticker_data) >= 20:
        fig.add_trace(
            go.Scatter(
                x=ticker_data.index,
                y=ticker_data['close'].rolling(window=20).mean(),
                line=dict(color='orange', width=1),
                name="20-day MA"
            )
        )
    
    if len(ticker_data) >= 50:
        fig.add_trace(
            go.Scatter(
                x=ticker_data.index,
                y=ticker_data['close'].rolling(window=50).mean(),
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

def display_stock_info(info):
    """Display basic stock information"""
    if not info:
        st.error("No company information available")
        return
    
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

def display_financials(info):
    """Display company financials without using pandas DataFrames (to avoid pyarrow issues)"""
    if not info:
        st.error("No financial data available")
        return
    
    try:
        # Get financial statements
        income_data = info.get('Financials', {}).get('Income_Statement', {}).get('yearly', {})
        balance_data = info.get('Financials', {}).get('Balance_Sheet', {}).get('yearly', {})
        cashflow_data = info.get('Financials', {}).get('Cash_Flow', {}).get('yearly', {})
        
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
st.markdown("<h1 class='main-header'>Money-Mitra (EODHD Version)</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Your Financial Analysis Assistant</p>", unsafe_allow_html=True)

# API key input if not set
if API_KEY == "YOUR_EODHD_API_KEY":
    API_KEY = st.text_input("Enter your EODHD API Key", type="password")
    if not API_KEY:
        st.warning("Please enter your EODHD API Key to continue")
        st.stop()

# Sidebar
with st.sidebar:
    st.title("Navigation")
    stock_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT, AMZN)", value="AAPL")
    time_period = st.selectbox(
        "Select Time Period",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
        index=3
    )
    
    st.caption("For BSE Stocks, add .BSE (e.g. RELIANCE.BSE)")
    st.caption("For NSE Stocks, add .NSE (e.g. RELIANCE.NSE)")
    
    if st.button("Analyze"):
        st.session_state['analyze_clicked'] = True
        st.session_state['stock_symbol'] = stock_symbol
        st.session_state['time_period'] = time_period

# Main content
if 'analyze_clicked' not in st.session_state:
    st.session_state['analyze_clicked'] = False

if st.session_state['analyze_clicked']:
    try:
        with st.spinner(f"Analyzing {st.session_state['stock_symbol']}..."):
            history, info = get_stock_data(
                st.session_state['stock_symbol'],
                st.session_state['time_period']
            )
            
            if history is None or history.empty:
                st.error(f"No data found for {st.session_state['stock_symbol']}. Please check the symbol and try again.")
            else:
                # Stock Overview
                st.markdown("<h2 class='subheader'>Stock Overview</h2>", unsafe_allow_html=True)
                display_stock_info(info)
                
                # Stock Chart
                st.markdown("<h2 class='subheader'>Stock Chart</h2>", unsafe_allow_html=True)
                fig = plot_stock_chart(history)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # Financials
                st.markdown("<h2 class='subheader'>Financial Statements</h2>", unsafe_allow_html=True)
                display_financials(info)
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
else:
    st.info("Enter a stock symbol in the sidebar and click 'Analyze' to get started.")

# Footer
st.markdown("---")
st.caption("Money-Mitra - A Financial Analysis Platform") 