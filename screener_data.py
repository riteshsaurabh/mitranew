"""
Screener.in Data Fetcher Module

This module is responsible for fetching financial data from Screener.in website.
It provides functions to get financial statements and other stock data.
"""

import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
import streamlit as st

# Mapping of NSE symbols to Screener.in URLs
# Some companies have different identifiers on Screener.in
SYMBOL_MAPPING = {
    # Common mapping overrides
    "RELIANCE.NS": "RELIANCE",
    "INFY.NS": "INFY",
    "TCS.NS": "TCS",
    "HDFCBANK.NS": "HDFCBANK",
    "ICICIBANK.NS": "ICICIBANK",
    "SBIN.NS": "SBIN",
    "TATASTEEL.NS": "TATASTEEL",
    "TATAMOTORS.NS": "TATAMOTORS",
    "HINDUNILVR.NS": "HINDUNILVR",
    "BAJFINANCE.NS": "BAJFINANCE",
    "BHARTIARTL.NS": "BHARTIARTL",
    "AXISBANK.NS": "AXISBANK",
    "MARUTI.NS": "MARUTI",
    "KOTAKBANK.NS": "KOTAKBANK",
    "ITC.NS": "ITC",
    "WIPRO.NS": "WIPRO",
    "HCLTECH.NS": "HCLTECH",
    # Add more mappings as needed
}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_screener_url(symbol):
    """
    Get the Screener.in URL for a given stock symbol
    
    Args:
        symbol (str): Stock symbol (with or without .NS/.BO suffix)
    
    Returns:
        str: URL for the company page on Screener.in
    """
    # Remove exchange suffix if present
    base_symbol = symbol.split('.')[0]
    
    # Check if we have a specific mapping
    if symbol in SYMBOL_MAPPING:
        base_symbol = SYMBOL_MAPPING[symbol]
    
    # Construct and return the URL
    return f"https://www.screener.in/company/{base_symbol}/"

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_screener_company_data(symbol):
    """
    Fetch all available company data from Screener.in
    
    Args:
        symbol (str): Stock symbol (with or without .NS/.BO suffix)
    
    Returns:
        dict: Dictionary containing the company data from Screener.in
    """
    url = get_screener_url(symbol)
    
    try:
        # Set user-agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Fetch the page
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check if the request was successful
        if response.status_code != 200:
            st.warning(f"Failed to fetch data from Screener.in: {response.status_code}")
            return None
            
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract company info
        company_info = {}
        company_name_element = soup.find('h1')
        if company_name_element:
            company_info['name'] = company_name_element.get_text().strip()
        else:
            company_info['name'] = 'N/A'
        
        # Extract ratios and metrics
        ratios_section = soup.find('div', {'id': 'top-ratios'})
        if ratios_section:
            ratios = {}
            ratio_items = ratios_section.find_all('li')
            for item in ratio_items:
                label_element = item.find('span', {'class': 'name'})
                value_element = item.find('span', {'class': 'value'})
                if label_element and value_element:
                    label_text = label_element.get_text().strip()
                    value_text = value_element.get_text().strip()
                    ratios[label_text] = value_text
            company_info['ratios'] = ratios
        
        # Look for JSON data in script tags - Screener often includes data in JSON format
        scripts = soup.find_all('script')
        for script in scripts:
            script_content = script.string if hasattr(script, 'string') else None
            if script_content and 'var data' in script_content:
                # Extract and parse the JSON data
                json_match = re.search(r'var data = ({.*?});', script_content, re.DOTALL)
                if json_match:
                    try:
                        company_data = json.loads(json_match.group(1))
                        company_info['data'] = company_data
                    except json.JSONDecodeError as json_err:
                        st.warning(f"Error parsing JSON data: {json_err}")
        
        # Return the complete company information
        return company_info
    
    except Exception as e:
        st.warning(f"Error fetching data from Screener.in: {e}")
        return None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_profit_and_loss(symbol):
    """
    Fetch the profit and loss (income statement) data from Screener.in
    
    Args:
        symbol (str): Stock symbol (with or without .NS/.BO suffix)
    
    Returns:
        pd.DataFrame: Profit and loss statement with years as columns and items as rows
    """
    company_data = fetch_screener_company_data(symbol)
    
    if not company_data or 'data' not in company_data:
        return pd.DataFrame()
    
    # Extract profit and loss data
    try:
        # Screener stores P&L data in the 'data' section
        data = company_data['data']
        
        if 'profit_and_loss' in data:
            pl_data = data['profit_and_loss']
            
            # Convert the data to a DataFrame
            periods = []
            pl_items = {}
            
            # Initialize with the structure we need
            for period in pl_data:
                period_key = period.get('c_name', 'Unknown')
                periods.append(period_key)
                
                # Process each item in the period
                for item in period.get('values', []):
                    item_name = item.get('name', 'Unknown')
                    value = item.get('value')
                    
                    # Initialize if not already in the dictionary
                    if item_name not in pl_items:
                        pl_items[item_name] = {}
                    
                    # Add the value for this period
                    pl_items[item_name][period_key] = value
            
            # Create a DataFrame from the collected data
            df = pd.DataFrame.from_dict(pl_items, orient='index')
            
            # Sort columns to have most recent first
            if not df.empty:
                df = df[sorted(df.columns, reverse=True)]
            
            return df
        else:
            return pd.DataFrame()
    
    except Exception as e:
        st.warning(f"Error processing P&L data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_balance_sheet(symbol):
    """
    Fetch the balance sheet data from Screener.in
    
    Args:
        symbol (str): Stock symbol (with or without .NS/.BO suffix)
    
    Returns:
        pd.DataFrame: Balance sheet with years as columns and items as rows
    """
    company_data = fetch_screener_company_data(symbol)
    
    if not company_data or 'data' not in company_data:
        return pd.DataFrame()
    
    # Extract balance sheet data
    try:
        # Screener stores balance sheet data in the 'data' section
        data = company_data['data']
        
        if 'balance_sheet' in data:
            bs_data = data['balance_sheet']
            
            # Convert the data to a DataFrame
            periods = []
            bs_items = {}
            
            # Initialize with the structure we need
            for period in bs_data:
                period_key = period.get('c_name', 'Unknown')
                periods.append(period_key)
                
                # Process each item in the period
                for item in period.get('values', []):
                    item_name = item.get('name', 'Unknown')
                    value = item.get('value')
                    
                    # Initialize if not already in the dictionary
                    if item_name not in bs_items:
                        bs_items[item_name] = {}
                    
                    # Add the value for this period
                    bs_items[item_name][period_key] = value
            
            # Create a DataFrame from the collected data
            df = pd.DataFrame.from_dict(bs_items, orient='index')
            
            # Sort columns to have most recent first
            if not df.empty:
                df = df[sorted(df.columns, reverse=True)]
            
            return df
        else:
            return pd.DataFrame()
    
    except Exception as e:
        st.warning(f"Error processing balance sheet data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cash_flow(symbol):
    """
    Fetch the cash flow statement data from Screener.in
    
    Args:
        symbol (str): Stock symbol (with or without .NS/.BO suffix)
    
    Returns:
        pd.DataFrame: Cash flow statement with years as columns and items as rows
    """
    company_data = fetch_screener_company_data(symbol)
    
    if not company_data or 'data' not in company_data:
        return pd.DataFrame()
    
    # Extract cash flow data
    try:
        # Screener stores cash flow data in the 'data' section
        data = company_data['data']
        
        if 'cash_flow' in data:
            cf_data = data['cash_flow']
            
            # Convert the data to a DataFrame
            periods = []
            cf_items = {}
            
            # Initialize with the structure we need
            for period in cf_data:
                period_key = period.get('c_name', 'Unknown')
                periods.append(period_key)
                
                # Process each item in the period
                for item in period.get('values', []):
                    item_name = item.get('name', 'Unknown')
                    value = item.get('value')
                    
                    # Initialize if not already in the dictionary
                    if item_name not in cf_items:
                        cf_items[item_name] = {}
                    
                    # Add the value for this period
                    cf_items[item_name][period_key] = value
            
            # Create a DataFrame from the collected data
            df = pd.DataFrame.from_dict(cf_items, orient='index')
            
            # Sort columns to have most recent first
            if not df.empty:
                df = df[sorted(df.columns, reverse=True)]
            
            return df
        else:
            return pd.DataFrame()
    
    except Exception as e:
        st.warning(f"Error processing cash flow data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_quarterly_results(symbol):
    """
    Fetch the quarterly results data from Screener.in
    
    Args:
        symbol (str): Stock symbol (with or without .NS/.BO suffix)
    
    Returns:
        pd.DataFrame: Quarterly results with quarters as columns and items as rows
    """
    company_data = fetch_screener_company_data(symbol)
    
    if not company_data or 'data' not in company_data:
        return pd.DataFrame()
    
    # Extract quarterly results data
    try:
        # Screener stores quarterly results in the 'data' section
        data = company_data['data']
        
        if 'quarters' in data:
            qtr_data = data['quarters']
            
            # Convert the data to a DataFrame
            periods = []
            qtr_items = {}
            
            # Initialize with the structure we need
            for period in qtr_data:
                period_key = period.get('c_name', 'Unknown')
                periods.append(period_key)
                
                # Process each item in the period
                for item in period.get('values', []):
                    item_name = item.get('name', 'Unknown')
                    value = item.get('value')
                    
                    # Initialize if not already in the dictionary
                    if item_name not in qtr_items:
                        qtr_items[item_name] = {}
                    
                    # Add the value for this period
                    qtr_items[item_name][period_key] = value
            
            # Create a DataFrame from the collected data
            df = pd.DataFrame.from_dict(qtr_items, orient='index')
            
            # Sort columns to have most recent first
            if not df.empty:
                df = df[sorted(df.columns, reverse=True)]
            
            return df
        else:
            return pd.DataFrame()
    
    except Exception as e:
        st.warning(f"Error processing quarterly results data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_peer_comparison(symbol):
    """
    Fetch peer comparison data from Screener.in
    
    Args:
        symbol (str): Stock symbol (with or without .NS/.BO suffix)
    
    Returns:
        pd.DataFrame: Peer comparison data with companies as rows and metrics as columns
    """
    company_data = fetch_screener_company_data(symbol)
    
    if not company_data or 'data' not in company_data:
        return pd.DataFrame(), []
    
    # Extract peer comparison data
    try:
        # Screener stores peer comparison in the 'data' section
        data = company_data['data']
        
        if 'peers' in data:
            peer_data = data['peers']
            
            # Process peer data into a DataFrame
            peers = []
            metrics = []
            
            # Extract metrics from the first peer (should be consistent)
            if peer_data and len(peer_data) > 0:
                first_peer = peer_data[0]
                for item in first_peer.get('values', []):
                    metrics.append(item.get('name', 'Unknown'))
            
            # Process each peer
            for peer in peer_data:
                peer_info = {}
                peer_info['Company'] = peer.get('name', 'Unknown')
                
                # Process each metric
                for item in peer.get('values', []):
                    metric_name = item.get('name', 'Unknown')
                    peer_info[metric_name] = item.get('value')
                
                peers.append(peer_info)
            
            # Create a DataFrame from the collected data
            df = pd.DataFrame(peers)
            
            # Get list of peer symbols
            peer_symbols = []
            if 'peer_cmp' in data:
                peer_symbols = [p.get('value', '') for p in data['peer_cmp']]
            
            return df, peer_symbols
        else:
            return pd.DataFrame(), []
    
    except Exception as e:
        st.warning(f"Error processing peer comparison data: {e}")
        return pd.DataFrame(), []

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_company_info(symbol):
    """
    Fetch general company information from Screener.in
    
    Args:
        symbol (str): Stock symbol (with or without .NS/.BO suffix)
    
    Returns:
        dict: Dictionary with company information
    """
    company_data = fetch_screener_company_data(symbol)
    
    if not company_data:
        return {}
    
    # Extract required company info
    result = {}
    
    # Basic info
    result['longName'] = company_data.get('name', 'N/A')
    
    # Process ratios
    if 'ratios' in company_data:
        ratios = company_data['ratios']
        
        # Map common ratios to our expected format
        ratio_mapping = {
            'CMP': 'currentPrice',
            'Market Cap': 'marketCap',
            'Stock P/E': 'trailingPE',
            'Book Value': 'bookValue',
            'Dividend Yield': 'dividendYield',
            'ROCE': 'returnOnEquity',
            'ROE': 'returnOnEquity',
            'Face Value': 'faceValue'
        }
        
        for screener_key, our_key in ratio_mapping.items():
            if screener_key in ratios:
                # Extract numeric values from text
                value_str = ratios[screener_key]
                numeric_value = re.findall(r'[-+]?\d*\.\d+|\d+', value_str)
                if numeric_value:
                    try:
                        result[our_key] = float(numeric_value[0])
                    except:
                        pass
    
    # Additional info from 'data' if available
    if 'data' in company_data:
        data = company_data['data']
        
        # Extract sector
        if 'warehouse_set' in data:
            warehouse = data['warehouse_set']
            if 'industry' in warehouse:
                result['sector'] = warehouse.get('industry', 'N/A')
            
        # Extract other company info
        if 'company' in data:
            company = data['company']
            if 'short_name' in company:
                result['shortName'] = company.get('short_name', 'N/A')
            if 'warehouse_set' in data and 'isin_code' in data['warehouse_set']:
                result['isin'] = data['warehouse_set'].get('isin_code', 'N/A')

    return result

@st.cache_data(ttl=3600)  # Cache for 1 hour
def format_pl_statement(pl_df, is_indian=True):
    """
    Format profit and loss statement data from Screener.in to the structure we need
    
    Args:
        pl_df (pd.DataFrame): Raw P&L data from Screener.in
        is_indian (bool): Whether it's an Indian stock
    
    Returns:
        pd.DataFrame: Formatted P&L statement with our standard rows
    """
    if pl_df.empty:
        return pd.DataFrame()
    
    # Define our standardized row structure
    std_rows = [
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
    
    # Create a mapping from Screener.in row names to our standardized names
    # These may vary but these are common ones
    row_mapping = {
        # Screener Key : Our Key
        "Sales": "Sales",
        "Revenue": "Sales",
        "Total Revenue": "Sales",
        "Total Income From Operations": "Sales",
        
        "Total Expenses": "Expenses",
        "Cost of Materials Consumed": "Expenses",
        "Operating Costs": "Expenses",
        
        "Operating Profit": "Operating Profit",
        "EBIT": "Operating Profit",
        "EBITDA": "Operating Profit",
        
        "OPM": "OPM %",
        "OPM%": "OPM %",
        "Operating Profit Margin": "OPM %",
        
        "Other Income": "Other Income",
        "Non Operating Income": "Other Income",
        
        "Interest": "Interest",
        "Finance Costs": "Interest",
        "Financial Charges": "Interest",
        
        "Depreciation": "Depreciation",
        "Depreciation and Amortization Expense": "Depreciation",
        
        "Profit Before Tax": "Profit before tax",
        "PBT": "Profit before tax",
        
        "Tax Rate": "Tax %",
        "Tax %": "Tax %",
        "Effective Tax Rate": "Tax %",
        
        "Net Profit": "Net Profit",
        "PAT": "Net Profit",
        "Profit After Tax": "Net Profit",
        
        "EPS": "EPS in Rs",
        "EPS in Rs": "EPS in Rs",
        "Basic EPS": "EPS in Rs",
        
        "Dividend Payout": "Dividend Payout %",
        "Dividend Payout %": "Dividend Payout %",
        "Dividend Payout Ratio": "Dividend Payout %"
    }
    
    # Create a new DataFrame with our standard structure
    result_df = pd.DataFrame(index=std_rows)
    
    # Copy over all columns from original data
    for col in pl_df.columns:
        result_df[col] = None
    
    # Map data from original DataFrame to our standard format
    for orig_row, std_row in row_mapping.items():
        if orig_row in pl_df.index:
            result_df.loc[std_row] = pl_df.loc[orig_row]
    
    # Calculate missing values where possible
    for col in result_df.columns:
        # Fill expenses if missing (Sales - Operating Profit)
        if (result_df.loc["Sales", col] is not None and 
            result_df.loc["Operating Profit", col] is not None and
            result_df.loc["Expenses", col] is None):
            result_df.loc["Expenses", col] = result_df.loc["Sales", col] - result_df.loc["Operating Profit", col]
        
        # Calculate OPM % if missing
        if (result_df.loc["Sales", col] is not None and 
            result_df.loc["Operating Profit", col] is not None and
            result_df.loc["OPM %", col] is None):
            if result_df.loc["Sales", col] != 0:
                result_df.loc["OPM %", col] = (result_df.loc["Operating Profit", col] / result_df.loc["Sales", col]) * 100
        
        # Calculate Tax % if missing (only if we have both Net Profit and Profit before tax)
        if (result_df.loc["Profit before tax", col] is not None and 
            result_df.loc["Net Profit", col] is not None and
            result_df.loc["Tax %", col] is None):
            pbt = result_df.loc["Profit before tax", col]
            pat = result_df.loc["Net Profit", col]
            if pbt != 0:
                result_df.loc["Tax %", col] = ((pbt - pat) / pbt) * 100
    
    # Format values for display
    formatted_df = result_df.copy()
    for col in formatted_df.columns:
        for idx in formatted_df.index:
            value = formatted_df.loc[idx, col]
            
            if pd.isna(value) or value is None:
                formatted_df.loc[idx, col] = "N/A"
            elif idx in ["OPM %", "Tax %", "Dividend Payout %"]:
                # Format percentages
                try:
                    formatted_df.loc[idx, col] = f"{int(round(value))}%"
                except:
                    formatted_df.loc[idx, col] = "N/A"
            elif idx == "EPS in Rs":
                # Format EPS with 2 decimal places
                try:
                    formatted_df.loc[idx, col] = f"{value:.2f}"
                except:
                    formatted_df.loc[idx, col] = "N/A"
            else:
                # Format financial values with commas - assumed in crores
                try:
                    formatted_df.loc[idx, col] = f"{int(round(value)):,}"
                except:
                    formatted_df.loc[idx, col] = "N/A"
    
    return formatted_df