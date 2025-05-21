"""
Screener.in Integration Module

This module provides functions to fetch financial data from Screener.in for Indian stocks.
"""

import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
import streamlit as st

# Common Indian stock symbol mappings
SYMBOL_MAPPINGS = {
    "RELIANCE.NS": "RELIANCE",
    "TCS.NS": "TCS",
    "HDFCBANK.NS": "HDFCBANK",
    "INFY.NS": "INFY",
    "ICICIBANK.NS": "ICICIBANK",
    "SBIN.NS": "SBIN",
    "HINDUNILVR.NS": "HINDUNILVR",
    "BAJFINANCE.NS": "BAJFINANCE",
    "TATAMOTORS.NS": "TATAMOTORS",
    "TATASTEEL.NS": "TATASTEEL",
    "AXISBANK.NS": "AXISBANK"
}

def get_screener_symbol(symbol):
    """Convert stock symbol to Screener.in format"""
    # Remove exchange suffix
    base_symbol = symbol.replace('.NS', '').replace('.BO', '')
    
    # Use mapping if available
    if symbol in SYMBOL_MAPPINGS:
        return SYMBOL_MAPPINGS[symbol]
    
    return base_symbol

def fetch_data(symbol):
    """Fetch data from Screener.in for given stock symbol"""
    try:
        # Convert to Screener.in format
        screener_symbol = get_screener_symbol(symbol)
        url = f"https://www.screener.in/company/{screener_symbol}/"
        
        # Use a realistic user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        with st.spinner(f"Fetching data from Screener.in for {screener_symbol}..."):
            # Make the request
            response = requests.get(url, headers=headers, timeout=15)
            
            # Check if successful
            if response.status_code != 200:
                st.warning(f"Could not fetch data from Screener.in: Status code {response.status_code}")
                return None
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract financial data
            return extract_data(soup)
    
    except Exception as e:
        st.error(f"Error fetching data from Screener.in: {e}")
        return None

def extract_data(soup):
    """Extract financial data from the parsed HTML"""
    data = {
        'company_info': {},
        'profit_loss': pd.DataFrame(),
        'balance_sheet': pd.DataFrame(),
        'cash_flow': pd.DataFrame(),
        'ratios': {},
        'quarterly': pd.DataFrame()
    }
    
    # Company name
    name_element = soup.find('h1')
    if name_element:
        data['company_info']['name'] = name_element.text.strip()
    
    # Extract tables
    tables = soup.find_all('table', {'class': 'data-table'})
    
    # Process each table
    for table in tables:
        # Determine table type based on preceding heading
        table_type = get_table_type(table)
        if table_type:
            df = table_to_dataframe(table)
            if not df.empty:
                data[table_type] = df
    
    # Extract ratios
    ratios_section = soup.find('div', {'id': 'top-ratios'})
    if ratios_section:
        data['ratios'] = extract_ratios(ratios_section)
    
    # Extract JSON data if available (as backup)
    data['json_data'] = extract_json_data(soup)
    
    return data

def get_table_type(table):
    """Determine the type of financial table based on its heading"""
    # Look for the heading before the table
    prev_element = table.find_previous(['h2', 'h3', 'h4', 'h5', 'div'])
    
    if prev_element:
        heading_text = prev_element.text.strip().lower()
        
        # Determine table type
        if 'profit' in heading_text or 'loss' in heading_text or 'p&l' in heading_text:
            return 'profit_loss'
        elif 'balance' in heading_text:
            return 'balance_sheet'
        elif 'cash' in heading_text and 'flow' in heading_text:
            return 'cash_flow'
        elif 'quarter' in heading_text:
            return 'quarterly'
    
    # Check the first row of the table for clues
    first_row = table.find('tr')
    if first_row:
        cells = first_row.find_all(['th', 'td'])
        if cells:
            header_text = ' '.join([cell.text.strip().lower() for cell in cells])
            
            if 'revenue' in header_text or 'net profit' in header_text:
                return 'profit_loss'
            elif 'assets' in header_text or 'liabilities' in header_text:
                return 'balance_sheet'
            elif 'cash flow' in header_text:
                return 'cash_flow'
            elif 'quarter' in header_text:
                return 'quarterly'
    
    return None

