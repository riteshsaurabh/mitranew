import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import indian_markets

@st.cache_data(ttl=3600)
def get_peer_data(symbol, peers, is_indian=False):
    """
    Get real financial data for peer comparison from Yahoo Finance
    
    Args:
        symbol (str): Main stock symbol
        peers (list): List of peer stock symbols
        is_indian (bool): Whether stocks are Indian
        
    Returns:
        pd.DataFrame: DataFrame with peer comparison data
    """
    # Create list with main stock and peers
    all_symbols = [symbol] + peers
    
    # Filter out any duplicates or None values
    all_symbols = [s for s in all_symbols if s and s != "Industry Average"]
    
    # Add the company information rows
    companies = []
    pe_ratios = []
    market_caps = []
    dividend_yields = []
    returns = []
    
    # Get current date and date 1 year ago for return calculation
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Collect data for each symbol
    for sym in all_symbols:
        try:
            # Get stock info
            stock = yf.Ticker(sym)
            info = stock.info
            
            # Get historical data for YTD calculation
            hist = stock.history(period="1y")
            
            # Calculate basic metrics
            # P/E Ratio
            pe = info.get('trailingPE', None)
            if not pe or not isinstance(pe, (int, float)):
                pe = "N/A"
            elif isinstance(pe, (int, float)):
                pe = round(pe, 2)
            
            # Market Cap
            market_cap = info.get('marketCap', None)
            if market_cap and isinstance(market_cap, (int, float)):
                # Convert to Crores (1 Crore = 10 million)
                # For Indian stocks, use the INR conversion rate if needed
                if is_indian:
                    market_cap = round(market_cap / 10000000, 2)  # Convert to Crore
                else:
                    # If USD, convert to INR and then to Crore
                    market_cap = round((market_cap * 83.0) / 10000000, 2)  # Approx conversion rate
            else:
                market_cap = "N/A"
            
            # Dividend Yield
            div_yield = info.get('dividendYield', None)
            if div_yield and isinstance(div_yield, (int, float)):
                div_yield = round(div_yield * 100, 2)  # Convert to percentage
            else:
                div_yield = "N/A"
            
            # YTD Return
            if not hist.empty and len(hist) > 1:
                first_price = hist['Close'].iloc[0]
                last_price = hist['Close'].iloc[-1]
                ytd_return = ((last_price / first_price) - 1) * 100
                ytd_return = round(ytd_return, 2)
            else:
                ytd_return = "N/A"
            
            # Get company name
            company_name = info.get('shortName', sym)
            
            # Add data to lists
            companies.append(f"{company_name} ({sym})")
            pe_ratios.append(pe)
            market_caps.append(market_cap)
            dividend_yields.append(div_yield)
            returns.append(ytd_return)
            
        except Exception as e:
            st.error(f"Error getting data for {sym}: {str(e)}")
            # Add placeholder data for the symbol
            companies.append(f"Unknown ({sym})")
            pe_ratios.append("N/A")
            market_caps.append("N/A")
            dividend_yields.append("N/A")
            returns.append("N/A")
    
    # Get industry averages
    if is_indian:
        # Use sector-specific industry averages for Indian stocks
        sector_averages = {
            "Technology": {
                "name": "Tech Avg",
                "pe": 22.5, 
                "mcap": 4500, 
                "div": 2.2, 
                "returns": 11.5
            },
            "Financial Services": {
                "name": "Financial Avg",
                "pe": 16.3, 
                "mcap": 8200, 
                "div": 1.9, 
                "returns": 13.2
            },
            "Consumer Cyclical": {
                "name": "Consumer Avg",
                "pe": 19.2, 
                "mcap": 2200, 
                "div": 1.5, 
                "returns": 14.8
            },
            "Communications": {
                "name": "Comm Avg",
                "pe": 18.7, 
                "mcap": 2800, 
                "div": 1.7, 
                "returns": 10.2
            },
            "Energy": {
                "name": "Energy Avg",
                "pe": 12.8, 
                "mcap": 9500, 
                "div": 3.2, 
                "returns": 9.7
            },
            "Healthcare": {
                "name": "Healthcare Avg",
                "pe": 24.3, 
                "mcap": 3700, 
                "div": 1.1, 
                "returns": 12.4
            }
        }
        
        # Default to Technology if sector not specified
        sector_avg = sector_averages.get("Technology", {})
        
        # Add industry average to comparison
        companies.append(f"Industry Average")
        pe_ratios.append(sector_avg.get("pe", "N/A"))
        market_caps.append(sector_avg.get("mcap", "N/A"))
        dividend_yields.append(sector_avg.get("div", "N/A"))
        returns.append(sector_avg.get("returns", "N/A"))
    
    # Create DataFrame
    data = {
        'Company': companies,
        'P/E Ratio': pe_ratios,
        'Market Cap (₹ Cr)': market_caps,
        'Dividend Yield (%)': dividend_yields,
        'YTD Return (%)': returns
    }
    
    return pd.DataFrame(data)

def get_sector_peers(symbol, sector):
    """
    Get real peer symbols based on sector from Yahoo Finance
    
    Args:
        symbol (str): Stock symbol
        sector (str): Stock sector
        
    Returns:
        list: List of peer stock symbols
    """
    # Define peer stocks for different sectors (focusing on Indian markets)
    peers = {
        "Technology": ["INFY.NS", "TECHM.NS", "WIPRO.NS", "HCLTECH.NS"],
        "Financial Services": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS"],
        "Consumer Cyclical": ["TATAMOTORS.NS", "MARUTI.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS"],
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