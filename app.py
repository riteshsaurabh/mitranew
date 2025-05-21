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
import random
import format_utils
import stock_prediction
import sentiment_tracker
import peer_comparison
import screener_integration  # New module for fetching data from Screener.in

# Load custom CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# App title and header
st.title("MoneyMitra - Your Financial Mitra for Informed Investment Decisions")

# App description
description = """
Welcome to MoneyMitra! This dashboard is designed to provide comprehensive stock analysis
to help you make informed investment decisions. Enter a stock symbol below to get started.
"""
st.markdown(description)

# Sidebar for input and navigation
with st.sidebar:
    st.header("Search Stocks")
    
    # Checkbox for Indian stocks
    is_indian = st.checkbox("Indian Stock (NSE/BSE)", value=True)
    
    # Stock symbol input
    stock_symbol = st.text_input("Enter Stock Symbol:", value="RELIANCE.NS" if is_indian else "AAPL")
    
    # Search button
    search_clicked = st.button("Analyze")
    
    # Default instructions based on market selection
    if is_indian:
        st.info("""
        **For Indian stocks:**
        - NSE: Add .NS (e.g., RELIANCE.NS, TCS.NS)
        - BSE: Add .BO (e.g., RELIANCE.BO)
        """)
    else:
        st.info("""
        **For US stocks:**
        - Just enter the symbol (e.g., AAPL, MSFT, GOOGL)
        """)

