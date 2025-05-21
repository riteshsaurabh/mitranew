import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import utils
import financial_metrics
import financial_metrics_direct
import simple_watchlist
import indian_markets
import stock_news
import stock_prediction
import format_utils
import financial_data

# Set page configuration
st.set_page_config(
    page_title="MoneyMitra - Your Financial Companion",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
with open("style.css") as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Title and description
st.markdown("""
<div style="display:flex; align-items:center; margin-bottom:20px; background:linear-gradient(90deg, #2D3047 0%, #1B998B 100%); padding:20px; border-radius:15px; box-shadow:0 4px 15px rgba(0,0,0,0.1);">
    <div style="margin-right:20px;">
        <h1 style="color:white; margin:0; font-size:2.5rem;">MoneyMitra</h1>
        <p style="color:#e5e5e5; margin:5px 0 0 0; font-size:1rem;">Your Financial Mitra for Making Informed Investment Decisions</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar with stock selection
with st.sidebar:
    st.markdown("## Stock Selection")
    
    # Choose market (Indian or International)
    market = st.radio("Select Market", ("Indian", "International"), horizontal=True)
    
    # Set flag for Indian stocks
    is_indian = (market == "Indian")
    
    # Stock symbol input
    symbol_placeholder = "Enter NSE Symbol (e.g., RELIANCE)" if is_indian else "Enter Symbol (e.g., AAPL)"
    
    # Get default symbols based on market
    default_symbols = ["RELIANCE", "TATAMOTORS", "INFY", "HDFCBANK", "ADANIENT"] if is_indian else ["AAPL", "MSFT", "AMZN", "GOOGL", "TSLA"]
    
    # Search for stock or select from popular ones
    search_col, popular_col = st.columns([3, 1])
    
    with search_col:
        stock_input = st.text_input("Search", placeholder=symbol_placeholder)
    
    with popular_col:
        st.write("")  # Empty space for alignment
        show_popular = st.button("Popular")
    
    # Show popular stocks if button clicked
    if show_popular:
        st.markdown("### Popular Stocks")
        
        # Display clickable buttons for popular stocks
        cols = st.columns(3)
        selected_symbol = None
        
        for i, symbol in enumerate(default_symbols):
            col_idx = i % 3
            with cols[col_idx]:
                if st.button(symbol, key=f"popular_{symbol}"):
                    selected_symbol = symbol
                    
        if selected_symbol:
            stock_input = selected_symbol
    
    # Append .NS suffix for Indian stocks if needed
    if stock_input and is_indian and not stock_input.endswith(".NS"):
        stock_symbol = f"{stock_input}.NS"
    else:
        stock_symbol = stock_input
    
    # Search button
    search_pressed = st.button("🔍 Search", key="search_stock", use_container_width=True)
    
    # Divider
    st.divider()
    
    # Watchlist section in sidebar
    st.markdown("## Watchlist")
    
    # Show watchlist
    simple_watchlist.display_watchlist(is_indian)

# Main content - only proceed if stock input is valid
if stock_symbol:
    try:
        # Get stock data
        ticker = yf.Ticker(stock_symbol)
        company_info = ticker.info
        
        # Check if company info was retrieved successfully
        if not company_info or not company_info.get('symbol'):
            st.warning(f"Could not retrieve data for {stock_symbol}. Please check the symbol and try again.")
        else:
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            stock_data = ticker.history(start=start_date, end=end_date)
            
            if stock_data.empty:
                st.warning(f"No historical data available for {stock_symbol}.")
            else:
                # Display company name and basic info
                company_name = company_info.get('shortName', stock_symbol)
                sector = company_info.get('sector', 'N/A')
                industry = company_info.get('industry', 'N/A')
                
                st.markdown(f"""
                <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:20px;">
                    <div style="display:flex; align-items:center; justify-content:space-between;">
                        <div>
                            <h2 style="margin:0; color:#2D3047;">{company_name}</h2>
                            <p style="margin:5px 0 0 0; color:#71717A; font-size:1rem;">{sector} | {industry}</p>
                        </div>
                        <div style="text-align:right;">
                            <h3 style="margin:0; color:#16C172;">
                                {format_utils.format_currency(company_info.get('currentPrice', stock_data['Close'].iloc[-1]), is_indian)}
                            </h3>
                            <p style="margin:5px 0 0 0; color:#71717A; font-size:0.9rem;">
                                {stock_symbol}
                            </p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Main content tabs
                main_tabs = st.tabs([
                    "📈 Overview", 
                    "💰 Financial Metrics", 
                    "📋 Income Statement", 
                    "📊 Balance Sheet", 
                    "💸 Cash Flow",
                    "🔎 Peer Comparison", 
                    "📰 News & Analysis"
                ])
                
                # OVERVIEW TAB
                with main_tabs[0]:
                    # Create a two-column layout
                    overview_col1, overview_col2 = st.columns([1, 2])
                    
                    with overview_col1:
                        # Key metrics section
                        st.markdown("### Key Metrics")
                        
                        # Create a 2x2 grid for metrics
                        metrics_row = st.columns(4)
                        
                        with metrics_row[0]:
                            if is_indian:
                                st.metric("Current Price", f"₹{stock_data['Close'].iloc[-1]:.2f}", 
                                        f"{((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100:.2f}%")
                            else:
                                st.metric("Current Price", f"${stock_data['Close'].iloc[-1]:.2f}", 
                                        f"{((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100:.2f}%")
                        with metrics_row[1]:
                            if is_indian:
                                # Format market cap in Indian style (Cr, L)
                                market_cap = company_info.get('marketCap')
                                if market_cap is not None:
                                    st.metric("Market Cap", format_utils.format_indian_numbers(market_cap, in_crores=True) + " Cr")
                                else:
                                    st.metric("Market Cap", "N/A")
                            else:
                                st.metric("Market Cap", format_utils.format_large_number(company_info.get('marketCap', 'N/A')))
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
                        
                        # Company overview
                        st.markdown("### Company Overview")
                        st.markdown(f"""
                        <div style="background:#f8f9fa; padding:15px; border-radius:10px; font-size:0.9rem; height:200px; overflow-y:auto;">
                            {company_info.get('longBusinessSummary', 'No company description available.')}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Key statistics section
                        st.markdown("### Key Statistics")
                        
                        # Create a nice looking statistics table
                        stats_data = {
                            "Open": format_utils.format_currency(company_info.get('open', 'N/A'), is_indian),
                            "High": format_utils.format_currency(company_info.get('dayHigh', 'N/A'), is_indian),
                            "Low": format_utils.format_currency(company_info.get('dayLow', 'N/A'), is_indian),
                            "Volume": format_utils.format_large_number(company_info.get('volume', 'N/A')),
                            "Avg Volume": format_utils.format_large_number(company_info.get('averageVolume', 'N/A')),
                            "Market Cap": format_utils.format_large_number(company_info.get('marketCap', 'N/A'), is_indian=is_indian),
                            "Beta": company_info.get('beta', 'N/A'),
                            "P/E Ratio": company_info.get('trailingPE', 'N/A'),
                            "EPS": format_utils.format_currency(company_info.get('trailingEps', 'N/A'), is_indian),
                            "Forward P/E": company_info.get('forwardPE', 'N/A'),
                            "Dividend Yield": format_utils.format_percent(company_info.get('dividendYield', 'N/A')),
                            "Target Price": format_utils.format_currency(company_info.get('targetMeanPrice', 'N/A'), is_indian)
                        }
                        
                        # Display in 2 columns for better layout
                        col1, col2 = st.columns(2)
                        
                        for i, (stat, value) in enumerate(stats_data.items()):
                            if i % 2 == 0:
                                with col1:
                                    st.markdown(f"""
                                    <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #eee;">
                                        <span style="color:#555; font-size:0.9rem;">{stat}</span>
                                        <span style="font-weight:500; font-size:0.9rem;">{value}</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                with col2:
                                    st.markdown(f"""
                                    <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #eee;">
                                        <span style="color:#555; font-size:0.9rem;">{stat}</span>
                                        <span style="font-weight:500; font-size:0.9rem;">{value}</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                    
                    with overview_col2:
                        # Display stock chart
                        st.markdown("### Stock Price Chart")
                        
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            # Chart type selection
                            chart_type = st.radio(
                                "Select chart type:",
                                ["Line", "Candlestick", "OHLC"],
                                horizontal=True,
                                key="chart_type"
                            )
                            
                        with col2:
                            # Add chart indicators
                            indicators = st.multiselect(
                                "Add indicators:",
                                ["SMA (20)", "SMA (50)", "SMA (200)", "EMA (20)", "Bollinger Bands"],
                                key="indicators"
                            )
                        
                        # Create chart based on type
                        if chart_type == "Line":
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=stock_data.index,
                                y=stock_data['Close'],
                                mode='lines',
                                name='Close Price',
                                line=dict(color='royalblue', width=2)
                            ))
                            
                        elif chart_type == "Candlestick":
                            fig = go.Figure(go.Candlestick(
                                x=stock_data.index,
                                open=stock_data['Open'],
                                high=stock_data['High'],
                                low=stock_data['Low'],
                                close=stock_data['Close'],
                                name='Price',
                                increasing_line_color='#16C172',
                                decreasing_line_color='#F05D5E'
                            ))
                            
                        else:  # OHLC
                            fig = go.Figure(go.Ohlc(
                                x=stock_data.index,
                                open=stock_data['Open'],
                                high=stock_data['High'],
                                low=stock_data['Low'],
                                close=stock_data['Close'],
                                name='Price',
                                increasing_line_color='#16C172',
                                decreasing_line_color='#F05D5E'
                            ))
                        
                        # Add indicators if selected
                        for indicator in indicators:
                            if indicator == "SMA (20)":
                                sma20 = stock_data['Close'].rolling(window=20).mean()
                                fig.add_trace(go.Scatter(
                                    x=stock_data.index,
                                    y=sma20,
                                    mode='lines',
                                    name='SMA 20',
                                    line=dict(color='orange', width=1)
                                ))
                            elif indicator == "SMA (50)":
                                sma50 = stock_data['Close'].rolling(window=50).mean()
                                fig.add_trace(go.Scatter(
                                    x=stock_data.index,
                                    y=sma50,
                                    mode='lines',
                                    name='SMA 50',
                                    line=dict(color='purple', width=1)
                                ))
                            elif indicator == "SMA (200)":
                                sma200 = stock_data['Close'].rolling(window=200).mean()
                                fig.add_trace(go.Scatter(
                                    x=stock_data.index,
                                    y=sma200,
                                    mode='lines',
                                    name='SMA 200',
                                    line=dict(color='red', width=1)
                                ))
                            elif indicator == "EMA (20)":
                                ema20 = stock_data['Close'].ewm(span=20, adjust=False).mean()
                                fig.add_trace(go.Scatter(
                                    x=stock_data.index,
                                    y=ema20,
                                    mode='lines',
                                    name='EMA 20',
                                    line=dict(color='green', width=1)
                                ))
                            elif indicator == "Bollinger Bands":
                                sma20 = stock_data['Close'].rolling(window=20).mean()
                                std20 = stock_data['Close'].rolling(window=20).std()
                                upper_band = sma20 + (std20 * 2)
                                lower_band = sma20 - (std20 * 2)
                                
                                fig.add_trace(go.Scatter(
                                    x=stock_data.index,
                                    y=upper_band,
                                    mode='lines',
                                    name='Upper BB',
                                    line=dict(color='rgba(173, 204, 255, 0.7)', width=1)
                                ))
                                
                                fig.add_trace(go.Scatter(
                                    x=stock_data.index,
                                    y=lower_band,
                                    mode='lines',
                                    name='Lower BB',
                                    line=dict(color='rgba(173, 204, 255, 0.7)', width=1),
                                    fill='tonexty',
                                    fillcolor='rgba(173, 204, 255, 0.2)'
                                ))
                        
                        # Update layout
                        fig.update_layout(
                            title=f"{company_name} ({stock_symbol}) - 1 Year Chart",
                            xaxis_title="Date",
                            yaxis_title=f"Price ({'₹' if is_indian else '$'})",
                            height=400,
                            template="plotly_white",
                            xaxis_rangeslider_visible=False,
                            margin=dict(l=0, r=0, t=40, b=0)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Additional sections for the overview tab
                        st.markdown("### Market Comparison")
                        
                        # Add comparison with either Sensex/Nifty or S&P 500 based on market
                        if is_indian:
                            try:
                                # Get NIFTY 50 data for comparison
                                nifty_symbol = "^NSEI"
                                nifty_data = yf.download(nifty_symbol, start=start_date, end=end_date, progress=False)
                                
                                if nifty_data is not None and not nifty_data.empty:
                                    # Normalize data for comparison
                                    normalized_stock = stock_data['Close'] / stock_data['Close'].iloc[0] * 100
                                    normalized_nifty = nifty_data['Close'] / nifty_data['Close'].iloc[0] * 100
                                    
                                    # Create comparison chart
                                    fig = go.Figure()
                                    
                                    fig.add_trace(go.Scatter(
                                        x=normalized_stock.index,
                                        y=normalized_stock,
                                        mode='lines',
                                        name=stock_symbol,
                                        line=dict(color='#16C172')
                                    ))
                                    
                                    fig.add_trace(go.Scatter(
                                        x=normalized_nifty.index,
                                        y=normalized_nifty,
                                        mode='lines',
                                        name='NIFTY 50',
                                        line=dict(color='#2D3047')
                                    ))
                                    
                                    # Update layout
                                    fig.update_layout(
                                        title=f"{company_name} vs NIFTY 50 (Normalized to 100)",
                                        xaxis_title="Date",
                                        yaxis_title="Normalized Price",
                                        height=400,
                                        template="plotly_white",
                                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Calculate performance metrics
                                    stock_return = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100
                                    nifty_return = ((nifty_data['Close'].iloc[-1] / nifty_data['Close'].iloc[0]) - 1) * 100
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.metric(
                                            f"{stock_symbol} Return", 
                                            f"{format_utils.format_percent(stock_return/100)}",
                                            f"{format_utils.format_percent((stock_return - nifty_return)/100)} vs NIFTY"
                                        )
                                        
                                    with col2:
                                        st.metric(
                                            "NIFTY Return", 
                                            f"{format_utils.format_percent(nifty_return/100)}"
                                        )
                                else:
                                    st.warning("Could not load NIFTY data for comparison.")
                            except Exception as e:
                                st.error(f"Error comparing with NIFTY: {str(e)}")
                        else:
                            try:
                                # Get S&P 500 data for comparison
                                sp500_symbol = "^GSPC"
                                sp500_data = yf.download(sp500_symbol, start=start_date, end=end_date, progress=False)
                                
                                if sp500_data is not None and not sp500_data.empty:
                                    # Normalize data for comparison
                                    normalized_stock = stock_data['Close'] / stock_data['Close'].iloc[0] * 100
                                    normalized_sp500 = sp500_data['Close'] / sp500_data['Close'].iloc[0] * 100
                                    
                                    # Create comparison chart
                                    fig = go.Figure()
                                    
                                    fig.add_trace(go.Scatter(
                                        x=normalized_stock.index,
                                        y=normalized_stock,
                                        mode='lines',
                                        name=stock_symbol,
                                        line=dict(color='#16C172')
                                    ))
                                    
                                    fig.add_trace(go.Scatter(
                                        x=normalized_sp500.index,
                                        y=normalized_sp500,
                                        mode='lines',
                                        name='S&P 500',
                                        line=dict(color='#2D3047')
                                    ))
                                    
                                    # Update layout
                                    fig.update_layout(
                                        title=f"{company_name} vs S&P 500 (Normalized to 100)",
                                        xaxis_title="Date",
                                        yaxis_title="Normalized Price",
                                        height=400,
                                        template="plotly_white",
                                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Calculate performance metrics
                                    stock_return = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100
                                    sp500_return = ((sp500_data['Close'].iloc[-1] / sp500_data['Close'].iloc[0]) - 1) * 100
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.metric(
                                            f"{stock_symbol} Return", 
                                            f"{format_utils.format_percent(stock_return/100)}",
                                            f"{format_utils.format_percent((stock_return - sp500_return)/100)} vs S&P 500"
                                        )
                                        
                                    with col2:
                                        st.metric(
                                            "S&P 500 Return", 
                                            f"{format_utils.format_percent(sp500_return/100)}"
                                        )
                                else:
                                    st.warning("Could not load S&P 500 data for comparison.")
                            except Exception as e:
                                st.error(f"Error comparing with S&P 500: {str(e)}")
                                
                # FINANCIAL METRICS TAB
                with main_tabs[1]:
                    st.markdown("""
                    <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:20px;">
                        <h3 style="margin-top:0; color:#2D3047;">Financial Metrics</h3>
                        <p style="color:#71717A; font-size:0.9rem; margin-bottom:0;">
                            Key financial metrics and ratios for analysis. Data source: Yahoo Finance.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.spinner("Loading financial metrics..."):
                        try:
                            # Get financial metrics using our direct implementation
                            metrics = financial_metrics_direct.get_financial_metrics(stock_symbol, is_indian)
                            
                            if metrics:
                                # Create tabs for different metric categories
                                metrics_tabs = st.tabs([
                                    "Valuation", 
                                    "Profitability", 
                                    "Financial Health",
                                    "Performance",
                                    "Technical",
                                    "Growth & Dividends"
                                ])
                                
                                # VALUATION METRICS TAB
                                with metrics_tabs[0]:
                                    st.markdown("### Valuation Metrics")
                                    
                                    # Display the metrics in a nice table
                                    if metrics['valuation_metrics']:
                                        # Create a DataFrame for display
                                        val_df = pd.DataFrame({
                                            'Metric': list(metrics['valuation_metrics'].keys()),
                                            'Value': list(metrics['valuation_metrics'].values())
                                        })
                                        
                                        # Create two columns to display the data
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            # First half of valuation metrics
                                            st.dataframe(
                                                val_df.iloc[:4],
                                                hide_index=True,
                                                use_container_width=True
                                            )
                                        
                                        with col2:
                                            # Second half of valuation metrics
                                            st.dataframe(
                                                val_df.iloc[4:],
                                                hide_index=True,
                                                use_container_width=True
                                            )
                                    else:
                                        st.warning("Valuation metrics data not available.")
                                
                                # PROFITABILITY METRICS TAB
                                with metrics_tabs[1]:
                                    st.markdown("### Profitability Metrics")
                                    
                                    if metrics['profitability_ratios']:
                                        # Create a DataFrame for display
                                        prof_df = pd.DataFrame({
                                            'Metric': list(metrics['profitability_ratios'].keys()),
                                            'Value': list(metrics['profitability_ratios'].values())
                                        })
                                        
                                        # Display the data
                                        st.dataframe(
                                            prof_df,
                                            hide_index=True,
                                            use_container_width=True
                                        )
                                    else:
                                        st.warning("Profitability metrics data not available.")
                                
                                # FINANCIAL HEALTH TAB
                                with metrics_tabs[2]:
                                    st.markdown("### Financial Health Metrics")
                                    
                                    if metrics['financial_health']:
                                        # Create a DataFrame for display
                                        health_df = pd.DataFrame({
                                            'Metric': list(metrics['financial_health'].keys()),
                                            'Value': list(metrics['financial_health'].values())
                                        })
                                        
                                        # Display the data
                                        st.dataframe(
                                            health_df,
                                            hide_index=True,
                                            use_container_width=True
                                        )
                                    else:
                                        st.warning("Financial health metrics data not available.")
                                
                                # PERFORMANCE METRICS TAB
                                with metrics_tabs[3]:
                                    st.markdown("### Performance Metrics")
                                    
                                    if metrics['performance_metrics']:
                                        # Create a DataFrame for display
                                        perf_df = pd.DataFrame({
                                            'Metric': list(metrics['performance_metrics'].keys()),
                                            'Value': list(metrics['performance_metrics'].values())
                                        })
                                        
                                        # Display the data in columns
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.dataframe(
                                                perf_df.iloc[:len(perf_df)//2],
                                                hide_index=True,
                                                use_container_width=True
                                            )
                                        
                                        with col2:
                                            st.dataframe(
                                                perf_df.iloc[len(perf_df)//2:],
                                                hide_index=True,
                                                use_container_width=True
                                            )
                                    else:
                                        st.warning("Performance metrics data not available.")
                                
                                # TECHNICAL INDICATORS TAB
                                with metrics_tabs[4]:
                                    st.markdown("### Technical Indicators")
                                    
                                    if metrics['technical_indicators']:
                                        # Create a DataFrame for display
                                        tech_df = pd.DataFrame({
                                            'Indicator': list(metrics['technical_indicators'].keys()),
                                            'Value': list(metrics['technical_indicators'].values())
                                        })
                                        
                                        # Display the data
                                        st.dataframe(
                                            tech_df,
                                            hide_index=True,
                                            use_container_width=True
                                        )
                                    else:
                                        st.warning("Technical indicator data not available.")
                                
                                # GROWTH & DIVIDENDS TAB
                                with metrics_tabs[5]:
                                    st.markdown("### Growth & Dividend Metrics")
                                    
                                    # Create two columns - one for growth, one for dividends
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown("#### Growth Metrics")
                                        
                                        if metrics['growth_metrics']:
                                            # Create a DataFrame for display
                                            growth_df = pd.DataFrame({
                                                'Metric': list(metrics['growth_metrics'].keys()),
                                                'Value': list(metrics['growth_metrics'].values())
                                            })
                                            
                                            # Display the data
                                            st.dataframe(
                                                growth_df,
                                                hide_index=True,
                                                use_container_width=True
                                            )
                                        else:
                                            st.warning("Growth metrics data not available.")
                                    
                                    with col2:
                                        st.markdown("#### Dividend Information")
                                        
                                        if metrics['dividend_info']:
                                            # Create a DataFrame for display
                                            div_df = pd.DataFrame({
                                                'Metric': list(metrics['dividend_info'].keys()),
                                                'Value': list(metrics['dividend_info'].values())
                                            })
                                            
                                            # Display the data
                                            st.dataframe(
                                                div_df,
                                                hide_index=True,
                                                use_container_width=True
                                            )
                                        else:
                                            st.warning("Dividend data not available.")
                            else:
                                st.warning("Financial metrics data not available for this stock.")
                        except Exception as e:
                            st.error(f"Error loading financial metrics: {str(e)}")
                
                # INCOME STATEMENT TAB
                with main_tabs[2]:
                    st.markdown("""
                    <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:20px;">
                        <h3 style="margin-top:0; color:#2D3047;">Income Statement</h3>
                        <p style="color:#71717A; font-size:0.9rem; margin-bottom:0;">
                            Financial data shown in {currency} {unit}. Data source: Yahoo Finance.
                        </p>
                    </div>
                    """.format(
                        currency="₹" if is_indian else "$",
                        unit="Crores" if is_indian else "Millions"
                    ), unsafe_allow_html=True)
                    
                    with st.spinner("Loading income statement..."):
                        # Get the income statement data using our direct approach
                        income_statement_df = financial_data.get_income_statement(stock_symbol, is_indian)
                        
                        if income_statement_df is not None and not income_statement_df.empty:
                            # Display the income statement
                            st.dataframe(
                                income_statement_df,
                                use_container_width=True,
                                hide_index=False
                            )
                            
                            # Display visualization for key metrics
                            st.markdown("### Key Income Statement Metrics")
                            
                            # Extract key metrics for visualization
                            key_metrics = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income"]
                            metrics_to_plot = []
                            
                            # Check which metrics exist in our data
                            for metric in key_metrics:
                                if metric in income_statement_df.index:
                                    metrics_to_plot.append(metric)
                            
                            if metrics_to_plot and len(income_statement_df.columns) > 0:
                                # Create visualization
                                fig = go.Figure()
                                
                                for metric in metrics_to_plot:
                                    # Convert string values to float for plotting
                                    try:
                                        values = [float(str(v).replace(',', '')) if isinstance(v, str) else v 
                                                 for v in income_statement_df.loc[metric]]
                                    except:
                                        # Skip if conversion fails
                                        continue
                                    
                                    fig.add_trace(go.Bar(
                                        x=income_statement_df.columns,
                                        y=values,
                                        name=metric
                                    ))
                                
                                # Update layout
                                fig.update_layout(
                                    title="Key Income Statement Metrics Over Time",
                                    xaxis_title="Reporting Period",
                                    yaxis_title=f"Value ({format_utils.format_currency(0, is_indian).strip('0')} {'Crores' if is_indian else 'Millions'})",
                                    legend_title="Metrics",
                                    height=400,
                                    template="plotly_white",
                                    barmode='group'
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Add margin analysis if possible
                                st.markdown("### Margin Analysis")
                                
                                # Calculate margins if we have the necessary metrics
                                if "Total Revenue" in income_statement_df.index and len(income_statement_df.columns) > 0:
                                    margins_df = pd.DataFrame(index=income_statement_df.columns)
                                    
                                    # Get total revenue values
                                    total_revenue = [float(str(v).replace(',', '')) if isinstance(v, str) else v 
                                                   for v in income_statement_df.loc["Total Revenue"]]
                                    
                                    # Gross Margin
                                    if "Gross Profit" in income_statement_df.index:
                                        gross_profit = [float(str(v).replace(',', '')) if isinstance(v, str) else v 
                                                      for v in income_statement_df.loc["Gross Profit"]]
                                        margins_df["Gross Margin"] = [gp/tr if tr != 0 else 0 for gp, tr in zip(gross_profit, total_revenue)]
                                    
                                    # Operating Margin
                                    if "Operating Income" in income_statement_df.index:
                                        operating_income = [float(str(v).replace(',', '')) if isinstance(v, str) else v 
                                                          for v in income_statement_df.loc["Operating Income"]]
                                        margins_df["Operating Margin"] = [oi/tr if tr != 0 else 0 for oi, tr in zip(operating_income, total_revenue)]
                                    
                                    # Net Margin
                                    if "Net Income" in income_statement_df.index:
                                        net_income = [float(str(v).replace(',', '')) if isinstance(v, str) else v 
                                                    for v in income_statement_df.loc["Net Income"]]
                                        margins_df["Net Margin"] = [ni/tr if tr != 0 else 0 for ni, tr in zip(net_income, total_revenue)]
                                    
                                    # Create visualization if we have margins data
                                    if not margins_df.empty and any(margins_df.columns):
                                        fig = go.Figure()
                                        
                                        for margin in margins_df.columns:
                                            fig.add_trace(go.Scatter(
                                                x=margins_df.index,
                                                y=margins_df[margin],
                                                mode='lines+markers',
                                                name=margin
                                            ))
                                        
                                        # Update layout
                                        fig.update_layout(
                                            title="Margin Analysis Over Time",
                                            xaxis_title="Reporting Period",
                                            yaxis_title="Margin (%)",
                                            yaxis_tickformat='.1%',
                                            legend_title="Margins",
                                            height=400,
                                            template="plotly_white"
                                        )
                                        
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.info("Not enough data to calculate margins.")
                                else:
                                    st.info("Total Revenue data not available for margin calculation.")
                            else:
                                st.warning("No suitable metrics found for visualization.")
                        else:
                            st.warning("Income statement data not available for this stock. Please try another stock symbol.")
                
                # BALANCE SHEET TAB
                with main_tabs[3]:
                    st.markdown("""
                    <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:20px;">
                        <h3 style="margin-top:0; color:#2D3047;">Balance Sheet</h3>
                        <p style="color:#71717A; font-size:0.9rem; margin-bottom:0;">
                            Financial data shown in {currency} {unit}. Data source: Yahoo Finance.
                        </p>
                    </div>
                    """.format(
                        currency="₹" if is_indian else "$",
                        unit="Crores" if is_indian else "Millions"
                    ), unsafe_allow_html=True)
                    
                    with st.spinner("Loading balance sheet..."):
                        # Get the balance sheet data using our direct approach
                        balance_sheet_df = financial_data.get_balance_sheet(stock_symbol, is_indian)
                        
                        if balance_sheet_df is not None and not balance_sheet_df.empty:
                            # Display the balance sheet
                            st.dataframe(
                                balance_sheet_df,
                                use_container_width=True,
                                hide_index=False
                            )
                            
                            # Check if we have enough data for visualization
                            if len(balance_sheet_df.columns) > 0:
                                # Display visualization for key categories
                                st.markdown("### Key Balance Sheet Categories")
                                
                                # Get the latest period
                                latest_period = balance_sheet_df.columns[0]
                                
                                # Define key categories we want to visualize
                                asset_categories = [
                                    "Total Assets", "Assets",
                                    "Cash And Cash Equivalents", "Cash",
                                    "Net Receivables", 
                                    "Inventory",
                                    "Property Plant & Equipment", "Net PPE",
                                    "Investments", "Long Term Investments"
                                ]
                                
                                liability_equity_categories = [
                                    "Total Liabilities", "Liabilities",
                                    "Accounts Payable",
                                    "Short Term Debt",
                                    "Long Term Debt",
                                    "Total Stockholder Equity", "Stockholders Equity", "Total Equity"
                                ]
                                
                                # Find which categories exist in our data
                                asset_items = {}
                                for category in asset_categories:
                                    if category in balance_sheet_df.index and pd.notna(balance_sheet_df.loc[category, latest_period]):
                                        # Try to convert string to float if needed
                                        value = balance_sheet_df.loc[category, latest_period]
                                        if isinstance(value, str):
                                            try:
                                                value = float(value.replace(',', ''))
                                            except:
                                                value = 0
                                        asset_items[category] = value
                                
                                liability_equity_items = {}
                                for category in liability_equity_categories:
                                    if category in balance_sheet_df.index and pd.notna(balance_sheet_df.loc[category, latest_period]):
                                        # Try to convert string to float if needed
                                        value = balance_sheet_df.loc[category, latest_period]
                                        if isinstance(value, str):
                                            try:
                                                value = float(value.replace(',', ''))
                                            except:
                                                value = 0
                                        liability_equity_items[category] = value
                                
                                # Only create visualizations if we have data
                                if asset_items and liability_equity_items:
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown(f"#### Asset Composition ({latest_period})")
                                        
                                        # Remove any negative values and duplicates
                                        asset_items_clean = {}
                                        
                                        # Prioritize which asset category to use
                                        if "Total Assets" in asset_items:
                                            asset_items_clean["Total Assets"] = max(0, asset_items["Total Assets"])
                                        elif "Assets" in asset_items:
                                            asset_items_clean["Total Assets"] = max(0, asset_items["Assets"])
                                        
                                        if "Cash And Cash Equivalents" in asset_items:
                                            asset_items_clean["Cash"] = max(0, asset_items["Cash And Cash Equivalents"])
                                        elif "Cash" in asset_items:
                                            asset_items_clean["Cash"] = max(0, asset_items["Cash"])
                                        
                                        if "Property Plant & Equipment" in asset_items:
                                            asset_items_clean["Property & Equipment"] = max(0, asset_items["Property Plant & Equipment"])
                                        elif "Net PPE" in asset_items:
                                            asset_items_clean["Property & Equipment"] = max(0, asset_items["Net PPE"])
                                        
                                        if "Net Receivables" in asset_items:
                                            asset_items_clean["Receivables"] = max(0, asset_items["Net Receivables"])
                                        
                                        if "Inventory" in asset_items:
                                            asset_items_clean["Inventory"] = max(0, asset_items["Inventory"])
                                            
                                        if "Investments" in asset_items:
                                            asset_items_clean["Investments"] = max(0, asset_items["Investments"])
                                        elif "Long Term Investments" in asset_items:
                                            asset_items_clean["Investments"] = max(0, asset_items["Long Term Investments"])
                                        
                                        # Calculate Other Assets
                                        total_assets = asset_items_clean.get("Total Assets", 0)
                                        specific_assets_sum = sum([v for k, v in asset_items_clean.items() if k != "Total Assets"])
                                        
                                        if total_assets > specific_assets_sum:
                                            asset_items_clean["Other Assets"] = total_assets - specific_assets_sum
                                        
                                        # Remove Total Assets for pie chart
                                        if "Total Assets" in asset_items_clean:
                                            del asset_items_clean["Total Assets"]
                                            
                                        # Only create pie chart if we have data
                                        if asset_items_clean:
                                            fig_assets = go.Figure(data=[go.Pie(
                                                labels=list(asset_items_clean.keys()),
                                                values=list(asset_items_clean.values()),
                                                hole=.4,
                                                marker=dict(colors=['#FF6B1A', '#16C172', '#1B998B', '#2D3047', '#F05D5E', '#E7C7B0', '#5F5AA2'])
                                            )])
                                            
                                            fig_assets.update_layout(
                                                title=f"Asset Composition - {latest_period}",
                                                height=350,
                                                template="plotly_white"
                                            )
                                            
                                            st.plotly_chart(fig_assets, use_container_width=True)
                                        else:
                                            st.info("Not enough asset data available for visualization.")
                                    
                                    with col2:
                                        st.markdown(f"#### Liability & Equity Composition ({latest_period})")
                                        
                                        # Clean up liability and equity items
                                        liab_equity_clean = {}
                                        
                                        # Prioritize categories
                                        if "Total Liabilities" in liability_equity_items:
                                            liab_equity_clean["Total Liabilities"] = max(0, liability_equity_items["Total Liabilities"])
                                        elif "Liabilities" in liability_equity_items:
                                            liab_equity_clean["Total Liabilities"] = max(0, liability_equity_items["Liabilities"])
                                        
                                        if "Total Stockholder Equity" in liability_equity_items:
                                            liab_equity_clean["Total Equity"] = max(0, liability_equity_items["Total Stockholder Equity"])
                                        elif "Stockholders Equity" in liability_equity_items:
                                            liab_equity_clean["Total Equity"] = max(0, liability_equity_items["Stockholders Equity"])
                                        elif "Total Equity" in liability_equity_items:
                                            liab_equity_clean["Total Equity"] = max(0, liability_equity_items["Total Equity"])
                                        
                                        if "Accounts Payable" in liability_equity_items:
                                            liab_equity_clean["Accounts Payable"] = max(0, liability_equity_items["Accounts Payable"])
                                        
                                        if "Short Term Debt" in liability_equity_items:
                                            liab_equity_clean["Short Term Debt"] = max(0, liability_equity_items["Short Term Debt"])
                                            
                                        if "Long Term Debt" in liability_equity_items:
                                            liab_equity_clean["Long Term Debt"] = max(0, liability_equity_items["Long Term Debt"])
                                        
                                        # Calculate Other Liabilities
                                        total_liabilities = liab_equity_clean.get("Total Liabilities", 0)
                                        specific_liabilities_sum = sum([v for k, v in liab_equity_clean.items() 
                                                                      if k != "Total Liabilities" and k != "Total Equity"])
                                        
                                        if total_liabilities > specific_liabilities_sum:
                                            liab_equity_clean["Other Liabilities"] = total_liabilities - specific_liabilities_sum
                                        
                                        # Remove Total Liabilities for pie chart
                                        if "Total Liabilities" in liab_equity_clean:
                                            del liab_equity_clean["Total Liabilities"]
                                        
                                        # Only create pie chart if we have data
                                        if liab_equity_clean:
                                            fig_liab_equity = go.Figure(data=[go.Pie(
                                                labels=list(liab_equity_clean.keys()),
                                                values=list(liab_equity_clean.values()),
                                                hole=.4,
                                                marker=dict(colors=['#F05D5E', '#2D3047', '#1B998B', '#FF6B1A', '#16C172'])
                                            )])
                                            
                                            fig_liab_equity.update_layout(
                                                title=f"Liability & Equity Composition - {latest_period}",
                                                height=350,
                                                template="plotly_white"
                                            )
                                            
                                            st.plotly_chart(fig_liab_equity, use_container_width=True)
                                        else:
                                            st.info("Not enough liability data available for visualization.")
                                else:
                                    st.info("Not enough data available for visualization.")
                        else:
                            st.warning("Balance sheet data not available for this stock. Please try another stock symbol.")
                
                # CASH FLOW TAB
                with main_tabs[4]:
                    st.markdown("""
                    <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:20px;">
                        <h3 style="margin-top:0; color:#2D3047;">Cash Flow Statement</h3>
                        <p style="color:#71717A; font-size:0.9rem; margin-bottom:0;">
                            Financial data shown in {currency} {unit}. Data source: Yahoo Finance.
                        </p>
                    </div>
                    """.format(
                        currency="₹" if is_indian else "$",
                        unit="Crores" if is_indian else "Millions"
                    ), unsafe_allow_html=True)
                    
                    with st.spinner("Loading cash flow statement..."):
                        # Get the cash flow data using our direct approach
                        cash_flow_df = financial_data.get_cash_flow(stock_symbol, is_indian)
                        
                        if cash_flow_df is not None and not cash_flow_df.empty:
                            # Display the cash flow statement
                            st.dataframe(
                                cash_flow_df,
                                use_container_width=True,
                                hide_index=False
                            )
                            
                            # Display visualization for key cash flow metrics
                            st.markdown("### Cash Flow Trends")
                            
                            # Select key metrics to visualize (common ones found in Yahoo Finance)
                            key_metrics = [
                                "Operating Cash Flow", "Total Cash From Operating Activities",
                                "Investing Cash Flow", "Total Cash From Investing Activities",
                                "Financing Cash Flow", "Total Cash From Financing Activities",
                                "Free Cash Flow"
                            ]
                            
                            # Find metrics that exist in our dataframe
                            metrics_to_plot = []
                            for metric in key_metrics:
                                if metric in cash_flow_df.index:
                                    metrics_to_plot.append(metric)
                                    # Only need one from each category
                                    if "Operating Cash Flow" in metrics_to_plot and "Total Cash From Operating Activities" in metrics_to_plot:
                                        metrics_to_plot.remove("Total Cash From Operating Activities")
                                    if "Investing Cash Flow" in metrics_to_plot and "Total Cash From Investing Activities" in metrics_to_plot:
                                        metrics_to_plot.remove("Total Cash From Investing Activities")
                                    if "Financing Cash Flow" in metrics_to_plot and "Total Cash From Financing Activities" in metrics_to_plot:
                                        metrics_to_plot.remove("Total Cash From Financing Activities")
                            
                            if metrics_to_plot and len(cash_flow_df.columns) > 0:
                                # Convert string values back to numbers for plotting
                                plot_data = cash_flow_df.copy()
                                for col in plot_data.columns:
                                    for idx in metrics_to_plot:
                                        if idx in plot_data.index:
                                            try:
                                                val = plot_data.loc[idx, col]
                                                if isinstance(val, str):
                                                    plot_data.loc[idx, col] = float(val.replace(',', ''))
                                            except:
                                                plot_data.loc[idx, col] = None
                                
                                # Create visualization
                                fig = go.Figure()
                                
                                for metric in metrics_to_plot:
                                    if metric in plot_data.index:
                                        fig.add_trace(go.Bar(
                                            x=plot_data.columns,
                                            y=plot_data.loc[metric],
                                            name=metric
                                        ))
                                
                                # Update layout
                                fig.update_layout(
                                    title="Cash Flow Trends Over Time",
                                    xaxis_title="Reporting Period",
                                    yaxis_title=f"Value ({format_utils.format_currency(0, is_indian).strip('0')} {'Crores' if is_indian else 'Millions'})",
                                    legend_title="Metrics",
                                    height=400,
                                    template="plotly_white",
                                    barmode='group'
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Cash flow composition breakdown
                                if len(cash_flow_df.columns) > 0:
                                    latest_period = cash_flow_df.columns[0]
                                    st.markdown(f"### Cash Flow Composition ({latest_period})")
                                    
                                    # Identify operating cash flow components
                                    ocf_components = [
                                        "Net Income", "Net Income From Continuing Operations",
                                        "Depreciation And Amortization", "Depreciation",
                                        "Change In Working Capital", "Changes In Working Capital"
                                    ]
                                    
                                    # Create columns for visualizations
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown("#### Cash Flow Components")
                                        
                                        # Try to find the main cash flow categories
                                        cf_categories = {}
                                        
                                        for cf_type in ["Operating Cash Flow", "Total Cash From Operating Activities"]:
                                            if cf_type in cash_flow_df.index and pd.notna(cash_flow_df.loc[cf_type, latest_period]):
                                                try:
                                                    if isinstance(cash_flow_df.loc[cf_type, latest_period], str):
                                                        cf_categories["Operating"] = float(cash_flow_df.loc[cf_type, latest_period].replace(',', ''))
                                                    else:
                                                        cf_categories["Operating"] = float(cash_flow_df.loc[cf_type, latest_period])
                                                    break
                                                except:
                                                    pass
                                        
                                        for cf_type in ["Investing Cash Flow", "Total Cash From Investing Activities"]:
                                            if cf_type in cash_flow_df.index and pd.notna(cash_flow_df.loc[cf_type, latest_period]):
                                                try:
                                                    if isinstance(cash_flow_df.loc[cf_type, latest_period], str):
                                                        cf_categories["Investing"] = float(cash_flow_df.loc[cf_type, latest_period].replace(',', ''))
                                                    else:
                                                        cf_categories["Investing"] = float(cash_flow_df.loc[cf_type, latest_period])
                                                    break
                                                except:
                                                    pass
                                        
                                        for cf_type in ["Financing Cash Flow", "Total Cash From Financing Activities"]:
                                            if cf_type in cash_flow_df.index and pd.notna(cash_flow_df.loc[cf_type, latest_period]):
                                                try:
                                                    if isinstance(cash_flow_df.loc[cf_type, latest_period], str):
                                                        cf_categories["Financing"] = float(cash_flow_df.loc[cf_type, latest_period].replace(',', ''))
                                                    else:
                                                        cf_categories["Financing"] = float(cash_flow_df.loc[cf_type, latest_period])
                                                    break
                                                except:
                                                    pass
                                        
                                        # Only create pie chart if we have at least two categories
                                        if len(cf_categories) >= 2:
                                            # Color the negative values differently
                                            colors = []
                                            for cat, value in cf_categories.items():
                                                if value >= 0:
                                                    colors.append('#16C172')  # Green for positive
                                                else:
                                                    colors.append('#F05D5E')  # Red for negative
                                            
                                            # Create absolute values for better visualization but keep the colors
                                            abs_categories = {k: abs(v) for k, v in cf_categories.items()}
                                            
                                            fig_cf_types = go.Figure(data=[go.Pie(
                                                labels=list(abs_categories.keys()),
                                                values=list(abs_categories.values()),
                                                hole=.4,
                                                marker=dict(colors=colors)
                                            )])
                                            
                                            fig_cf_types.update_layout(
                                                title="Cash Flow Categories by Magnitude",
                                                height=350,
                                                template="plotly_white"
                                            )
                                            
                                            st.plotly_chart(fig_cf_types, use_container_width=True)
                                        else:
                                            st.info("Not enough cash flow categories for visualization.")
                                            
                                    with col2:
                                        st.markdown("#### Operating Cash Flow Details")
                                        
                                        # Collect operating cash flow components
                                        ocf_breakdown = {}
                                        
                                        for component in ocf_components:
                                            if component in cash_flow_df.index and pd.notna(cash_flow_df.loc[component, latest_period]):
                                                try:
                                                    if isinstance(cash_flow_df.loc[component, latest_period], str):
                                                        val = float(cash_flow_df.loc[component, latest_period].replace(',', ''))
                                                    else:
                                                        val = float(cash_flow_df.loc[component, latest_period])
                                                    
                                                    # Use a more readable name for the component
                                                    if "Net Income" in component:
                                                        ocf_breakdown["Net Income"] = val
                                                    elif "Depreciation" in component:
                                                        ocf_breakdown["Depreciation & Amort."] = val
                                                    elif "Working Capital" in component:
                                                        ocf_breakdown["Working Capital"] = val
                                                except:
                                                    pass
                                        
                                        # Calculate Operating CF value 
                                        ocf_value = None
                                        for cf_type in ["Operating Cash Flow", "Total Cash From Operating Activities"]:
                                            if cf_type in cash_flow_df.index and pd.notna(cash_flow_df.loc[cf_type, latest_period]):
                                                try:
                                                    if isinstance(cash_flow_df.loc[cf_type, latest_period], str):
                                                        ocf_value = float(cash_flow_df.loc[cf_type, latest_period].replace(',', ''))
                                                    else:
                                                        ocf_value = float(cash_flow_df.loc[cf_type, latest_period])
                                                    break
                                                except:
                                                    pass
                                        
                                        # If we have OCF value and components, add "Other" category
                                        if ocf_value is not None and ocf_breakdown:
                                            component_sum = sum(ocf_breakdown.values())
                                            if abs(ocf_value - component_sum) > 0.01:  # Check if there's a difference
                                                ocf_breakdown["Other Components"] = ocf_value - component_sum
                                        
                                        # Only create waterfall chart if we have components
                                        if ocf_breakdown:
                                            # Create a waterfall chart for operating CF
                                            fig_ocf = go.Figure(go.Waterfall(
                                                name="Operating Cash Flow", 
                                                orientation="v",
                                                measure=["relative"]*len(ocf_breakdown),
                                                x=list(ocf_breakdown.keys()),
                                                y=list(ocf_breakdown.values()),
                                                connector={"line":{"color":"rgb(63, 63, 63)"}},
                                            ))
                                            
                                            fig_ocf.update_layout(
                                                title="Operating Cash Flow Breakdown",
                                                showlegend=False,
                                                height=350,
                                                template="plotly_white"
                                            )
                                            
                                            st.plotly_chart(fig_ocf, use_container_width=True)
                                        else:
                                            st.info("Not enough operating cash flow details for visualization.")
                                            
                                        # Free Cash Flow trend if available
                                        if "Free Cash Flow" in cash_flow_df.index:
                                            st.markdown("#### Free Cash Flow Trend")
                                            
                                            try:
                                                fcf_data = []
                                                for col in cash_flow_df.columns:
                                                    if pd.notna(cash_flow_df.loc["Free Cash Flow", col]):
                                                        try:
                                                            if isinstance(cash_flow_df.loc["Free Cash Flow", col], str):
                                                                val = float(cash_flow_df.loc["Free Cash Flow", col].replace(',', ''))
                                                            else:
                                                                val = float(cash_flow_df.loc["Free Cash Flow", col])
                                                            fcf_data.append(val)
                                                        except:
                                                            fcf_data.append(None)
                                                    else:
                                                        fcf_data.append(None)
                                                
                                                if any(fcf_data):
                                                    fig_fcf = go.Figure()
                                                    
                                                    fig_fcf.add_trace(go.Scatter(
                                                        x=cash_flow_df.columns,
                                                        y=fcf_data,
                                                        mode='lines+markers',
                                                        name='Free Cash Flow',
                                                        line=dict(color='#16C172', width=3),
                                                        marker=dict(size=8)
                                                    ))
                                                    
                                                    fig_fcf.update_layout(
                                                        title="Free Cash Flow Trend",
                                                        xaxis_title="Reporting Period",
                                                        yaxis_title=f"FCF ({format_utils.format_currency(0, is_indian).strip('0')} {'Crores' if is_indian else 'Millions'})",
                                                        height=200,
                                                        margin=dict(l=10, r=10, t=40, b=20),
                                                        template="plotly_white"
                                                    )
                                                    
                                                    st.plotly_chart(fig_fcf, use_container_width=True)
                                            except:
                                                st.info("Could not display Free Cash Flow trend.")
                                else:
                                    st.info("Not enough data for Cash Flow composition visualization.")
                            else:
                                st.warning("No suitable metrics found for visualization.")
                        else:
                            st.warning("Cash flow statement data not available for this stock. Please try another stock symbol.")
                
                # PEER COMPARISON TAB
                with main_tabs[5]:
                    st.markdown("""
                    <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:20px;">
                        <h3 style="margin-top:0; color:#2D3047;">Peer Comparison</h3>
                        <p style="color:#71717A; font-size:0.9rem; margin-bottom:0;">
                            Compare key metrics across industry peers. All values in same currency for fair comparison.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.spinner("Loading peer comparison data..."):
                        # Get the sector information for the stock
                        sector = company_info.get('sector', None)
                        
                        if sector:
                            # Get peer symbols based on sector
                            peer_symbols = utils.get_peer_symbols(stock_symbol, sector, is_indian)
                            
                            if peer_symbols:
                                # Get comparison data for visualization
                                comparison_data = utils.get_peer_comparison_data(stock_symbol, peer_symbols, is_indian)
                                
                                if comparison_data is not None and not comparison_data.empty:
                                    # Display the peer comparison data
                                    st.dataframe(
                                        comparison_data,
                                        use_container_width=True
                                    )
                                    
                                    # Create visualizations for key metrics
                                    st.markdown("### Key Metrics Comparison")
                                    
                                    # Add tabs for different comparison views
                                    comparison_tabs = st.tabs(["Valuation", "Performance", "Financial Health"])
                                    
                                    # Valuation metrics comparison
                                    with comparison_tabs[0]:
                                        # Create columns for multiple charts
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            # P/E Ratio comparison
                                            if 'P/E Ratio' in comparison_data.columns:
                                                # Extract P/E values and convert to numeric
                                                pe_values = []
                                                for val in comparison_data['P/E Ratio']:
                                                    try:
                                                        if isinstance(val, str):
                                                            pe_values.append(float(val.replace(',', '')))
                                                        else:
                                                            pe_values.append(float(val))
                                                    except:
                                                        pe_values.append(None)
                                                
                                                # Create the figure
                                                fig = go.Figure()
                                                
                                                fig.add_trace(go.Bar(
                                                    x=comparison_data.index,
                                                    y=pe_values,
                                                    marker_color=['#FF6B1A' if x == stock_symbol else '#1B998B' for x in comparison_data.index]
                                                ))
                                                
                                                fig.update_layout(
                                                    title="P/E Ratio Comparison",
                                                    height=400,
                                                    template="plotly_white"
                                                )
                                                
                                                st.plotly_chart(fig, use_container_width=True)
                                        
                                        with col2:
                                            # P/B Ratio comparison
                                            if 'P/B Ratio' in comparison_data.columns:
                                                # Extract P/B values and convert to numeric
                                                pb_values = []
                                                for val in comparison_data['P/B Ratio']:
                                                    try:
                                                        if isinstance(val, str):
                                                            pb_values.append(float(val.replace(',', '')))
                                                        else:
                                                            pb_values.append(float(val))
                                                    except:
                                                        pb_values.append(None)
                                                
                                                # Create the figure
                                                fig = go.Figure()
                                                
                                                fig.add_trace(go.Bar(
                                                    x=comparison_data.index,
                                                    y=pb_values,
                                                    marker_color=['#FF6B1A' if x == stock_symbol else '#1B998B' for x in comparison_data.index]
                                                ))
                                                
                                                fig.update_layout(
                                                    title="P/B Ratio Comparison",
                                                    height=400,
                                                    template="plotly_white"
                                                )
                                                
                                                st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Performance metrics comparison
                                    with comparison_tabs[1]:
                                        # Extract return values and convert to numeric
                                        if 'YTD Return' in comparison_data.columns:
                                            # Create columns for multiple charts
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                # YTD Return comparison
                                                # Extract YTD returns and convert to numeric
                                                ytd_values = []
                                                for val in comparison_data['YTD Return']:
                                                    try:
                                                        if isinstance(val, str) and '%' in val:
                                                            ytd_values.append(float(val.replace('%', '').replace(',', '')))
                                                        else:
                                                            ytd_values.append(float(val) * 100 if val is not None else None)
                                                    except:
                                                        ytd_values.append(None)
                                                
                                                # Create the figure
                                                fig = go.Figure()
                                                
                                                fig.add_trace(go.Bar(
                                                    x=comparison_data.index,
                                                    y=ytd_values,
                                                    marker_color=['#FF6B1A' if x == stock_symbol else ('#16C172' if y is not None and y >= 0 else '#F05D5E') for x, y in zip(comparison_data.index, ytd_values)]
                                                ))
                                                
                                                fig.update_layout(
                                                    title="YTD Return Comparison (%)",
                                                    height=400,
                                                    template="plotly_white"
                                                )
                                                
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            with col2:
                                                # Beta comparison
                                                if 'Beta' in comparison_data.columns:
                                                    # Extract Beta values and convert to numeric
                                                    beta_values = []
                                                    for val in comparison_data['Beta']:
                                                        try:
                                                            if isinstance(val, str):
                                                                beta_values.append(float(val.replace(',', '')))
                                                            else:
                                                                beta_values.append(float(val))
                                                        except:
                                                            beta_values.append(None)
                                                    
                                                    # Create the figure
                                                    fig = go.Figure()
                                                    
                                                    fig.add_trace(go.Bar(
                                                        x=comparison_data.index,
                                                        y=beta_values,
                                                        marker_color=['#FF6B1A' if x == stock_symbol else '#1B998B' for x in comparison_data.index]
                                                    ))
                                                    
                                                    # Add a horizontal line at Beta = 1
                                                    fig.add_shape(
                                                        type='line',
                                                        x0=-0.5,
                                                        y0=1,
                                                        x1=len(comparison_data.index) - 0.5,
                                                        y1=1,
                                                        line=dict(color='red', width=2, dash='dash')
                                                    )
                                                    
                                                    fig.update_layout(
                                                        title="Beta Comparison (Market Beta = 1.0)",
                                                        height=400,
                                                        template="plotly_white"
                                                    )
                                                    
                                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Financial Health metrics comparison
                                    with comparison_tabs[2]:
                                        # Create columns for multiple charts
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            # Profit Margin comparison
                                            if 'Profit Margin' in comparison_data.columns:
                                                # Extract Profit Margin values and convert to numeric
                                                margin_values = []
                                                for val in comparison_data['Profit Margin']:
                                                    try:
                                                        if isinstance(val, str) and '%' in val:
                                                            margin_values.append(float(val.replace('%', '').replace(',', '')))
                                                        else:
                                                            margin_values.append(float(val) * 100 if val is not None else None)
                                                    except:
                                                        margin_values.append(None)
                                                
                                                # Create the figure
                                                fig = go.Figure()
                                                
                                                fig.add_trace(go.Bar(
                                                    x=comparison_data.index,
                                                    y=margin_values,
                                                    marker_color=['#FF6B1A' if x == stock_symbol else ('#16C172' if y is not None and y >= 0 else '#F05D5E') for x, y in zip(comparison_data.index, margin_values)]
                                                ))
                                                
                                                fig.update_layout(
                                                    title="Profit Margin Comparison (%)",
                                                    height=400,
                                                    template="plotly_white"
                                                )
                                                
                                                st.plotly_chart(fig, use_container_width=True)
                                        
                                        with col2:
                                            # ROE comparison
                                            if 'ROE' in comparison_data.columns:
                                                # Extract ROE values and convert to numeric
                                                roe_values = []
                                                for val in comparison_data['ROE']:
                                                    try:
                                                        if isinstance(val, str) and '%' in val:
                                                            roe_values.append(float(val.replace('%', '').replace(',', '')))
                                                        else:
                                                            roe_values.append(float(val) * 100 if val is not None else None)
                                                    except:
                                                        roe_values.append(None)
                                                
                                                # Create the figure
                                                fig = go.Figure()
                                                
                                                fig.add_trace(go.Bar(
                                                    x=comparison_data.index,
                                                    y=roe_values,
                                                    marker_color=['#FF6B1A' if x == stock_symbol else ('#16C172' if y is not None and y >= 0 else '#F05D5E') for x, y in zip(comparison_data.index, roe_values)]
                                                ))
                                                
                                                fig.update_layout(
                                                    title="Return on Equity Comparison (%)",
                                                    height=400,
                                                    template="plotly_white"
                                                )
                                                
                                                st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning("Could not load comparison data for peers.")
                            else:
                                st.warning(f"No peer companies found for {company_name} in the {sector} sector.")
                        else:
                            st.warning(f"Sector information not available for {company_name}.")
                
                # NEWS & ANALYSIS TAB
                with main_tabs[6]:
                    st.markdown("""
                    <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:20px;">
                        <h3 style="margin-top:0; color:#2D3047;">News & Analysis</h3>
                        <p style="color:#71717A; font-size:0.9rem; margin-bottom:0;">
                            Latest news, sentiment analysis, and AI-powered insights for informed decisions.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.spinner("Loading news and analysis..."):
                        # Get news for the stock
                        max_news = 5  # Number of news articles to display
                        news_data = stock_news.get_stock_news(stock_symbol, max_news)
                        
                        if news_data:
                            # Display news articles
                            st.markdown("### Latest News")
                            
                            for i, news in enumerate(news_data):
                                # Format the news article display
                                st.markdown(f"""
                                <div style="background:#f8f9fa; padding:15px; border-radius:10px; margin-bottom:15px;">
                                    <h4 style="margin:0; color:#2D3047; font-size:1.2rem;">{news['title']}</h4>
                                    <p style="margin:5px 0; color:#71717A; font-size:0.8rem;">{news.get('publisher', 'Unknown')} • {news.get('date', '')}</p>
                                    <p style="margin:10px 0;">{news['summary']}</p>
                                    <a href="{news['link']}" target="_blank" style="color:#FF6B1A; text-decoration:none; font-weight:500;">
                                        Read more →
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Add sentiment analysis if available
                            if any('sentiment' in news for news in news_data):
                                st.markdown("### Sentiment Analysis")
                                
                                # Extract sentiment scores and sources
                                sentiment_data = [
                                    (news.get('sentiment', 'neutral'), news.get('publisher', 'Unknown'))
                                    for news in news_data
                                    if 'sentiment' in news
                                ]
                                
                                if sentiment_data:
                                    # Count sentiments
                                    pos_count = sum(1 for s, _ in sentiment_data if s == 'positive')
                                    neg_count = sum(1 for s, _ in sentiment_data if s == 'negative')
                                    neu_count = sum(1 for s, _ in sentiment_data if s == 'neutral')
                                    
                                    total = len(sentiment_data)
                                    pos_pct = (pos_count / total) if total > 0 else 0
                                    neg_pct = (neg_count / total) if total > 0 else 0
                                    neu_pct = (neu_count / total) if total > 0 else 0
                                    
                                    # Display sentiment distribution
                                    col1, col2 = st.columns([1, 1])
                                    
                                    with col1:
                                        # Create a pie chart for sentiment distribution
                                        labels = ['Positive', 'Neutral', 'Negative']
                                        values = [pos_count, neu_count, neg_count]
                                        colors = ['#16C172', '#FFC857', '#F05D5E']
                                        
                                        fig = go.Figure(data=[go.Pie(
                                            labels=labels,
                                            values=values,
                                            marker=dict(colors=colors),
                                            hole=.4
                                        )])
                                        
                                        fig.update_layout(
                                            title="News Sentiment Distribution",
                                            height=300,
                                            margin=dict(l=10, r=10, t=30, b=10),
                                            template="plotly_white"
                                        )
                                        
                                        st.plotly_chart(fig, use_container_width=True)
                                    
                                    with col2:
                                        # Display overall sentiment score
                                        sentiment_score = (pos_pct - neg_pct) * 100  # Scale from -100 to 100
                                        
                                        # Create sentiment gauge
                                        fig = go.Figure(go.Indicator(
                                            mode="gauge+number",
                                            value=sentiment_score,
                                            domain={'x': [0, 1], 'y': [0, 1]},
                                            title={'text': "Market Sentiment Score", 'font': {'size': 16}},
                                            gauge={
                                                'axis': {'range': [-100, 100], 'tickwidth': 1},
                                                'bar': {'color': "#1B998B"},
                                                'steps': [
                                                    {'range': [-100, -40], 'color': "#F05D5E"},
                                                    {'range': [-40, 40], 'color': "#FFC857"},
                                                    {'range': [40, 100], 'color': "#16C172"}
                                                ],
                                                'threshold': {
                                                    'line': {'color': "black", 'width': 2},
                                                    'thickness': 0.75,
                                                    'value': sentiment_score
                                                }
                                            }
                                        ))
                                        
                                        fig.update_layout(
                                            height=300,
                                            margin=dict(l=10, r=10, t=30, b=10),
                                            template="plotly_white"
                                        )
                                        
                                        st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning(f"No recent news found for {company_name}.")
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
else:
    # Display welcome message if no stock is selected
    st.markdown("""
    <div style="background:white; padding:30px; border-radius:15px; text-align:center; max-width:800px; margin:0 auto;">
        <h2 style="color:#2D3047; margin-bottom:20px;">Welcome to MoneyMitra!</h2>
        <p style="font-size:1.1rem; color:#555; margin-bottom:20px;">
            Your comprehensive stock analysis and investment research platform. Search for a stock symbol to get started.
        </p>
        <div style="display:flex; justify-content:center; margin-top:20px;">
            <div style="background:#f8f9fa; padding:15px; margin:0 10px; border-radius:10px; text-align:center; width:180px;">
                <div style="font-size:2rem; color:#FF6B1A; margin-bottom:10px;">📊</div>
                <div style="font-weight:500; color:#2D3047;">Financial Analysis</div>
                <p style="font-size:0.9rem; color:#71717A;">Comprehensive financial metrics and statements</p>
            </div>
            <div style="background:#f8f9fa; padding:15px; margin:0 10px; border-radius:10px; text-align:center; width:180px;">
                <div style="font-size:2rem; color:#16C172; margin-bottom:10px;">📈</div>
                <div style="font-weight:500; color:#2D3047;">Technical Charts</div>
                <p style="font-size:0.9rem; color:#71717A;">Interactive price charts with indicators</p>
            </div>
            <div style="background:#f8f9fa; padding:15px; margin:0 10px; border-radius:10px; text-align:center; width:180px;">
                <div style="font-size:2rem; color:#1B998B; margin-bottom:10px;">📰</div>
                <div style="font-weight:500; color:#2D3047;">News & Insights</div>
                <p style="font-size:0.9rem; color:#71717A;">AI-powered news analysis and sentiment</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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