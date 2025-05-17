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
import stock_prediction

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
        "Consumer Cyclical": ["TATAMOTORS.NS", "M&M.NS", "MARUTI.NS", "HEROMOTOCO.NS"],
        "Communications": ["BHARTIARTL.NS", "IDEA.NS", "TATACOMM.NS", "INDIAMART.NS"],
        "Energy": ["RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS"],
        "Healthcare": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS"]
    }
    
    # Default to technology if sector not found
    if sector not in peers:
        sector = "Technology"
    
    # Get peers for the sector
    sector_peers = peers[sector].copy()
    
    # Remove the current symbol if it's in the list
    if symbol in sector_peers:
        sector_peers.remove(symbol)
    
    # Return up to 4 peers
    return sector_peers[:4]

# Page configuration
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

# Initialize session state for watchlist integration
if 'selected_stock' not in st.session_state:
    st.session_state['selected_stock'] = None

# Title and description
st.title("MoneyMitra - Your Financial Mitra")
st.write("Your Financial Mitra that brings all the relevant detailed financial analysis data in one place for you to make your investment decisions easy, quick but well informed")

# Dashboard header with stock market image
col1, col2 = st.columns([1, 3])
with col1:
    st.image("https://pixabay.com/get/g738a334be08e7073603a68932df55ea8c27b445f40ba8f4b3e42a2629cc1dfa830b85a80523ec7bf5bc7932ec2b0ad49bc5bab7cc138fa443e41f23d1313bccb_1280.jpg", 
             use_container_width=True)
with col2:
    st.write("""
    This dashboard provides real-time financial data visualization and metrics powered by Yahoo Finance. 
    Get insights on stock performance, financial ratios, and company overviews in one place.
    """)
    
    # Input for stock symbol
    col_symbol, col_period = st.columns([1, 1])
    
    with col_symbol:
        # Check if a stock was selected from the watchlist
        initial_value = st.session_state.get('selected_stock', 'RELIANCE.NS')
        # Make sure initial_value is not None 
        if initial_value is None:
            initial_value = 'RELIANCE.NS'
        stock_symbol = st.text_input("Enter Stock Symbol (e.g., RELIANCE.NS, TATAMOTORS.NS, INFY.NS)", initial_value).upper()
        # Reset the selected stock after use
        if st.session_state.get('selected_stock'):
            st.session_state['selected_stock'] = None
    
    with col_period:
        time_period = st.selectbox(
            "Select Time Period",
            ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        )
    