def table_to_dataframe(table):
    """Convert an HTML table to a pandas DataFrame"""
    try:
        # Extract headers
        headers = []
        header_row = table.find('tr')
        if header_row:
            header_cells = header_row.find_all(['th', 'td'])
            headers = [cell.text.strip() for cell in header_cells]
        
        # Extract rows
        rows = []
        data_rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in data_rows:
            cells = row.find_all(['td', 'th'])
            cell_values = []
            
            for cell in cells:
                cell_text = cell.text.strip()
                
                # Try to convert numeric values
                if cell_text and cell_text != '-':
                    # Remove commas from numbers
                    clean_text = cell_text.replace(',', '')
                    
                    # Try to convert to float
                    try:
                        cell_value = float(clean_text)
                    except ValueError:
                        cell_value = cell_text
                else:
                    cell_value = None
                
                cell_values.append(cell_value)
            
            if len(cell_values) > 0:
                rows.append(cell_values)
        
        # Create DataFrame
        if headers and rows:
            df = pd.DataFrame(rows, columns=headers)
            
            # Set the first column as index if it contains row labels
            if len(df.columns) > 0:
                df.set_index(df.columns[0], inplace=True)
            
            return df
        
        return pd.DataFrame()
        
    except Exception as e:
        st.warning(f"Error converting table to DataFrame: {e}")
        return pd.DataFrame()

def extract_ratios(ratios_section):
    """Extract financial ratios from the ratios section"""
    ratios = {}
    
    try:
        ratio_items = ratios_section.find_all('li')
        
        for item in ratio_items:
            name_elem = item.find('span', {'class': 'name'})
            value_elem = item.find('span', {'class': 'value'})
            
            if name_elem and value_elem:
                name = name_elem.text.strip()
                value = value_elem.text.strip()
                
                # Try to convert to number
                try:
                    value_clean = value.replace(',', '')
                    if '%' in value_clean:
                        value_clean = value_clean.replace('%', '')
                        value = float(value_clean) / 100
                    else:
                        value = float(value_clean)
                except ValueError:
                    pass
                
                ratios[name] = value
        
        return ratios
    
    except Exception as e:
        st.warning(f"Error extracting ratios: {e}")
        return {}

def extract_json_data(soup):
    """Extract any embedded JSON data from script tags"""
    try:
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string and 'var data' in script.string:
                # Look for JSON data
                match = re.search(r'var\s+data\s*=\s*({.*?});', script.string, re.DOTALL)
                
                if match:
                    json_str = match.group(1)
                    
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
        
        return None
    
    except Exception as e:
        st.warning(f"Error extracting JSON data: {e}")
        return None

