import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Money-Mitra - Simple Version",
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

def get_stock_data(ticker_symbol, period="1y"):
    """Get stock data using yfinance"""
    ticker = yf.Ticker(ticker_symbol)
    history = ticker.history(period=period)
    info = ticker.info
    return ticker, history, info

def plot_stock_chart(ticker_data, period="1y"):
    """Create interactive stock price chart"""
    fig = go.Figure()
    
    fig.add_trace(
        go.Candlestick(
            x=ticker_data.index,
            open=ticker_data['Open'],
            high=ticker_data['High'],
            low=ticker_data['Low'],
            close=ticker_data['Close'],
            name="Price"
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=ticker_data.index,
            y=ticker_data['Close'].rolling(window=20).mean(),
            line=dict(color='orange', width=1),
            name="20-day MA"
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=ticker_data.index,
            y=ticker_data['Close'].rolling(window=50).mean(),
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
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Company:** {info.get('longName', 'N/A')}")
        st.write(f"**Sector:** {info.get('sector', 'N/A')}")
        st.write(f"**Industry:** {info.get('industry', 'N/A')}")
        st.write(f"**Country:** {info.get('country', 'N/A')}")
    
    with col2:
        st.write(f"**Market Cap:** ${info.get('marketCap', 0)/1e9:.2f} B")
        st.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
        st.write(f"**Dividend Yield:** {info.get('dividendYield', 0)*100:.2f}%")
        st.write(f"**52 Week Range:** ${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}")

def display_financials(ticker):
    """Display company financials"""
    try:
        income_stmt = ticker.income_stmt
        balance_sheet = ticker.balance_sheet
        cash_flow = ticker.cashflow
        
        st.subheader("Income Statement")
        st.dataframe(income_stmt.iloc[:10], use_container_width=True)
        
        st.subheader("Balance Sheet")
        st.dataframe(balance_sheet.iloc[:10], use_container_width=True)
        
        st.subheader("Cash Flow")
        st.dataframe(cash_flow.iloc[:10], use_container_width=True)
    except Exception as e:
        st.warning(f"Unable to fetch financial data: {str(e)}")

# Main App
st.markdown("<h1 class='main-header'>Money-Mitra (Simple Version)</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Your Financial Analysis Assistant</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Navigation")
    stock_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT, AMZN)", value="AAPL")
    time_period = st.selectbox(
        "Select Time Period",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
        index=3
    )
    
    st.caption("For NSE Stocks, add .NS (e.g. RELIANCE.NS)")
    
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
            ticker, history, info = get_stock_data(
                st.session_state['stock_symbol'],
                st.session_state['time_period']
            )
            
            if history.empty:
                st.error(f"No data found for {st.session_state['stock_symbol']}. Please check the symbol and try again.")
            else:
                # Stock Overview
                st.markdown("<h2 class='subheader'>Stock Overview</h2>", unsafe_allow_html=True)
                display_stock_info(info)
                
                # Stock Chart
                st.markdown("<h2 class='subheader'>Stock Chart</h2>", unsafe_allow_html=True)
                fig = plot_stock_chart(history, st.session_state['time_period'])
                st.plotly_chart(fig, use_container_width=True)
                
                # Financials
                st.markdown("<h2 class='subheader'>Financial Statements</h2>", unsafe_allow_html=True)
                display_financials(ticker)
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
else:
    st.info("Enter a stock symbol in the sidebar and click 'Analyze' to get started.")

# Footer
st.markdown("---")
st.caption("Money-Mitra - A Financial Analysis Platform") 