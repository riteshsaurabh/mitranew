"""
Financial Statements Module for MoneyMitra Dashboard

This module provides functions to fetch and format financial statements
including profit & loss statements, balance sheets, and cash flow statements.
"""

import pandas as pd
import yfinance as yf
import streamlit as st
import format_utils

def get_income_statement(symbol, is_indian=False):
    """
    Get income statement (profit & loss) data for a company
    
    Args:
        symbol (str): Stock symbol
        is_indian (bool): Whether it's an Indian stock
        
    Returns:
        pd.DataFrame: Formatted income statement
    """
    try:
        # Get the ticker data
        ticker = yf.Ticker(symbol)
        
        # Try different endpoints to get the most data
        income_data = ticker.income_stmt
        
        if income_data is None or income_data.empty:
            income_data = ticker.financials
        
        if income_data is None or income_data.empty:
            # Try quarterly data
            income_data = ticker.quarterly_income_stmt
            if income_data is None or income_data.empty:
                income_data = ticker.quarterly_financials
        
        if income_data is not None and not income_data.empty:
            # Format the columns - convert dates to string format
            if isinstance(income_data.columns, pd.DatetimeIndex):
                income_data.columns = income_data.columns.strftime('%b %Y')
            
            # Prepare the data - we want a good-looking P&L statement
            # Create a standardized P&L format with key metrics
            pl_items = [
                "Total Revenue", 
                "Cost of Revenue",
                "Gross Profit",
                "Operating Expense",
                "Operating Income",
                "Interest Expense", 
                "Income Before Tax",
                "Income Tax Expense", 
                "Net Income",
                "Basic EPS",
                "Diluted EPS"
            ]
            
            # Create a new DataFrame with our desired metrics
            pl_data = pd.DataFrame(index=pl_items)
            
            # Map Yahoo Finance data to our format
            mapping = {
                "Total Revenue": ["Total Revenue", "Revenue"],
                "Cost of Revenue": ["Cost of Revenue", "Cost Of Revenue"],
                "Gross Profit": ["Gross Profit"],
                "Operating Expense": ["Operating Expense", "Total Operating Expenses"],
                "Operating Income": ["Operating Income", "EBIT"],
                "Interest Expense": ["Interest Expense"],
                "Income Before Tax": ["Income Before Tax", "Pretax Income"],
                "Income Tax Expense": ["Income Tax Expense", "Tax Provision"],
                "Net Income": ["Net Income", "Net Income Common Stockholders"],
                "Basic EPS": ["Basic EPS"],
                "Diluted EPS": ["Diluted EPS", "EPS - Earnings Per Share"]
            }
            
            # Get the most recent 4 reporting periods
            columns_to_use = income_data.columns[:4]
            
            # Fill in our P&L DataFrame
            for pl_item in pl_items:
                found = False
                for possible_key in mapping[pl_item]:
                    if possible_key in income_data.index:
                        for col in columns_to_use:
                            value = income_data.loc[possible_key, col]
                            if is_indian:
                                # Convert to crores for Indian stocks
                                value = value / 10000000 if not pd.isna(value) else None
                            else:
                                # Convert to millions for other stocks
                                value = value / 1000000 if not pd.isna(value) else None
                            pl_data.loc[pl_item, col] = value
                        found = True
                        break
                
                if not found:
                    # If we didn't find a match, fill with None
                    for col in columns_to_use:
                        pl_data.loc[pl_item, col] = None
            
            # Format values for display - ensure consistent decimal places
            for col in pl_data.columns:
                for idx in pl_data.index:
                    val = pl_data.loc[idx, col]
                    if pd.notna(val) and isinstance(val, (int, float)):
                        pl_data.loc[idx, col] = format_utils.format_number(float(val))
            
            return pl_data
        else:
            return None
    except Exception as e:
        st.error(f"Error retrieving income statement: {str(e)}")
        return None