def format_pl_statement(data, is_indian=True):
    """Format profit and loss data into a standardized DataFrame"""
    # Get the profit and loss data
    raw_df = data.get('profit_loss', pd.DataFrame())
    
    if raw_df.empty:
        # Try to get from JSON data if table parsing failed
        json_data = data.get('json_data', {})
        if json_data and 'profit_and_loss' in json_data:
            return format_pl_from_json(json_data['profit_and_loss'], is_indian)
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
    
    # Create mapping of raw data rows to our standardized rows
    row_mapping = {
        # These are common in Screener.in data - add more as needed
        "Revenue": "Sales",
        "Total Revenue": "Sales",
        "Net Sales": "Sales",
        "Income": "Sales",
        
        "Total Expenses": "Expenses",
        "Expenses": "Expenses",
        "Operating Expenses": "Expenses",
        
        "Operating Profit": "Operating Profit",
        "EBITDA": "Operating Profit",
        
        "Other Income": "Other Income",
        
        "Interest": "Interest",
        "Finance Cost": "Interest",
        "Finance Costs": "Interest",
        
        "Depreciation": "Depreciation",
        "Depreciation & Amortization": "Depreciation",
        
        "Profit Before Tax": "Profit before tax",
        "PBT": "Profit before tax",
        
        "Tax": "Tax %",
        "Tax Expenses": "Tax %",
        
        "Net Profit": "Net Profit",
        "PAT": "Net Profit",
        
        "EPS": "EPS in Rs",
        "Basic EPS": "EPS in Rs",
        "Diluted EPS": "EPS in Rs",
        
        "Dividend Payout": "Dividend Payout %",
        "Dividend Payout Ratio": "Dividend Payout %"
    }
    
    # Create result DataFrame with our standard structure
    result_df = pd.DataFrame(index=std_rows)
    
    # Map data from raw DataFrame to our standardized format
    for col in raw_df.columns:
        result_df[col] = None
        
        for raw_row, std_row in row_mapping.items():
            if raw_row in raw_df.index:
                value = raw_df.loc[raw_row, col]
                if value is not None:
                    result_df.loc[std_row, col] = value
    
    # Calculate any missing values
    for col in result_df.columns:
        # Calculate expenses if missing
        if result_df.loc["Sales", col] is not None and result_df.loc["Operating Profit", col] is not None and result_df.loc["Expenses", col] is None:
            result_df.loc["Expenses", col] = result_df.loc["Sales", col] - result_df.loc["Operating Profit", col]
        
        # Calculate operating profit if missing
        if result_df.loc["Sales", col] is not None and result_df.loc["Expenses", col] is not None and result_df.loc["Operating Profit", col] is None:
            result_df.loc["Operating Profit", col] = result_df.loc["Sales", col] - result_df.loc["Expenses", col]
        
        # Calculate OPM %
        if result_df.loc["Sales", col] is not None and result_df.loc["Operating Profit", col] is not None and result_df.loc["Sales", col] != 0:
            result_df.loc["OPM %", col] = (result_df.loc["Operating Profit", col] / result_df.loc["Sales", col]) * 100
        
        # Calculate tax percentage
        if result_df.loc["Profit before tax", col] is not None and result_df.loc["Net Profit", col] is not None and result_df.loc["Profit before tax", col] != 0:
            tax_amount = result_df.loc["Profit before tax", col] - result_df.loc["Net Profit", col]
            if tax_amount > 0:  # Avoid negative tax rates
                result_df.loc["Tax %", col] = (tax_amount / result_df.loc["Profit before tax", col]) * 100
    
    # Format values for display
    display_df = result_df.copy()
    
    for col in display_df.columns:
        for idx in display_df.index:
            value = display_df.loc[idx, col]
            
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
    
    return display_df

def format_pl_from_json(json_data, is_indian=True):
    """Format P&L data from JSON if table parsing failed"""
    if not json_data:
        return pd.DataFrame()
    
    # Define our standardized rows
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
    
    # Create result DataFrame
    result_df = pd.DataFrame(index=std_rows)
    
    # Process each period
    for period in json_data:
        period_name = period.get('c_name', 'Unknown')
        result_df[period_name] = None
        
        # Process values
        values = period.get('values', [])
        
        # Create mapping
        value_map = {}
        for item in values:
            item_name = item.get('name', '')
            item_value = item.get('value')
            value_map[item_name] = item_value
        
        # Map to our standard format
        if 'Sales' in value_map:
            result_df.loc["Sales", period_name] = value_map['Sales']
        
        if 'Operating Profit' in value_map:
            result_df.loc["Operating Profit", period_name] = value_map['Operating Profit']
        
        if 'Net Profit' in value_map:
            result_df.loc["Net Profit", period_name] = value_map['Net Profit']
        
        # Calculate other values
        if result_df.loc["Sales", period_name] is not None and result_df.loc["Operating Profit", period_name] is not None:
            result_df.loc["Expenses", period_name] = result_df.loc["Sales", period_name] - result_df.loc["Operating Profit", period_name]
            
            if result_df.loc["Sales", period_name] != 0:
                result_df.loc["OPM %", period_name] = (result_df.loc["Operating Profit", period_name] / result_df.loc["Sales", period_name]) * 100
    
    # Format values for display
    display_df = result_df.copy()
    
    for col in display_df.columns:
        for idx in display_df.index:
            value = display_df.loc[idx, col]
            
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
    
    return display_df

