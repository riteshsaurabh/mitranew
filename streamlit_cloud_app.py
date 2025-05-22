import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

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
    st.session_state['eodhd_api_key'] = os.environ.get("EODHD_API_KEY", "")

# Data source functions
def get_yfinance_data(symbol, period="1y"):
    """Get stock data using yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period)
        info = ticker.info
        
        return {
            "history": history,
            "info": info
        }
    except Exception as e:
        st.error(f"Error fetching data from Yahoo Finance: {e}")
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

# Main App
st.markdown("<h1 class='main-header'>Money-Mitra Finance Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Your Financial Analysis Assistant</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Navigation")
    
    # Stock Symbol input
    st.subheader("Stock Information")
    stock_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT, AMZN)", value="AAPL")
    
    # Help text for different exchanges
    st.caption("For NSE Stocks, add .NS (e.g. RELIANCE.NS)")
    st.caption("For BSE Stocks, add .BO (e.g. RELIANCE.BO)")
    
    time_period = st.selectbox(
        "Select Time Period",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
        index=3
    )
    
    if st.button("Analyze"):
        st.session_state['analyze_clicked'] = True
        st.session_state['stock_symbol'] = stock_symbol
        st.session_state['time_period'] = time_period

# Main content
if 'analyze_clicked' not in st.session_state:
    st.session_state['analyze_clicked'] = False

# Data source indicator
st.markdown(f"<div class='data-source'>📊 Data Source: <b>Yahoo Finance</b></div>", unsafe_allow_html=True)

if st.session_state['analyze_clicked']:
    try:
        with st.spinner(f"Analyzing {st.session_state['stock_symbol']}..."):
            # Get data based on Yahoo Finance
            data = get_yfinance_data(
                st.session_state['stock_symbol'],
                st.session_state['time_period']
            )
            
            if data is None or data['history'].empty:
                st.error(f"No data found for {st.session_state['stock_symbol']}. Please check the symbol and try again.")
            else:
                # Stock Overview
                st.markdown("<h2 class='subheader'>Stock Overview</h2>", unsafe_allow_html=True)
                display_stock_info_yfinance(data)
                
                # Stock Chart
                st.markdown("<h2 class='subheader'>Stock Chart</h2>", unsafe_allow_html=True)
                fig = plot_stock_chart(data)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
else:
    st.info("Enter a stock symbol in the sidebar and click 'Analyze' to get started.")

# Footer
st.markdown("---")
st.caption("Money-Mitra - A Financial Analysis Platform")
st.caption("Streamlit Cloud Version - Simplified for stability") 