def get_balance_sheet(symbol, is_indian=False):
    """
    Get balance sheet data for a company
    
    Args:
        symbol (str): Stock symbol
        is_indian (bool): Whether it's an Indian stock
        
    Returns:
        pd.DataFrame: Formatted balance sheet
    """
    try:
        # Get the ticker data
        ticker = yf.Ticker(symbol)
        
        # Try different endpoints to get the most data
        bs_data = ticker.balance_sheet
        
        if bs_data is None or bs_data.empty:
            # Try quarterly data
            bs_data = ticker.quarterly_balance_sheet
        
        if bs_data is not None and not bs_data.empty:
            # Format the columns - convert dates to string format
            if isinstance(bs_data.columns, pd.DatetimeIndex):
                bs_data.columns = bs_data.columns.strftime('%b %Y')
            
            # Prepare the data - we want a good-looking balance sheet
            # Create a standardized balance sheet format with key metrics
            bs_items = [
                "Total Assets",
                "Total Current Assets",
                "Cash And Cash Equivalents",
                "Inventory",
                "Net Receivables",
                "Total Non Current Assets",
                "Property Plant & Equipment",
                "Investments",
                "Goodwill",
                "Total Liabilities",
                "Total Current Liabilities",
                "Accounts Payable",
                "Short Term Debt",
                "Total Non Current Liabilities",
                "Long Term Debt",
                "Total Stockholder Equity",
                "Retained Earnings",
                "Common Stock",
            ]
            
            # Create a new DataFrame with our desired metrics
            bs_data_clean = pd.DataFrame(index=bs_items)
            
            # Map Yahoo Finance data to our format
            mapping = {
                "Total Assets": ["Total Assets"],
                "Total Current Assets": ["Total Current Assets"],
                "Cash And Cash Equivalents": ["Cash And Cash Equivalents", "Cash"],
                "Inventory": ["Inventory"],
                "Net Receivables": ["Net Receivables"],
                "Total Non Current Assets": ["Total Non Current Assets"],
                "Property Plant & Equipment": ["Property Plant & Equipment", "Net PPE"],
                "Investments": ["Investments", "Long Term Investments"],
                "Goodwill": ["Goodwill"], 
                "Total Liabilities": ["Total Liabilities"],
                "Total Current Liabilities": ["Total Current Liabilities"],
                "Accounts Payable": ["Accounts Payable"],
                "Short Term Debt": ["Short Term Debt"],
                "Total Non Current Liabilities": ["Total Non Current Liabilities", "Long Term Liabilities"],
                "Long Term Debt": ["Long Term Debt"],
                "Total Stockholder Equity": ["Total Stockholder Equity", "Stockholders Equity"],
                "Retained Earnings": ["Retained Earnings"],
                "Common Stock": ["Common Stock"]
            }
            
            # Get the most recent 4 reporting periods
            columns_to_use = bs_data.columns[:4]
            
            # Fill in our balance sheet DataFrame
            for bs_item in bs_items:
                found = False
                for possible_key in mapping[bs_item]:
                    if possible_key in bs_data.index:
                        for col in columns_to_use:
                            value = bs_data.loc[possible_key, col]
                            if is_indian:
                                # Convert to crores for Indian stocks
                                value = value / 10000000 if not pd.isna(value) else None
                            else:
                                # Convert to millions for other stocks
                                value = value / 1000000 if not pd.isna(value) else None
                            bs_data_clean.loc[bs_item, col] = value
                        found = True
                        break
                
                if not found:
                    # If we didn't find a match, fill with None
                    for col in columns_to_use:
                        bs_data_clean.loc[bs_item, col] = None
            
            # Format values for display - ensure consistent decimal places
            for col in bs_data_clean.columns:
                for idx in bs_data_clean.index:
                    val = bs_data_clean.loc[idx, col]
                    if pd.notna(val) and isinstance(val, (int, float)):
                        bs_data_clean.loc[idx, col] = format_utils.format_number(float(val))
            
            return bs_data_clean
        else:
            return None
    except Exception as e:
        st.error(f"Error retrieving balance sheet: {str(e)}")
        return None