def format_balance_sheet(data, is_indian=True):
    """Format balance sheet data into a standardized DataFrame"""
    # Get the balance sheet data
    raw_df = data.get('balance_sheet', pd.DataFrame())
    
    if raw_df.empty:
        return pd.DataFrame()
    
    # Define our standardized row structure
    std_rows = [
        "Equity Capital",
        "Reserves", 
        "Borrowings",
        "Other Liabilities",
        "Total Liabilities",
        "Fixed Assets",
        "CWIP",
        "Investments",
        "Other Assets",
        "Total Assets"
    ]
    
    # Create mapping of raw data rows to our standardized rows
    row_mapping = {
        "Share Capital": "Equity Capital",
        "Equity Share Capital": "Equity Capital",
        
        "Reserves and Surplus": "Reserves",
        "Other Equity": "Reserves",
        "Reserves": "Reserves",
        
        "Total Debt": "Borrowings",
        "Borrowings": "Borrowings",
        "Long Term Borrowings": "Borrowings",
        
        "Other Liabilities": "Other Liabilities",
        "Current Liabilities": "Other Liabilities",
        
        "Total Liabilities": "Total Liabilities",
        
        "Fixed Assets": "Fixed Assets",
        "Property Plant and Equipment": "Fixed Assets",
        "Net Block": "Fixed Assets",
        
        "Capital Work-in-Progress": "CWIP",
        "CWIP": "CWIP",
        
        "Investments": "Investments",
        "Non-current Investments": "Investments",
        
        "Other Assets": "Other Assets",
        "Current Assets": "Other Assets",
        
        "Total Assets": "Total Assets"
    }
    
    # Create result DataFrame with our standard structure
    result_df = pd.DataFrame(index=std_rows)
    
    # Map data from raw DataFrame to our standardized format
    for col in raw_df.columns:
        result_df[col] = None
        
        for raw_row, std_row in row_mapping.items():
            if raw_row in raw_df.index:
                value = raw_df.loc[raw_row, col]
                if value is not None:
                    result_df.loc[std_row, col] = value
    
    # Fill missing totals if we have the components
    for col in result_df.columns:
        # Calculate Total Liabilities if missing
        components_present = (
            result_df.loc["Equity Capital", col] is not None and
            result_df.loc["Reserves", col] is not None and
            result_df.loc["Borrowings", col] is not None and
            result_df.loc["Other Liabilities", col] is not None
        )
        
        if components_present and result_df.loc["Total Liabilities", col] is None:
            result_df.loc["Total Liabilities", col] = (
                result_df.loc["Equity Capital", col] +
                result_df.loc["Reserves", col] +
                result_df.loc["Borrowings", col] +
                result_df.loc["Other Liabilities", col]
            )
            
        # Calculate Total Assets if missing
        components_present = (
            result_df.loc["Fixed Assets", col] is not None and
            result_df.loc["CWIP", col] is not None and
            result_df.loc["Investments", col] is not None and
            result_df.loc["Other Assets", col] is not None
        )
        
        if components_present and result_df.loc["Total Assets", col] is None:
            result_df.loc["Total Assets", col] = (
                result_df.loc["Fixed Assets", col] +
                result_df.loc["CWIP", col] +
                result_df.loc["Investments", col] +
                result_df.loc["Other Assets", col]
            )
    
    # Format values for display
    display_df = result_df.copy()
    
    for col in display_df.columns:
        for idx in display_df.index:
            value = display_df.loc[idx, col]
            
            if pd.isna(value) or value is None:
                display_df.loc[idx, col] = "N/A"
            else:
                # Format financial values with commas
                try:
                    display_df.loc[idx, col] = f"{int(round(value)):,}"
                except:
                    display_df.loc[idx, col] = "N/A"
    
    return display_df

