import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import utils
import financial_metrics

# Page configuration
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

# Title and description
st.title("Stock Analysis Dashboard")
st.write("Enter a stock symbol to get comprehensive financial analysis and visualization")

# Dashboard header with stock market image
col1, col2 = st.columns([1, 3])
with col1:
    st.image("https://pixabay.com/get/g738a334be08e7073603a68932df55ea8c27b445f40ba8f4b3e42a2629cc1dfa830b85a80523ec7bf5bc7932ec2b0ad49bc5bab7cc138fa443e41f23d1313bccb_1280.jpg", 
             use_column_width=True)
with col2:
    st.write("""
    This dashboard provides real-time financial data visualization and metrics powered by Yahoo Finance. 
    Get insights on stock performance, financial ratios, and company overviews in one place.
    """)
    
    # Input for stock symbol
    col_symbol, col_period = st.columns([1, 1])
    
    with col_symbol:
        stock_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT, GOOGL)", "AAPL").upper()
    
    with col_period:
        time_period = st.selectbox(
            "Select Time Period",
            ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        )
    
# Load data with status indicator
with st.spinner(f"Loading data for {stock_symbol}..."):
    try:
        # Get stock data
        stock_data = utils.get_stock_data(stock_symbol, time_period)
        
        # Get company info
        company_info = utils.get_company_info(stock_symbol)
        
        # Get financial metrics
        financial_data = financial_metrics.get_financial_metrics(stock_symbol)
        
        # Basic validation
        if stock_data.empty:
            st.error(f"No data found for symbol {stock_symbol}. Please check the symbol and try again.")
            st.stop()
        
        data_loaded = True
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.write("Please check the stock symbol and try again.")
        data_loaded = False
        st.stop()

if data_loaded:
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
            st.metric("Current Price", f"${stock_data['Close'].iloc[-1]:.2f}", 
                     f"{((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100:.2f}%")
        with metrics_row[1]:
            st.metric("Market Cap", utils.format_large_number(company_info.get('marketCap', 'N/A')))
        with metrics_row[2]:
            st.metric("P/E Ratio", f"{company_info.get('trailingPE', 'N/A'):.2f}" if isinstance(company_info.get('trailingPE'), (int, float)) else "N/A")
        with metrics_row[3]:
            st.metric("52W Range", f"${company_info.get('fiftyTwoWeekLow', 'N/A'):.2f} - ${company_info.get('fiftyTwoWeekHigh', 'N/A'):.2f}" if all(isinstance(company_info.get(x), (int, float)) for x in ['fiftyTwoWeekLow', 'fiftyTwoWeekHigh']) else "N/A")
    
    with overview_col2:
        st.image("https://pixabay.com/get/g87690ed3ce15cbccbebd694d12edf27c88cc096992c61c05e3d858515dbb583c5f8adf1645f81df6bdd0f6982a4a408fdb2f409ed8cc38f390680a33e567f751_1280.jpg", 
                 use_column_width=True)
        
        sector = company_info.get('sector', 'N/A')
        industry = company_info.get('industry', 'N/A')
        website = company_info.get('website', 'N/A')
        
        st.write(f"**Sector:** {sector}")
        st.write(f"**Industry:** {industry}")
        st.write(f"**Exchange:** {company_info.get('exchange', 'N/A')}")
        st.write(f"**Currency:** {company_info.get('currency', 'N/A')}")
        
        if website != 'N/A':
            st.write(f"**Website:** [{website}]({website})")
    
    # Chart section
    st.header("Price History")
    
    chart_tabs = st.tabs(["Line Chart", "Candlestick Chart", "Volume Analysis"])
    
    with chart_tabs[0]:
        fig = utils.create_line_chart(stock_data)
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_tabs[1]:
        fig = utils.create_candlestick_chart(stock_data)
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_tabs[2]:
        fig = utils.create_volume_chart(stock_data)
        st.plotly_chart(fig, use_container_width=True)
    
    # Financial metrics section
    st.header("Financial Metrics")
    
    metrics_tabs = st.tabs(["Key Ratios", "Performance", "Valuation"])
    
    with metrics_tabs[0]:
        if 'key_ratios' in financial_data:
            utils.display_key_ratios_table(financial_data['key_ratios'])
        else:
            st.write("Key ratios data not available for this stock.")
    
    with metrics_tabs[1]:
        if 'performance' in financial_data:
            utils.display_performance_table(financial_data['performance'])
        else:
            st.write("Performance data not available for this stock.")
    
    with metrics_tabs[2]:
        if 'valuation' in financial_data:
            utils.display_valuation_table(financial_data['valuation'])
        else:
            st.write("Valuation data not available for this stock.")
    
    # Financial statements section
    st.header("Financial Statements")
    
    statement_tabs = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
    
    with statement_tabs[0]:
        income_statement = utils.get_income_statement(stock_symbol)
        if not income_statement.empty:
            st.dataframe(income_statement)
        else:
            st.write("Income statement data not available for this stock.")
    
    with statement_tabs[1]:
        balance_sheet = utils.get_balance_sheet(stock_symbol)
        if not balance_sheet.empty:
            st.dataframe(balance_sheet)
        else:
            st.write("Balance sheet data not available for this stock.")
    
    with statement_tabs[2]:
        cash_flow = utils.get_cash_flow(stock_symbol)
        if not cash_flow.empty:
            st.dataframe(cash_flow)
        else:
            st.write("Cash flow data not available for this stock.")
    
    # Download section
    st.header("Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = stock_data.to_csv(index=True)
        st.download_button(
            label="Download Historical Price Data (CSV)",
            data=csv,
            file_name=f"{stock_symbol}_historical_data.csv",
            mime="text/csv",
        )
    
    with col2:
        st.write("Download options available for premium subscribers")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center;">
    <p>Data provided by Yahoo Finance | Created with Streamlit</p>
    <p>This dashboard is for informational purposes only and should not be considered as financial advice.</p>
</div>
""", unsafe_allow_html=True)