def get_cash_flow(symbol, is_indian=False):
    """
    Get cash flow statement data for a company
    
    Args:
        symbol (str): Stock symbol
        is_indian (bool): Whether it's an Indian stock
        
    Returns:
        pd.DataFrame: Formatted cash flow statement
    """
    try:
        # Get the ticker data
        ticker = yf.Ticker(symbol)
        
        # Try to get cash flow data
        cf_data = ticker.cashflow
        
        if cf_data is None or cf_data.empty:
            # Try quarterly data
            cf_data = ticker.quarterly_cashflow
        
        if cf_data is not None and not cf_data.empty:
            # Format the columns - convert dates to string format
            if isinstance(cf_data.columns, pd.DatetimeIndex):
                cf_data.columns = cf_data.columns.strftime('%b %Y')
            
            # Prepare the data - we want a good-looking cash flow statement
            # Create a standardized cash flow format with key metrics
            cf_items = [
                "Operating Cash Flow",
                "Net Income",
                "Depreciation And Amortization",
                "Change In Working Capital",
                "Investing Cash Flow",
                "Capital Expenditure",
                "Acquisitions",
                "Purchase Of Investment",
                "Sale Of Investment",
                "Financing Cash Flow",
                "Dividend Payout",
                "Stock Repurchase",
                "Debt Repayment",
                "Free Cash Flow"
            ]
            
            # Create a new DataFrame with our desired metrics
            cf_data_clean = pd.DataFrame(index=cf_items)
            
            # Map Yahoo Finance data to our format
            mapping = {
                "Operating Cash Flow": ["Operating Cash Flow", "Total Cash From Operating Activities"],
                "Net Income": ["Net Income", "Net Income From Continuing Operations"],
                "Depreciation And Amortization": ["Depreciation And Amortization", "Depreciation"],
                "Change In Working Capital": ["Change In Working Capital"],
                "Investing Cash Flow": ["Investing Cash Flow", "Total Cash From Investing Activities"],
                "Capital Expenditure": ["Capital Expenditure", "Capital Expenditures"],
                "Acquisitions": ["Acquisitions", "Acquisitions Net"],
                "Purchase Of Investment": ["Purchase Of Investment", "Investments In Property Plant And Equipment"],
                "Sale Of Investment": ["Sale Of Investment", "Sale Of Investment Property"],
                "Financing Cash Flow": ["Financing Cash Flow", "Total Cash From Financing Activities"],
                "Dividend Payout": ["Dividend Payout", "Dividends Paid"],
                "Stock Repurchase": ["Stock Repurchase", "Repurchase Of Stock"],
                "Debt Repayment": ["Debt Repayment", "Repayments Of Long Term Debt"],
                "Free Cash Flow": ["Free Cash Flow"]
            }
            
            # Get the most recent 4 reporting periods
            columns_to_use = cf_data.columns[:4]
            
            # Fill in our cash flow DataFrame
            for cf_item in cf_items:
                found = False
                for possible_key in mapping[cf_item]:
                    if possible_key in cf_data.index:
                        for col in columns_to_use:
                            value = cf_data.loc[possible_key, col]
                            if is_indian:
                                # Convert to crores for Indian stocks
                                value = value / 10000000 if not pd.isna(value) else None
                            else:
                                # Convert to millions for other stocks
                                value = value / 1000000 if not pd.isna(value) else None
                            cf_data_clean.loc[cf_item, col] = value
                        found = True
                        break
                
                if not found:
                    # If we didn't find a match, fill with None
                    for col in columns_to_use:
                        cf_data_clean.loc[cf_item, col] = None
            
            # Format values for display - ensure consistent decimal places
            for col in cf_data_clean.columns:
                for idx in cf_data_clean.index:
                    val = cf_data_clean.loc[idx, col]
                    if pd.notna(val) and isinstance(val, (int, float)):
                        cf_data_clean.loc[idx, col] = format_utils.format_number(float(val))
            
            return cf_data_clean
        else:
            return None
    except Exception as e:
        st.error(f"Error retrieving cash flow statement: {str(e)}")
        return None

def display_financial_statement(df, title, statement_type):
    """
    Display a financial statement with proper formatting
    
    Args:
        df (pd.DataFrame): Financial statement dataframe
        title (str): Title to display
        statement_type (str): Type of statement ('pl', 'bs', or 'cf')
    """
    if df is None or df.empty:
        st.warning(f"No {title} data available for this stock.")
        return
    
    # Create HTML styling
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
    </style>
    """, unsafe_allow_html=True)
    
    # Highlight important rows based on statement type
    if statement_type == 'pl':
        # P&L statement bold rows
        st.markdown("""
        <style>
        .dataframe tr:nth-child(3), .dataframe tr:nth-child(9), .dataframe tr:nth-child(11) {
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
    elif statement_type == 'bs':
        # Balance sheet bold rows
        st.markdown("""
        <style>
        .dataframe tr:nth-child(1), .dataframe tr:nth-child(10), .dataframe tr:nth-child(16) {
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
    elif statement_type == 'cf':
        # Cash flow bold rows
        st.markdown("""
        <style>
        .dataframe tr:nth-child(1), .dataframe tr:nth-child(5), .dataframe tr:nth-child(10) {
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Display the table
    st.write(df.to_html(classes='dataframe', escape=False), unsafe_allow_html=True)