def format_cash_flow(data, is_indian=True):
    """Format cash flow data into a standardized DataFrame"""
    # Get the cash flow data
    raw_df = data.get('cash_flow', pd.DataFrame())
    
    if raw_df.empty:
        return pd.DataFrame()
    
    # Define our standardized row structure
    std_rows = [
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
    
    # Create mapping of raw data rows to our standardized rows
    row_mapping = {
        "Cash from Operations": "Cash from Operating Activity",
        "Cash from Operating Activities": "Cash from Operating Activity",
        "Net Cash Flow from Operating Activities": "Cash from Operating Activity",
        
        "Profit Before Tax": "Profit from operations",
        "Net Profit": "Profit from operations",
        
        "Working Capital Changes": "Working capital changes",
        "Change in Working Capital": "Working capital changes",
        
        "Direct Taxes Paid": "Direct taxes",
        "Income Taxes Paid": "Direct taxes",
        
        "Cash from Investing": "Cash from Investing Activity",
        "Cash from Investing Activities": "Cash from Investing Activity",
        "Net Cash Flow from Investing Activities": "Cash from Investing Activity",
        
        "Fixed Assets": "Fixed assets",
        "Purchase of Fixed Assets": "Fixed assets",
        
        "Purchase of Investments": "Investments",
        "Sale of Investments": "Investments",
        
        "Cash from Financing": "Cash from Financing Activity",
        "Cash from Financing Activities": "Cash from Financing Activity",
        "Net Cash Flow from Financing Activities": "Cash from Financing Activity",
        
        "Borrowings": "Borrowings",
        "Proceeds from Borrowings": "Borrowings",
        
        "Dividend Paid": "Dividend",
        "Dividends Paid": "Dividend",
        
        "Net Cash Flow": "Net Cash Flow",
        "Net Increase in Cash": "Net Cash Flow"
    }
    
    # Create result DataFrame with our standard structure
    result_df = pd.DataFrame(index=std_rows)
    
    # Map data from raw DataFrame to our standardized format
    for col in raw_df.columns:
        result_df[col] = None
        
        for raw_row, std_row in row_mapping.items():
            if raw_row in raw_df.index:
                value = raw_df.loc[raw_row, col]
                if value is not None:
                    result_df.loc[std_row, col] = value
    
    # Format values for display
    display_df = result_df.copy()
    
    for col in display_df.columns:
        for idx in display_df.index:
            value = display_df.loc[idx, col]
            
            if pd.isna(value) or value is None:
                display_df.loc[idx, col] = "N/A"
            else:
                # Format financial values with commas
                try:
                    display_df.loc[idx, col] = f"{int(round(value)):,}"
                except:
                    display_df.loc[idx, col] = "N/A"
    
    return display_df

def get_company_info(data):
    """Extract and format company information"""
    company_info = {}
    
    # Basic info
    company_info['name'] = data.get('company_info', {}).get('name', 'N/A')
    
    # Extract from ratios
    ratios = data.get('ratios', {})
    if ratios:
        # Map ratio fields to our expected format
        ratio_mapping = {
            'Market Cap': 'marketCap',
            'Current Price': 'currentPrice',
            'P/E': 'trailingPE',
            'Book Value (Rs)': 'bookValue',
            'Dividend Yield': 'dividendYield',
            'ROCE': 'returnOnEquity',
            'ROE': 'returnOnEquity',
            'Face Value': 'faceValue',
            'Industry': 'industry',
            'Sector': 'sector'
        }
        
        for key, target in ratio_mapping.items():
            if key in ratios:
                company_info[target] = ratios[key]
    
    return company_info