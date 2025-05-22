import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Money-Mitra - YFinance Version",
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
        st.error(f"Error fetching data: {e}")
        return None

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

def display_stock_info(ticker_data):
    """Display basic stock information"""
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

def display_financials(ticker_data):
    """Display company financials without using pyarrow-dependent functions"""
    if ticker_data is None:
        st.error("No financial data available")
        return
    
    ticker_symbol = ticker_data['info'].get('symbol', '')
    
    try:
        # Get financial statements
        ticker = yf.Ticker(ticker_symbol)
        income_stmt = ticker.income_stmt
        balance_sheet = ticker.balance_sheet
        cash_flow = ticker.cashflow
        
        # Display Income Statement
        if not income_stmt.empty:
            st.subheader("Income Statement")
            # Convert to HTML to avoid using st.dataframe or st.table
            st.markdown(income_stmt.head(5).to_html(), unsafe_allow_html=True)
        
        # Display Balance Sheet
        if not balance_sheet.empty:
            st.subheader("Balance Sheet")
            # Convert to HTML to avoid using st.dataframe or st.table
            st.markdown(balance_sheet.head(5).to_html(), unsafe_allow_html=True)
        
        # Display Cash Flow
        if not cash_flow.empty:
            st.subheader("Cash Flow")
            # Convert to HTML to avoid using st.dataframe or st.table
            st.markdown(cash_flow.head(5).to_html(), unsafe_allow_html=True)
            
    except Exception as e:
        st.warning(f"Unable to format financial data: {str(e)}")

def display_news(ticker_data):
    """Display recent news"""
    if ticker_data is None or 'news' not in ticker_data:
        return
    
    news = ticker_data['news']
    
    if news:
        st.subheader("Recent News")
        
        for article in news[:5]:  # Show 5 most recent articles
            title = article.get('title', 'No title')
            publisher = article.get('publisher', 'Unknown publisher')
            article_url = article.get('link', '#')
            publish_time = datetime.fromtimestamp(article.get('providerPublishTime', 0))
            
            st.markdown(f"**[{title}]({article_url})**")
            st.caption(f"{publisher} • {publish_time.strftime('%Y-%m-%d %H:%M')}")
            st.write("---")

def display_recommendations(ticker_data):
    """Display analyst recommendations"""
    if ticker_data is None or 'recommendations' not in ticker_data or ticker_data['recommendations'] is None:
        return
    
    recommendations = ticker_data['recommendations']
    
    if not recommendations.empty:
        st.subheader("Analyst Recommendations")
        # Convert to HTML to avoid using st.dataframe or st.table
        st.markdown(recommendations.tail(5).to_html(), unsafe_allow_html=True)

# Main App
st.markdown("<h1 class='main-header'>Money-Mitra (YFinance Version)</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Your Financial Analysis Assistant</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Navigation")
    stock_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT, AMZN)", value="AAPL")
    
    # For Indian stocks, add .NS (NSE) or .BO (BSE)
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

if st.session_state['analyze_clicked']:
    try:
        with st.spinner(f"Analyzing {st.session_state['stock_symbol']}..."):
            data = get_stock_data(
                st.session_state['stock_symbol'],
                st.session_state['time_period']
            )
            
            if data is None or data['history'].empty:
                st.error(f"No data found for {st.session_state['stock_symbol']}. Please check the symbol and try again.")
            else:
                # Stock Overview
                st.markdown("<h2 class='subheader'>Stock Overview</h2>", unsafe_allow_html=True)
                display_stock_info(data)
                
                # Stock Chart
                st.markdown("<h2 class='subheader'>Stock Chart</h2>", unsafe_allow_html=True)
                fig = plot_stock_chart(data)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # Display News
                st.markdown("<h2 class='subheader'>Recent News</h2>", unsafe_allow_html=True)
                display_news(data)
                
                # Display Recommendations
                st.markdown("<h2 class='subheader'>Analyst Recommendations</h2>", unsafe_allow_html=True)
                display_recommendations(data)
                
                # Financials
                st.markdown("<h2 class='subheader'>Financial Statements</h2>", unsafe_allow_html=True)
                display_financials(data)
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
else:
    st.info("Enter a stock symbol in the sidebar and click 'Analyze' to get started.")

# Footer
st.markdown("---")
st.caption("Money-Mitra - A Financial Analysis Platform") 