# Load data with status indicator
with st.spinner(f"Loading data for {stock_symbol}..."):
    try:
        # Check if it's an Indian stock
        is_indian = indian_markets.is_indian_symbol(stock_symbol) or '.NS' in stock_symbol or '.BO' in stock_symbol
        
        if is_indian:
            # Get Indian stock data
            stock_data = indian_markets.get_indian_stock_data(stock_symbol, time_period)
            
            # Get Indian company info
            company_info = indian_markets.get_indian_company_info(stock_symbol)
            
            # Get financial metrics (using standard financial_metrics for now)
            financial_data = financial_metrics.get_financial_metrics(stock_symbol)
            
            # Set flag for Indian stock
            is_indian_stock = True
        else:
            # Get regular stock data
            stock_data = utils.get_stock_data(stock_symbol, time_period)
            
            # Get company info
            company_info = utils.get_company_info(stock_symbol)
            
            # Get financial metrics
            financial_data = financial_metrics.get_financial_metrics(stock_symbol)
            
            # Set flag for non-Indian stock
            is_indian_stock = False
        
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
    # Create tabs for main sections
    main_tabs = st.tabs([
        "📊 Dashboard Overview", 
        "🔍 Detailed Analysis", 
        "💰 Financial Statements", 
        "📈 Performance Analysis",
        "📋 Research Report",
        "📰 Latest News",
        "⭐ Watchlists"
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
                if is_indian_stock:
                    # For Indian stocks, show price in Rupees
                    price_value = stock_data['Close'].iloc[-1]
                    price_change = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100
                    st.metric("Current Price", f"₹{price_value:.2f}", f"{price_change:.2f}%")
                else:
                    st.metric("Current Price", f"${stock_data['Close'].iloc[-1]:.2f}", 
                            f"{((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100:.2f}%")
            with metrics_row[1]:
                if is_indian_stock:
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
                if is_indian_stock:
                    low = company_info.get('fiftyTwoWeekLow')
                    high = company_info.get('fiftyTwoWeekHigh')
                    if all(isinstance(val, (int, float)) for val in [low, high]):
                        st.metric("52W Range", f"₹{low:.2f} - ₹{high:.2f}")
                    else:
                        st.metric("52W Range", "N/A")
                else:
                    st.metric("52W Range", f"${company_info.get('fiftyTwoWeekLow', 'N/A'):.2f} - ${company_info.get('fiftyTwoWeekHigh', 'N/A'):.2f}" if all(isinstance(company_info.get(x), (int, float)) for x in ['fiftyTwoWeekLow', 'fiftyTwoWeekHigh']) else "N/A")
        
        with overview_col2:
            st.image("https://pixabay.com/get/g87690ed3ce15cbccbebd694d12edf27c88cc096992c61c05e3d858515dbb583c5f8adf1645f81df6bdd0f6982a4a408fdb2f409ed8cc38f390680a33e567f751_1280.jpg", 
                    use_container_width=True)
            
            sector = company_info.get('sector', 'N/A')
            industry = company_info.get('industry', 'N/A')
            website = company_info.get('website', 'N/A')
            
            st.write(f"**Sector:** {sector}")
            st.write(f"**Industry:** {industry}")
            
            if is_indian_stock:
                # Show NSE/BSE specific information
                exchange = "NSE" if ".NS" in stock_symbol else "BSE" if ".BO" in stock_symbol else company_info.get('exchange', 'N/A')
                st.write(f"**Exchange:** {exchange}")
                st.write(f"**Currency:** INR (₹)")
                
                # Add additional Indian stock information if available
                if 'nse_totalTradedVolume' in company_info:
                    st.write(f"**Trading Volume:** {company_info['nse_totalTradedVolume']:,}")
                if 'nse_pChange' in company_info:
                    st.write(f"**% Change:** {company_info['nse_pChange']}%")
            else:
                st.write(f"**Exchange:** {company_info.get('exchange', 'N/A')}")
                st.write(f"**Currency:** {company_info.get('currency', 'N/A')}")
            
            if website != 'N/A':
                st.write(f"**Website:** [{website}]({website})")
        
        # Chart section
        st.header("Price History")
        
        chart_tabs = st.tabs(["Line Chart", "Candlestick Chart", "Volume Analysis"])
        
        with chart_tabs[0]:
            if is_indian_stock:
                # Use INR currency for Indian stocks
                fig = utils.create_line_chart(stock_data, currency="₹")
            else:
                fig = utils.create_line_chart(stock_data)
            st.plotly_chart(fig, use_container_width=True)
        
        with chart_tabs[1]:
            if is_indian_stock:
                # Use INR currency for Indian stocks
                fig = utils.create_candlestick_chart(stock_data, currency="₹")
            else:
                fig = utils.create_candlestick_chart(stock_data)
            st.plotly_chart(fig, use_container_width=True)
        
        with chart_tabs[2]:
            fig = utils.create_volume_chart(stock_data)
            st.plotly_chart(fig, use_container_width=True)
            
        # Add Indian market benchmark comparison if it's an Indian stock
        if is_indian_stock:
            st.subheader("Benchmark Comparison")
            
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
                                name="NIFTY 50",
                                line=dict(color='firebrick')
                            ))
                            
                            fig.update_layout(
                                title=f"{stock_symbol} vs NIFTY 50 (Normalized to 100)",
                                xaxis_title="Date",
                                yaxis_title="Normalized Value",
                                legend_title="Comparison",
                                height=500
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Performance comparison
                            stock_perf = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100
                            nifty_perf = ((nifty_data['Close'].iloc[-1] / nifty_data['Close'].iloc[0]) - 1) * 100
                            
                            st.write(f"**{stock_symbol} Performance:** {stock_perf:.2f}%")
                            st.write(f"**NIFTY 50 Performance:** {nifty_perf:.2f}%")
                            st.write(f"**Difference:** {stock_perf - nifty_perf:.2f}%")
                    except Exception as e:
                        st.error(f"Failed to load NIFTY data: {str(e)}")
            
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
                                name="SENSEX",
                                line=dict(color='firebrick')
                            ))
                            
                            fig.update_layout(
                                title=f"{stock_symbol} vs SENSEX (Normalized to 100)",
                                xaxis_title="Date",
                                yaxis_title="Normalized Value",
                                legend_title="Comparison",
                                height=500
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Performance comparison
                            stock_perf = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100
                            sensex_perf = ((sensex_data['Close'].iloc[-1] / sensex_data['Close'].iloc[0]) - 1) * 100
                            
                            st.write(f"**{stock_symbol} Performance:** {stock_perf:.2f}%")
                            st.write(f"**SENSEX Performance:** {sensex_perf:.2f}%")
                            st.write(f"**Difference:** {stock_perf - sensex_perf:.2f}%")
                    except Exception as e:
                        st.error(f"Failed to load SENSEX data: {str(e)}")
    
    # Detailed Analysis Tab
    with main_tabs[1]:
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
                
        # Business Analysis
        st.header("Business Analysis")
        
        # Key milestones
        st.subheader("Key Milestones")
        st.write("Information about the company's key milestones, product launches, and strategic initiatives.")
        
        # SWOT Analysis
        st.subheader("SWOT Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Strengths**")
            if sector == "Technology":
                st.write("- Strong brand recognition")
                st.write("- Diversified product portfolio")
                st.write("- Robust research and development")
            else:
                st.write("- Industry leader position")
                st.write("- Strong financial position")
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
    
    # Performance Analysis Tab
    with main_tabs[3]:
        st.header("Performance Analysis")
        
        # Add stock price prediction with animated trend line and confidence intervals
        st.subheader("Price Prediction Analysis")
        # Get company name for the chart title
        company_name = company_info.get('shortName', stock_symbol)
        # Display the stock prediction section with animated chart
        stock_prediction.display_prediction_section(stock_symbol, stock_data, company_name, is_indian_stock)
        
        # Historical Performance
        st.subheader("Historical Performance")
        
        # Year-to-date performance
        current_year = datetime.now().year
        ytd_start = datetime(current_year, 1, 1)
        # Convert index to datetime if it's not already
        if not isinstance(stock_data.index, pd.DatetimeIndex):
            stock_data.index = pd.to_datetime(stock_data.index)
        # Use datetime objects without timezone for comparison
        # Convert any timezone-aware datetimes to naive datetimes for comparison
        naive_dates = stock_data.index.tz_localize(None) if stock_data.index.tz is not None else stock_data.index
        ytd_data = stock_data[naive_dates >= ytd_start]
        ytd_performance = 0.0
        if not ytd_data.empty:
            ytd_performance = ((ytd_data['Close'].iloc[-1] / ytd_data['Close'].iloc[0]) - 1) * 100
            st.metric("Year-to-Date Performance", f"{ytd_performance:.2f}%")
        
        # Volatility and Risk Metrics
        st.subheader("Volatility and Risk Metrics")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Beta", f"{company_info.get('beta', 'N/A'):.2f}" if isinstance(company_info.get('beta'), (int, float)) else "N/A")
        with col2:
            # Calculate standard deviation of daily returns
            if len(stock_data) > 30:
                daily_returns = stock_data['Close'].pct_change().dropna()
                st.metric("Daily Volatility (30 Day)", f"{daily_returns.tail(30).std() * 100:.2f}%")
        
        # Peer Comparison
        st.subheader("Peer Comparison")
        if sector != 'N/A':
            st.write(f"Comparison with other companies in the {sector} sector:")
            
            try:
                # Import peer comparison module for real-time data
                import peer_comparison
                
                # Show a loading spinner while fetching real-time comparison data
                with st.spinner("Fetching real-time peer comparison data..."):
                    # Get real sector peers based on the company's sector
                    peer_symbols = peer_comparison.get_sector_peers(stock_symbol, sector)
                    
                    # Get real-time financial data for the peer comparison
                    peers_df = peer_comparison.get_peer_data(stock_symbol, peer_symbols, is_indian_stock)
                    
                    # Display the peer comparison data
                    st.dataframe(peers_df)
                    
                    # Add explanation of the metrics
                    with st.expander("About these metrics"):
                        st.markdown("""
                        **P/E Ratio**: Price-to-Earnings ratio, a valuation metric that compares a company's stock price to its earnings per share.
                        
                        **Market Cap (₹ Cr)**: Total market value of a company's outstanding shares in Indian Rupees Crores (1 Crore = 10 Million).
                        
                        **Dividend Yield (%)**: Annual dividend payment as a percentage of the stock price, showing income generated relative to investment.
                        
                        **YTD Return (%)**: Year-to-Date return, showing the percentage change in stock price since the beginning of the calendar year.
                        """)
            
            except Exception as e:
                st.error(f"Error loading peer comparison data: {str(e)}")
                st.info("Please try a different stock symbol or check your internet connection.")
    
    # Research Report Tab  
    with main_tabs[4]:
        st.header("Equity Research Report")
        
        # Company Overview
        st.subheader("1. Company Overview")
        
        # Business Model and Key Segments
        st.markdown("**Business Model and Key Segments:**")
        st.write(company_info.get('longBusinessSummary', 'No company description available.'))
        
        # Revenue mix (placeholder since we don't have segment data)
        st.markdown("**Revenue Mix:**")
        st.write("Detailed segment revenue information requires premium financial data.")
        
        # Key Milestones
        st.markdown("**Key Milestones:**")
        st.write("Information about IPO, product launches, and strategic partnerships.")
        
        # Strategic Developments
        st.subheader("2. Strategic Developments & Execution Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**A. Business Expansion & Innovation**")
            st.write("- Recent product/service launches")
            st.write("- R&D initiatives and new technologies")
            st.write("- Strategic partnerships and acquisitions")
            
            st.markdown("**B. Order Book & Execution Capacity**")
            st.write("- Current order book size and growth trends")
            st.write("- Future order pipeline and execution visibility")
        
        with col2:
            st.markdown("**C. Capacity Expansion**")
            st.write("- Details of expansion initiatives")
            st.write("- Capex funding strategy")
            
            st.markdown("**D. Risk Analysis**")
            st.write("- Regulatory and operational risks")
            st.write("- Geopolitical and other external factors")
            st.write("- Credit profile and financial health")
        
        # Management & Governance
        st.markdown("**E. Management & Governance**")
        st.write("- Management track record and execution capabilities")
        st.write("- Shareholding pattern and governance practices")
        st.write("- Any potential red flags or litigation concerns")
        
        # Valuation & Investment Perspective
        st.subheader("7. Valuation & Investment Perspective")
        
        # Valuation Multiples
        st.markdown("**Valuation Multiples:**")
        
        multiples_col1, multiples_col2 = st.columns(2)
        with multiples_col1:
            pe_ratio = company_info.get('trailingPE', 'N/A')
            if isinstance(pe_ratio, (int, float)):
                st.metric("P/E Ratio (TTM)", f"{pe_ratio:.2f}")
            else:
                st.metric("P/E Ratio (TTM)", "N/A")
                
            ps_ratio = company_info.get('priceToSalesTrailing12Months', 'N/A')
            if isinstance(ps_ratio, (int, float)):
                st.metric("P/S Ratio", f"{ps_ratio:.2f}")
            else:
                st.metric("P/S Ratio", "N/A")
        
        with multiples_col2:
            pb_ratio = company_info.get('priceToBook', 'N/A')
            if isinstance(pb_ratio, (int, float)):
                st.metric("P/B Ratio", f"{pb_ratio:.2f}")
            else:
                st.metric("P/B Ratio", "N/A")
                
            dividend_yield = company_info.get('dividendYield', 'N/A')
            if isinstance(dividend_yield, (int, float)):
                st.metric("Dividend Yield", f"{dividend_yield * 100:.2f}%")
            else:
                st.metric("Dividend Yield", "N/A")
        
        # Investment Rationale
        st.subheader("9. Conclusion & Investment Rationale")
        
        # Final Rating
        st.markdown("**Final Rating:**")
        
        # Example rating logic based on financial metrics
        if isinstance(company_info.get('returnOnEquity'), (int, float)) and company_info.get('returnOnEquity') > 0.15:
            rating = "Buy"
            rationale = "Strong financial performance with high return on equity."
        elif isinstance(company_info.get('returnOnEquity'), (int, float)) and company_info.get('returnOnEquity') > 0.10:
            rating = "Hold"
            rationale = "Solid financial performance with reasonable return metrics."
        else:
            rating = "Neutral"
            rationale = "Limited financial data available for a strong recommendation."
        
        st.info(f"**Investment Rating: {rating}**\n\n{rationale}")
        
        # Upside/Downside Triggers
        st.markdown("**Upside/Downside Triggers:**")
        
        upside_col, downside_col = st.columns(2)
        with upside_col:
            st.write("**Upside Triggers:**")
            st.write("- Strong earnings growth")
            st.write("- New product launches")
            st.write("- Expansion into new markets")
            st.write("- Favorable industry trends")
        
        with downside_col:
            st.write("**Downside Risks:**")
            st.write("- Competitive pressures")
            st.write("- Regulatory challenges")
            st.write("- Economic slowdown")
            st.write("- Supply chain disruptions")
            
    # Latest News Tab
    with main_tabs[5]:
        st.header("Latest Financial News")
        # Display one-click news summary for the selected stock
        stock_news.display_news(stock_symbol)
    
    # Watchlists Tab
    with main_tabs[6]:
        # Display watchlist section using the simplified implementation
        simple_watchlist.render_watchlist_section(stock_symbol)
    
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
        st.write("Advanced report options available for premium subscribers")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center;">
    <p>Data provided by Yahoo Finance | Created with Streamlit</p>
    <p>This dashboard is for informational purposes only and should not be considered as financial advice.</p>
</div>
""", unsafe_allow_html=True)