# Main content
if stock_symbol:
    try:
        # Loading spinner
        with st.spinner(f"Fetching data for {stock_symbol}..."):
            # Get stock data
            stock_data = utils.get_stock_data(stock_symbol, period="1y")
            
            if stock_data.empty:
                st.error(f"Could not fetch data for {stock_symbol}. Please check the symbol and try again.")
                st.stop()
            
            # Check if it's an Indian stock (if not specified)
            if not is_indian and indian_markets.is_indian_symbol(stock_symbol):
                is_indian = True
                st.warning(f"Detected an Indian stock. Switching to Indian market mode.")
            
            # Get company info
            company_info = utils.get_company_info(stock_symbol)
            
            # Calculate financial metrics
            metrics = financial_metrics.get_financial_metrics(stock_symbol)
    
        # Display company name and logo
        col1, col2 = st.columns([3, 1])
        
        with col1:
            company_name = company_info.get('shortName', stock_symbol)
            st.header(company_name)
            st.subheader(company_info.get('sector', 'Sector not available') + " | " + company_info.get('industry', 'Industry not available'))
            
        with col2:
            # Show market status
            if is_indian:
                market = "NSE" if ".NS" in stock_symbol else "BSE" if ".BO" in stock_symbol else "Indian Market"
            else:
                market = company_info.get('exchange', 'US Market')
            
            st.info(f"Listed on: {market}")
    
        # Display stock data in the main content area
        
        # Create tabs for different sections
        overview_tab, charts_tab, financials_tab, news_tab, peer_comparison_tab = st.tabs([
            "Overview", "Charts", "Financials", "News & Sentiment", "Peer Comparison"
        ])
        
        # OVERVIEW TAB
        with overview_tab:
            st.subheader("Current Stock Summary")
            
            # Current price and daily change
            current_price = stock_data['Close'].iloc[-1]
            previous_close = stock_data['Close'].iloc[-2]
            price_change = current_price - previous_close
            price_change_pct = (price_change / previous_close) * 100
            
            # Format currency based on market
            if is_indian:
                price_str = f"₹{format_utils.format_number(current_price, decimal_places=2)}"
                change_str = f"{format_utils.format_number(price_change, decimal_places=2)} ({format_utils.format_number(price_change_pct, decimal_places=2)}%)"
            else:
                price_str = f"${format_utils.format_number(current_price, decimal_places=2)}"
                change_str = f"{format_utils.format_number(price_change, decimal_places=2)} ({format_utils.format_number(price_change_pct, decimal_places=2)}%)"
            
            # Color for price change
            if price_change >= 0:
                change_color = "green"
                change_icon = "↑"
            else:
                change_color = "red"
                change_icon = "↓"
            
            # Create three columns for price information
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Current Price", price_str)
            
            with col2:
                st.markdown(f"<h3 style='color: {change_color};'>{change_icon} {change_str}</h3>", unsafe_allow_html=True)
            
            with col3:
                # Combine the emoji with the current price's description
                sentiment_emoji = sentiment_tracker.get_sentiment_emoji(price_change_pct)
                st.markdown(f"<h3>{sentiment_emoji} Market Sentiment</h3>", unsafe_allow_html=True)
            
            # Create columns for key metrics
            st.subheader("Key Metrics")
            metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
            
            # Display metrics in the columns
            with metrics_col1:
                # Market Cap
                market_cap = company_info.get('marketCap', None)
                if market_cap:
                    if is_indian:
                        # Convert to Indian format (Crores)
                        market_cap_str = format_utils.format_large_number(market_cap, is_indian=True)
                        st.metric("Market Cap", market_cap_str)
                    else:
                        # Format in billions USD
                        market_cap_str = format_utils.format_large_number(market_cap)
                        st.metric("Market Cap", market_cap_str)
                else:
                    st.metric("Market Cap", "N/A")
                
                # P/E Ratio
                pe_ratio = company_info.get('trailingPE', None)
                if pe_ratio:
                    st.metric("P/E Ratio", format_utils.format_number(pe_ratio))
                else:
                    st.metric("P/E Ratio", "N/A")
            
            with metrics_col2:
                # 52-week high
                week_high = company_info.get('fiftyTwoWeekHigh', None)
                if week_high:
                    if is_indian:
                        week_high_str = f"₹{format_utils.format_number(week_high, decimal_places=2)}"
                    else:
                        week_high_str = f"${format_utils.format_number(week_high, decimal_places=2)}"
                    st.metric("52-Week High", week_high_str)
                else:
                    st.metric("52-Week High", "N/A")
                
                # EPS
                eps = company_info.get('trailingEps', None)
                if eps:
                    if is_indian:
                        eps_str = f"₹{format_utils.format_number(eps, decimal_places=2)}"
                    else:
                        eps_str = f"${format_utils.format_number(eps, decimal_places=2)}"
                    st.metric("EPS (TTM)", eps_str)
                else:
                    st.metric("EPS (TTM)", "N/A")
            
            with metrics_col3:
                # 52-week low
                week_low = company_info.get('fiftyTwoWeekLow', None)
                if week_low:
                    if is_indian:
                        week_low_str = f"₹{format_utils.format_number(week_low, decimal_places=2)}"
                    else:
                        week_low_str = f"${format_utils.format_number(week_low, decimal_places=2)}"
                    st.metric("52-Week Low", week_low_str)
                else:
                    st.metric("52-Week Low", "N/A")
                
                # Dividend Yield
                dividend_yield = company_info.get('dividendYield', None)
                if dividend_yield:
                    dividend_str = f"{format_utils.format_percent(dividend_yield)}"
                    st.metric("Dividend Yield", dividend_str)
                else:
                    st.metric("Dividend Yield", "N/A")
            
            with metrics_col4:
                # Volume
                volume = stock_data['Volume'].iloc[-1]
                if volume:
                    volume_str = format_utils.format_large_number(volume, decimal_places=0)
                    st.metric("Volume", volume_str)
                else:
                    st.metric("Volume", "N/A")
                
                # Beta
                beta = company_info.get('beta', None)
                if beta:
                    st.metric("Beta", format_utils.format_number(beta))
                else:
                    st.metric("Beta", "N/A")
            
            # Company description
            st.subheader("About the Company")
            company_description = company_info.get('longBusinessSummary', 'No description available.')
            st.write(company_description)
            
        # CHARTS TAB
        with charts_tab:
            st.subheader("Stock Price Chart")
            
            # Create time frame selection
            timeframe = st.radio(
                "Select Time Frame:",
                ["1 Month", "3 Months", "6 Months", "YTD", "1 Year", "3 Years", "5 Years", "Max"],
                horizontal=True
            )
            
            # Set period based on selection
            if timeframe == "1 Month":
                period = "1mo"
            elif timeframe == "3 Months":
                period = "3mo"
            elif timeframe == "6 Months":
                period = "6mo"
            elif timeframe == "YTD":
                period = "ytd"
            elif timeframe == "1 Year":
                period = "1y"
            elif timeframe == "3 Years":
                period = "3y"
            elif timeframe == "5 Years":
                period = "5y"
            else:
                period = "max"
            
            # Get stock data for the selected period
            chart_data = utils.get_stock_data(stock_symbol, period=period)
            
            # Chart type selection
            chart_type = st.radio(
                "Select Chart Type:",
                ["Line", "Candlestick", "OHLC"],
                horizontal=True
            )
            
            # Create the chart based on selection
            if chart_type == "Line":
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=chart_data.index,
                    y=chart_data['Close'],
                    mode='lines',
                    name='Close Price',
                    line=dict(color='royalblue', width=2)
                ))
                
                # Add a title and axis labels
                fig.update_layout(
                    title=f"{company_info.get('shortName', stock_symbol)} - {timeframe} Price Chart",
                    xaxis_title="Date",
                    yaxis_title="Price" + (" (₹)" if is_indian else " ($)"),
                    height=500,
                    template="plotly_white"
                )
                
            elif chart_type == "Candlestick":
                fig = go.Figure(data=[go.Candlestick(
                    x=chart_data.index,
                    open=chart_data['Open'],
                    high=chart_data['High'],
                    low=chart_data['Low'],
                    close=chart_data['Close'],
                    increasing_line_color='green',
                    decreasing_line_color='red'
                )])
                
                # Add a title and axis labels
                fig.update_layout(
                    title=f"{company_info.get('shortName', stock_symbol)} - {timeframe} Candlestick Chart",
                    xaxis_title="Date",
                    yaxis_title="Price" + (" (₹)" if is_indian else " ($)"),
                    height=500,
                    template="plotly_white"
                )
                
            else:  # OHLC
                fig = go.Figure(data=[go.Ohlc(
                    x=chart_data.index,
                    open=chart_data['Open'],
                    high=chart_data['High'],
                    low=chart_data['Low'],
                    close=chart_data['Close'],
                    increasing_line_color='green',
                    decreasing_line_color='red'
                )])
                
                # Add a title and axis labels
                fig.update_layout(
                    title=f"{company_info.get('shortName', stock_symbol)} - {timeframe} OHLC Chart",
                    xaxis_title="Date",
                    yaxis_title="Price" + (" (₹)" if is_indian else " ($)"),
                    height=500,
                    template="plotly_white"
                )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Add volume chart
            st.subheader("Volume Chart")
            
            # Create volume figure
            volume_fig = go.Figure()
            volume_fig.add_trace(go.Bar(
                x=chart_data.index,
                y=chart_data['Volume'],
                marker=dict(color='rgba(58, 71, 80, 0.6)'),
                name='Volume'
            ))
            
            # Update layout
            volume_fig.update_layout(
                title=f"{company_info.get('shortName', stock_symbol)} - {timeframe} Volume Chart",
                xaxis_title="Date",
                yaxis_title="Volume",
                height=300,
                template="plotly_white"
            )
            
            # Display the volume chart
            st.plotly_chart(volume_fig, use_container_width=True)
        
        # FINANCIALS TAB
        with financials_tab:
            # Create subtabs for different financial statements
            statement_tabs = st.tabs(["Valuation Metrics", "Balance Sheet", "Cash Flow", "Profit & Loss"])
            
            with statement_tabs[0]:
                st.subheader("Valuation Metrics")
                
                # Create 3 columns for displaying valuation metrics
                val_col1, val_col2, val_col3 = st.columns(3)
                
                with val_col1:
                    # Price-based ratios
                    st.markdown("**Price Ratios**")
                    # P/E Ratio (Trailing)
                    pe_ratio = metrics.get('valuation_metrics', {}).get('trailingPE')
                    if pe_ratio:
                        st.metric("P/E Ratio (TTM)", format_utils.format_number(pe_ratio))
                    else:
                        st.metric("P/E Ratio (TTM)", "N/A")
                    
                    # P/E Ratio (Forward)
                    forward_pe = metrics.get('valuation_metrics', {}).get('forwardPE')
                    if forward_pe:
                        st.metric("P/E Ratio (Forward)", format_utils.format_number(forward_pe))
                    else:
                        st.metric("P/E Ratio (Forward)", "N/A")
                    
                    # Price to Book
                    pb_ratio = metrics.get('valuation_metrics', {}).get('priceToBook')
                    if pb_ratio:
                        st.metric("Price to Book", format_utils.format_number(pb_ratio))
                    else:
                        st.metric("Price to Book", "N/A")
                    
                    # Price to Sales
                    ps_ratio = metrics.get('valuation_metrics', {}).get('priceToSalesTrailing12Months')
                    if ps_ratio:
                        st.metric("Price to Sales (TTM)", format_utils.format_number(ps_ratio))
                    else:
                        st.metric("Price to Sales (TTM)", "N/A")
                    
                    # PEG Ratio
                    peg_ratio = metrics.get('valuation_metrics', {}).get('pegRatio')
                    if peg_ratio:
                        st.metric("PEG Ratio", format_utils.format_number(peg_ratio))
                    else:
                        st.metric("PEG Ratio", "N/A")
                
                with val_col2:
                    # Profitability ratios
                    st.markdown("**Profitability**")
                    
                    # Profit Margin
                    profit_margin = metrics.get('key_ratios', {}).get('profitMargins')
                    if profit_margin:
                        st.metric("Profit Margin", format_utils.format_percent(profit_margin))
                    else:
                        st.metric("Profit Margin", "N/A")
                    
                    # Operating Margin
                    operating_margin = metrics.get('key_ratios', {}).get('operatingMargins')
                    if operating_margin:
                        st.metric("Operating Margin", format_utils.format_percent(operating_margin))
                    else:
                        st.metric("Operating Margin", "N/A")
                    
                    # ROE
                    roe = metrics.get('key_ratios', {}).get('returnOnEquity')
                    if roe:
                        st.metric("Return on Equity", format_utils.format_percent(roe))
                    else:
                        st.metric("Return on Equity", "N/A")
                    
                    # ROA
                    roa = metrics.get('key_ratios', {}).get('returnOnAssets')
                    if roa:
                        st.metric("Return on Assets", format_utils.format_percent(roa))
                    else:
                        st.metric("Return on Assets", "N/A")
                    
                    # ROCE (if available)
                    roce = metrics.get('key_ratios', {}).get('returnOnCapitalEmployed')
                    if roce:
                        st.metric("Return on Capital Employed", format_utils.format_percent(roce))
                    else:
                        st.metric("Return on Capital Employed", "N/A")
                
                with val_col3:
                    # Growth and other metrics
                    st.markdown("**Growth & Others**")
                    
                    # Revenue Growth
                    revenue_growth = metrics.get('performance_metrics', {}).get('revenueGrowth')
                    if revenue_growth:
                        st.metric("Revenue Growth (YoY)", format_utils.format_percent(revenue_growth))
                    else:
                        st.metric("Revenue Growth (YoY)", "N/A")
                    
                    # Earnings Growth
                    earnings_growth = metrics.get('performance_metrics', {}).get('earningsGrowth')
                    if earnings_growth:
                        st.metric("Earnings Growth (YoY)", format_utils.format_percent(earnings_growth))
                    else:
                        st.metric("Earnings Growth (YoY)", "N/A")
                    
                    # Current Ratio
                    current_ratio = metrics.get('key_ratios', {}).get('currentRatio')
                    if current_ratio:
                        st.metric("Current Ratio", format_utils.format_number(current_ratio))
                    else:
                        st.metric("Current Ratio", "N/A")
                    
                    # Debt to Equity
                    debt_to_equity = metrics.get('key_ratios', {}).get('debtToEquity')
                    if debt_to_equity:
                        st.metric("Debt to Equity", format_utils.format_number(debt_to_equity))
                    else:
                        st.metric("Debt to Equity", "N/A")
                    
                    # Dividend Yield
                    dividend_yield = metrics.get('key_ratios', {}).get('dividendYield')
                    if dividend_yield:
                        st.metric("Dividend Yield", format_utils.format_percent(dividend_yield))
                    else:
                        st.metric("Dividend Yield", "N/A")
            
            with statement_tabs[1]:
                st.subheader("Balance Sheet")
                
                # Display subtitle for Balance Sheet
                if is_indian:
                    st.write("Consolidated Figures in Rs. Crores / View Standalone")
                else:
                    st.write("Consolidated Figures in $ Millions / View Standalone")
                
                # Create a simple demo balance sheet that matches the screenshot format but with real data
                # We'll then fill it with data from Yahoo Finance
                raw_balance_sheet = utils.get_balance_sheet(stock_symbol)
                
                # Define our row labels exactly as in the screenshot
                row_labels = [
                    "Equity Capital", 
                    "Reserves", 
                    "Borrowings", 
                    "Other Liabilities",
                    "Total Liabilities",
                    "Fixed Assets",
                    "CWIP",  # Capital Work in Progress
                    "Investments",
                    "Other Assets",
                    "Total Assets"
                ]
                
                # Create column headers for 10 years (from current year back)
                current_year = pd.Timestamp.now().year
                year_labels = [f'Mar {y}' for y in range(current_year, current_year-10, -1)]
                
                # Create the balance sheet DataFrame
                balance_sheet_df = pd.DataFrame(index=row_labels)
                
                # Add year columns with default N/A values
                for year in year_labels:
                    balance_sheet_df[year] = "N/A"
                
                # Fill with actual data if available
                if not raw_balance_sheet.empty:
                    if is_indian:
                        st.info("Using data from Yahoo Finance (formatted for Indian market)")
                    else:
                        st.info("Using data from Yahoo Finance")
                        
                    # Map Yahoo Finance balance sheet items to our template
                    bs_mapping = {
                        "Common Stock": "Equity Capital",
                        "Retained Earnings": "Reserves",
                        "Long Term Debt": "Borrowings",
                        "Total Current Liabilities": "Other Liabilities",
                        "Total Liabilities Net Minority Interest": "Total Liabilities",
                        "Net PPE": "Fixed Assets",
                        "Construction In Progress": "CWIP",
                        "Investments": "Investments",
                        "Other Assets": "Other Assets",
                        "Total Assets": "Total Assets"
                    }
                    
                    # Convert column labels if they are timestamps
                    if isinstance(raw_balance_sheet.columns[0], pd.Timestamp):
                        formatted_columns = {}
                        for col in raw_balance_sheet.columns:
                            # Map to 'Mar YYYY' format
                            year_label = f"Mar {col.year}"
                            # Only use those within our target years
                            if year_label in year_labels:
                                formatted_columns[col] = year_label
                        
                        # Process each item in the raw balance sheet
                        for bs_item, our_label in bs_mapping.items():
                            if bs_item in raw_balance_sheet.index:
                                for orig_col, year_label in formatted_columns.items():
                                    value = raw_balance_sheet.loc[bs_item, orig_col]
                                    
                                    # Skip NaN values
                                    if pd.isna(value):
                                        continue
                                    
                                    # Convert to appropriate unit (Millions for USD, Crores for INR)
                                    divisor = 10000000 if is_indian else 1000000  # 1 crore = 10 million
                                    value = value / divisor
                                    
                                    # Format with commas and store in our DataFrame
                                    balance_sheet_df.loc[our_label, year_label] = f"{int(value):,}"
                
                # Display the balance sheet
                st.write(balance_sheet_df, use_container_width=True)
        
            with statement_tabs[2]:
                st.subheader("Cash Flow")
                
                # Display subtitle for Cash Flow
                if is_indian:
                    st.write("Consolidated Figures in Rs. Crores / View Standalone")
                else:
                    st.write("Consolidated Figures in $ Millions / View Standalone")
                    
                # Create a function to display cash flow statement
                def display_cash_flow(stock_symbol, is_indian=False):
                    try:
                        # First try to get data from Screener.in for Indian stocks
                        screener_data_available = False
                        if is_indian:
                            with st.spinner("Fetching cash flow data from Screener.in..."):
                                # Fetch data from Screener.in
                                data = screener_integration.fetch_data(stock_symbol)
                                
                                if data:
                                    # Format the cash flow data
                                    formatted_cf = screener_integration.format_cash_flow(data, is_indian=True)
                                    
                                    if not formatted_cf.empty:
                                        # Success message
                                        st.success("Using Screener.in cash flow data")
                                        
                                        # Define key rows we want to highlight
                                        important_rows = [
                                            "Cash from Operating Activity",
                                            "Cash from Investing Activity",
                                            "Cash from Financing Activity",
                                            "Net Cash Flow"
                                        ]
                                        
                                        # Create HTML for the cash flow table with styling
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
                                        .total-row {
                                            font-weight: bold;
                                            background-color: #f9f9f9;
                                        }
                                        </style>
                                        """, unsafe_allow_html=True)
                                        
                                        # Create HTML table with custom styling for important rows
                                        html_table = formatted_cf.to_html(classes='dataframe', escape=False)
                                        
                                        # Add special styling for important rows
                                        for row in important_rows:
                                            if row in formatted_cf.index:
                                                html_table = html_table.replace(f'<tr>\n      <th>{row}</th>', 
                                                                              f'<tr class="total-row">\n      <th>{row}</th>')
                                        
                                        # Display the table
                                        st.write(html_table, unsafe_allow_html=True)
                                        screener_data_available = True
                                        return
                        
                        # If Screener data is not available or it's not an Indian stock, use Yahoo Finance
                        if not screener_data_available:
                            # Get data from Yahoo Finance
                            ticker = yf.Ticker(stock_symbol)
                            cash_flow = ticker.cashflow
                            
                            if cash_flow is not None and not cash_flow.empty:
                                st.info("Using Yahoo Finance cash flow data")
                                
                                # Define row labels matching the professional format
                                row_labels = [
                                    "Cash from Operating Activity",
                                    "Profit from operations",
                                    "Working capital changes",
                                    "Direct taxes",
                                    "Cash from Investing Activity",
                                    "Fixed assets",
                                    "Investments", 
                                    "Cash from Financing Activity",
                                    "Borrowings",
                                    "Dividend",
                                    "Net Cash Flow"
                                ]
                                
                                # Create DataFrame with our standard format
                                formatted_cf = pd.DataFrame(index=row_labels)
                                
                                # Process columns
                                for col in cash_flow.columns:
                                    col_name = col
                                    if isinstance(col, pd.Timestamp):
                                        col_name = col.strftime('%b %Y')
                                    
                                    formatted_cf[col_name] = None
                                    
                                    # Map values from Yahoo Finance to our standard format
                                    if 'Total Cash From Operating Activities' in cash_flow.index:
                                        value = cash_flow.loc['Total Cash From Operating Activities', col]
                                        if pd.notna(value):
                                            # Convert to crores/millions
                                            value = value / (10000000 if is_indian else 1000000)
                                            formatted_cf.loc['Cash from Operating Activity', col_name] = value
                                            
                                    if 'Total Cashflows From Investing Activities' in cash_flow.index:
                                        value = cash_flow.loc['Total Cashflows From Investing Activities', col]
                                        if pd.notna(value):
                                            # Convert to crores/millions
                                            value = value / (10000000 if is_indian else 1000000)
                                            formatted_cf.loc['Cash from Investing Activity', col_name] = value
                                            
                                    if 'Total Cash From Financing Activities' in cash_flow.index:
                                        value = cash_flow.loc['Total Cash From Financing Activities', col]
                                        if pd.notna(value):
                                            # Convert to crores/millions
                                            value = value / (10000000 if is_indian else 1000000)
                                            formatted_cf.loc['Cash from Financing Activity', col_name] = value
                                            
                                    # Calculate Net Cash Flow if we have all components
                                    if (pd.notna(formatted_cf.loc['Cash from Operating Activity', col_name]) and
                                        pd.notna(formatted_cf.loc['Cash from Investing Activity', col_name]) and
                                        pd.notna(formatted_cf.loc['Cash from Financing Activity', col_name])):
                                        
                                        net_value = (formatted_cf.loc['Cash from Operating Activity', col_name] +
                                                    formatted_cf.loc['Cash from Investing Activity', col_name] +
                                                    formatted_cf.loc['Cash from Financing Activity', col_name])
                                        
                                        formatted_cf.loc['Net Cash Flow', col_name] = net_value
                                
                                # Format values for display
                                display_cf = formatted_cf.copy()
                                for col in display_cf.columns:
                                    for idx in display_cf.index:
                                        value = display_cf.loc[idx, col]
                                        
                                        if pd.isna(value) or value is None:
                                            display_cf.loc[idx, col] = "N/A"
                                        else:
                                            # Format financial values with commas
                                            try:
                                                display_cf.loc[idx, col] = f"{int(round(value)):,}"
                                            except:
                                                display_cf.loc[idx, col] = "N/A"
                                
                                # Create HTML for the cash flow table with styling
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
                                .total-row {
                                    font-weight: bold;
                                    background-color: #f9f9f9;
                                }
                                </style>
                                """, unsafe_allow_html=True)
                                
                                # Create HTML table with custom styling for important rows
                                html_table = display_cf.to_html(classes='dataframe', escape=False)
                                
                                # Add special styling for important rows
                                important_rows = [
                                    "Cash from Operating Activity",
                                    "Cash from Investing Activity",
                                    "Cash from Financing Activity",
                                    "Net Cash Flow"
                                ]
                                
                                for row in important_rows:
                                    if row in display_cf.index:
                                        html_table = html_table.replace(f'<tr>\n      <th>{row}</th>', 
                                                                      f'<tr class="total-row">\n      <th>{row}</th>')
                                
                                # Display the table
                                st.write(html_table, unsafe_allow_html=True)
                            else:
                                st.warning("Cash flow data not available for this stock.")
                    except Exception as e:
                        st.error(f"Error displaying cash flow: {str(e)}")
                        
                        # Fallback to raw data
                        try:
                            ticker = yf.Ticker(stock_symbol)
                            raw_cf = ticker.cashflow
                            
                            if raw_cf is not None and not raw_cf.empty:
                                st.write("Showing raw cash flow data:")
                                # Format column names if timestamps
                                if isinstance(raw_cf.columns[0], pd.Timestamp):
                                    raw_cf.columns = [col.strftime('%b %Y') for col in raw_cf.columns]
                                st.dataframe(raw_cf, use_container_width=True)
                            else:
                                st.write("Cash flow data not available for this stock.")
                        except Exception as fallback_error:
                            st.error(f"Could not display fallback data: {fallback_error}")
                            st.write("Cash flow data not available for this stock.")
                
                # Call the function to display cash flow
                display_cash_flow(stock_symbol, is_indian)
            
            with statement_tabs[3]:
                st.subheader("Profit & Loss")
                
                # Display subtitle for P&L Statement
                if is_indian:
                    st.write("Consolidated Figures in Rs. Crores")
                else:
                    st.write("Consolidated Figures in $ Millions")
                    
                # Create a function to display the P&L statement
                def display_pl_statement(stock_symbol, is_indian=False):
                    try:
                        # First try to get data from Screener.in for Indian stocks
                        screener_data_available = False
                        if is_indian:
                            try:
                                with st.spinner("Fetching financial data from Screener.in..."):
                                    # Fetch all financial data from Screener.in
                                    screener_data = screener_integration.fetch_data(stock_symbol)
                                    
                                    if screener_data and isinstance(screener_data, dict):
                                        # Format the P&L data
                                        formatted_df = screener_integration.format_pl_statement(screener_data, is_indian=True)
                                        
                                        if not formatted_df.empty:
                                            st.success("Using financial data from Screener.in")
                                            screener_data_available = True
                                            
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
                                            }
                                            </style>
                                            """, unsafe_allow_html=True)
                                            
                                            # Display the P&L table with real data
                                            st.write(formatted_df.to_html(classes='dataframe', escape=False), unsafe_allow_html=True)
                                            
                                            # Don't need to use Yahoo Finance
                                            return
                            except Exception as e:
                                st.warning(f"Could not fetch data from Screener.in: {str(e)}")
                                st.info("Falling back to Yahoo Finance data")
                        
                        # If Screener data is not available or it's not an Indian stock, use Yahoo Finance
                        if not screener_data_available:
                            try:
                                # Get stock data from Yahoo Finance
                                ticker = yf.Ticker(stock_symbol)
                                
                                # For proper P&L table, we need to gather info from different sources
                                income_data = ticker.income_stmt
                                
                                # If no income statement is available, fallback to financials
                                if income_data is None or income_data.empty:
                                    income_data = ticker.financials
                                    
                                # Additional fallback to quarterly data if annual data is not available
                                if income_data is None or income_data.empty:
                                    income_data = ticker.quarterly_income_stmt
                                    if income_data is None or income_data.empty:
                                        income_data = ticker.quarterly_financials
                                        
                                st.success(f"Successfully retrieved financial data for {stock_symbol}")
                            except Exception as e:
                                st.error(f"Error retrieving financial data: {str(e)}")
                                income_data = None
                            
                            # If still no data, show a message and return
                            if income_data is None or income_data.empty:
                                st.warning("No financial data available from Yahoo Finance for this stock.")
                                return
                            
                            st.info("Using Yahoo Finance financial data")
                            
                            # Units conversion factor - Millions for USD, Crores for INR
                            divisor = 10000000 if is_indian else 1000000
                            
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
                            
                            # Map Yahoo Finance keys to our P&L rows
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
                            formatted_df = pd.DataFrame(index=pl_rows)
                            
                            # Process each year column
                            for col in income_data.columns:
                                # Create an empty column 
                                formatted_df[col] = None
                                
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
                                        formatted_df.loc[target_row, col] = value
                                
                                # Calculate any missing values
                                
                                # If we have Sales but no Operating Profit, calculate it
                                if formatted_df.loc["Sales", col] is not None and formatted_df.loc["Operating Profit", col] is None:
                                    if formatted_df.loc["Expenses", col] is not None:
                                        formatted_df.loc["Operating Profit", col] = formatted_df.loc["Sales", col] - formatted_df.loc["Expenses", col]
                                
                                # If we have Sales and Operating Profit but no Expenses, calculate it
                                if formatted_df.loc["Sales", col] is not None and formatted_df.loc["Operating Profit", col] is not None:
                                    if formatted_df.loc["Expenses", col] is None:
                                        formatted_df.loc["Expenses", col] = formatted_df.loc["Sales", col] - formatted_df.loc["Operating Profit", col]
                                
                                # Calculate OPM % if we have both Sales and Operating Profit
                                if formatted_df.loc["Sales", col] is not None and formatted_df.loc["Operating Profit", col] is not None:
                                    if formatted_df.loc["Sales", col] != 0:
                                        formatted_df.loc["OPM %", col] = (formatted_df.loc["Operating Profit", col] / formatted_df.loc["Sales", col]) * 100
                                
                                # Calculate Tax % if we have both Tax and Profit before tax
                                if formatted_df.loc["Tax %", col] is not None and formatted_df.loc["Profit before tax", col] is not None:
                                    if isinstance(formatted_df.loc["Tax %", col], (int, float)) and isinstance(formatted_df.loc["Profit before tax", col], (int, float)):
                                        if formatted_df.loc["Profit before tax", col] != 0:
                                            # Calculate actual tax percentage
                                            formatted_df.loc["Tax %", col] = abs(formatted_df.loc["Tax %", col] / formatted_df.loc["Profit before tax", col] * 100)
                            
                            # Format values for display
                            display_df = formatted_df.copy()
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
                            }
                            </style>
                            """, unsafe_allow_html=True)
                            
                            # Display the P&L table with real data
                            st.write(display_df.to_html(classes='dataframe', escape=False), unsafe_allow_html=True)
                            
                    except Exception as e:
                        st.error(f"Error displaying P&L statement: {str(e)}")
                        
                        try:
                            # Fallback to displaying raw income statement
                            ticker = yf.Ticker(stock_symbol)
                            raw_income = ticker.financials
                            
                            if raw_income is not None and not raw_income.empty:
                                st.write("Showing raw financial data from Yahoo Finance:")
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
                display_pl_statement(stock_symbol, is_indian)
        
        # NEWS TAB
        with news_tab:
            st.subheader("Latest News")
            
            # Get news
            news_items = stock_news.get_news(stock_symbol)
            
            if not news_items:
                st.warning("No recent news available for this stock.")
            else:
                # Display news as expandable cards
                for i, news in enumerate(news_items):
                    # Get the date from the correct key (our get_news function uses 'date')
                    news_date = news.get('date', 'Recent')
                    
                    with st.expander(f"{news['title']} ({news_date})"):
                        if 'summary' in news and news['summary']:
                            st.write(news['summary'])
                        else:
                            st.write(news.get('text', "No summary available."))
                        
                        # Use publisher instead of source (our get_news function uses 'publisher')
                        st.write(f"Source: {news.get('publisher', 'Unknown')}")
                        
                        # Use link instead of url (our get_news function uses 'link')
                        if 'link' in news and news['link']:
                            st.write(f"[Read full article]({news['link']})")
            
            # Sentiment Analysis
            st.subheader("Market Sentiment Analysis")
            
            # Get sentiment data (this will use OpenAI for natural language processing)
            sentiment_data = stock_news.analyze_news_sentiment(stock_symbol)
            
            # Display sentiment score
            if sentiment_data and 'overall_score' in sentiment_data:
                # Get the score
                score = sentiment_data['overall_score']
                
                # Determine color
                if score >= 0.7:
                    color = "green"
                    label = "Bullish"
                elif score >= 0.5:
                    color = "lightgreen"
                    label = "Slightly Bullish"
                elif score >= 0.4:
                    color = "gray"
                    label = "Neutral"
                elif score >= 0.2:
                    color = "orange"
                    label = "Slightly Bearish"
                else:
                    color = "red"
                    label = "Bearish"
                
                # Create custom progress bar
                st.markdown(f"""
                <div style="width:100%; background-color:#f0f0f0; height:30px; border-radius:5px; margin-bottom:10px;">
                    <div style="width:{score*100}%; background-color:{color}; height:30px; border-radius:5px; text-align:center; line-height:30px; color:white;">
                        {score*100:.1f}%
                    </div>
                </div>
                <p style="text-align:center; font-weight:bold; color:{color};">{label}</p>
                """, unsafe_allow_html=True)
                
                # Display top positive and negative factors
                if 'positive_factors' in sentiment_data and sentiment_data['positive_factors']:
                    st.subheader("Positive Factors")
                    for factor in sentiment_data['positive_factors']:
                        st.markdown(f"- {factor}")
                
                if 'negative_factors' in sentiment_data and sentiment_data['negative_factors']:
                    st.subheader("Negative Factors")
                    for factor in sentiment_data['negative_factors']:
                        st.markdown(f"- {factor}")
            else:
                st.warning("Sentiment analysis not available for this stock.")
        
        # PEER COMPARISON TAB
        with peer_comparison_tab:
            st.subheader("Peer Comparison")
            
            # Get sector information
            sector = company_info.get('sector', None)
            
            if not sector:
                st.warning("Sector information not available for this stock. Cannot perform peer comparison.")
            else:
                # Get peer symbols
                peer_symbols = utils.get_peer_symbols(stock_symbol, sector, is_indian)
                
                if not peer_symbols:
                    st.warning("No peer stocks found for comparison.")
                else:
                    # Allow user to select which peers to compare
                    selected_peers = st.multiselect(
                        "Select peers for comparison:",
                        peer_symbols,
                        default=peer_symbols[:4]  # Default to first 4 peers
                    )
                    
                    if selected_peers:
                        # Add the main stock to the comparison
                        comparison_symbols = [stock_symbol] + selected_peers
                        
                        # Get comparison data
                        comparison_data = peer_comparison.get_peer_data(stock_symbol, selected_peers, is_indian)
                        
                        if comparison_data is not None and not comparison_data.empty:
                            # Plot key metrics comparison
                            st.subheader("Key Financial Metrics Comparison")
                            
                            # Select metrics to compare
                            metrics_to_compare = st.multiselect(
                                "Select metrics to compare:",
                                [
                                    "P/E Ratio", "Price to Book", "Price to Sales", "ROE",
                                    "Operating Margin", "Net Margin", "Debt to Equity",
                                    "Dividend Yield", "Market Cap", "Beta"
                                ],
                                default=["P/E Ratio", "Price to Book", "ROE", "Dividend Yield"]
                            )
                            
                            if metrics_to_compare:
                                # Create subplots for each metric
                                fig = make_subplots(
                                    rows=len(metrics_to_compare),
                                    cols=1,
                                    subplot_titles=metrics_to_compare,
                                    vertical_spacing=0.1
                                )
                                
                                # Add data for each metric
                                for i, metric in enumerate(metrics_to_compare):
                                    metric_col = metric.replace(" ", "_").lower()
                                    
                                    # Check if the metric is in the comparison data
                                    if metric_col in comparison_data.columns:
                                        # Sort the data for better visualization
                                        sorted_data = comparison_data.sort_values(by=metric_col)
                                        
                                        # Highlight the main stock
                                        colors = ['royalblue'] * len(sorted_data)
                                        for j, symbol in enumerate(sorted_data['Symbol']):
                                            if symbol == stock_symbol:
                                                colors[j] = 'orange'
                                        
                                        # Add horizontal bar chart
                                        fig.add_trace(
                                            go.Bar(
                                                y=sorted_data['Company'],
                                                x=sorted_data[metric_col],
                                                orientation='h',
                                                marker_color=colors,
                                                text=sorted_data[metric_col].apply(
                                                    lambda x: f"{x:.2f}"
                                                ),
                                                textposition='auto',
                                                name=metric
                                            ),
                                            row=i+1,
                                            col=1
                                        )
                                        
                                        # Update layout for this subplot
                                        fig.update_yaxes(title_text="", row=i+1, col=1)
                                        fig.update_xaxes(title_text=metric, row=i+1, col=1)
                                
                                # Update overall layout
                                fig.update_layout(
                                    height=250 * len(metrics_to_compare),
                                    showlegend=False,
                                    template="plotly_white"
                                )
                                
                                # Display the comparison chart
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Display comparative price performance
                            st.subheader("Price Performance Comparison")
                            
                            # Time period selection
                            time_period = st.radio(
                                "Select time period:",
                                ["1 Month", "3 Months", "6 Months", "1 Year", "YTD"],
                                horizontal=True
                            )
                            
                            # Map selection to period
                            period_map = {
                                "1 Month": "1mo",
                                "3 Months": "3mo",
                                "6 Months": "6mo",
                                "1 Year": "1y",
                                "YTD": "ytd"
                            }
                            period = period_map.get(time_period, "1mo")
                            
                            # Create normalized price chart
                            fig = go.Figure()
                            
                            # First date for normalization baseline
                            baseline_date = None
                            
                            # Add each stock to the chart
                            for symbol in comparison_symbols:
                                # Get historical data
                                hist_data = utils.get_stock_data(symbol, period=period)
                                
                                if not hist_data.empty:
                                    # Set baseline date if not set
                                    if baseline_date is None:
                                        baseline_date = hist_data.index[0]
                                    
                                    # Calculate relative performance (normalized to 100)
                                    baseline_price = hist_data.loc[baseline_date, 'Close']
                                    normalized_prices = (hist_data['Close'] / baseline_price) * 100
                                    
                                    # Highlight main stock with thicker line
                                    if symbol == stock_symbol:
                                        line_width = 3
                                        line_color = 'orange'
                                    else:
                                        line_width = 1.5
                                        line_color = None  # Use default color cycle
                                    
                                    # Get company name for the legend
                                    company_name = utils.get_company_name(symbol)
                                    if not company_name:
                                        company_name = symbol
                                    
                                    # Add line to chart
                                    fig.add_trace(go.Scatter(
                                        x=hist_data.index,
                                        y=normalized_prices,
                                        mode='lines',
                                        name=company_name,
                                        line=dict(width=line_width, color=line_color)
                                    ))
                            
                            # Update layout
                            fig.update_layout(
                                title=f"Relative Price Performance (Base = 100)",
                                xaxis_title="Date",
                                yaxis_title="Normalized Price",
                                height=500,
                                template="plotly_white",
                                hovermode="x unified"
                            )
                            
                            # Add baseline reference
                            fig.add_shape(
                                type="line",
                                x0=baseline_date,
                                y0=100,
                                x1=hist_data.index[-1],
                                y1=100,
                                line=dict(color="gray", width=1, dash="dash")
                            )
                            
                            # Display the chart
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Display comparative metrics in a table
                            st.subheader("Comparative Financial Metrics")
                            
                            # Format the comparison data for display
                            display_cols = ['Company']
                            rename_map = {
                                'pe_ratio': 'P/E Ratio',
                                'price_to_book': 'P/B Ratio',
                                'price_to_sales': 'P/S Ratio',
                                'roe': 'ROE %',
                                'operating_margin': 'Op. Margin %',
                                'net_margin': 'Net Margin %',
                                'debt_to_equity': 'D/E Ratio',
                                'dividend_yield': 'Div. Yield %',
                                'market_cap': 'Market Cap',
                                'beta': 'Beta'
                            }
                            
                            display_metrics = []
                            for col in comparison_data.columns:
                                if col in rename_map:
                                    display_metrics.append(col)
                                    
                            # Add the metrics columns to display columns
                            display_cols.extend(display_metrics)
                            
                            # Create a copy for display
                            display_df = comparison_data[display_cols].copy()
                            
                            # Rename columns to more readable names
                            display_df = display_df.rename(columns=rename_map)
                            
                            # Format the values
                            for col in display_df.columns:
                                if col != 'Company':
                                    # Market Cap needs special formatting
                                    if col == 'Market Cap':
                                        display_df[col] = display_df[col].apply(
                                            lambda x: format_utils.format_large_number(x, is_indian=is_indian)
                                        )
                                    # Percentage metrics
                                    elif any(pct in col for pct in ['ROE', 'Margin', 'Yield']):
                                        display_df[col] = display_df[col].apply(
                                            lambda x: format_utils.format_percent(x)
                                        )
                                    # Other numeric metrics with 2 decimal places
                                    else:
                                        display_df[col] = display_df[col].apply(
                                            lambda x: format_utils.format_number(x, decimal_places=2)
                                        )
                            
                            # Highlight the main stock
                            def highlight_main_stock(row):
                                if row['Company'] == utils.get_company_name(stock_symbol):
                                    return ['background-color: #ffedcc'] * len(row)
                                return [''] * len(row)
                            
                            # Apply highlighting
                            styled_df = display_df.style.apply(highlight_main_stock, axis=1)
                            
                            # Display the table
                            st.dataframe(styled_df, use_container_width=True)
                        else:
                            st.warning("Could not fetch comparison data for the selected peers.")
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try another stock symbol or check your internet connection.")