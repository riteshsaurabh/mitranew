"""
Financial Data Module for MoneyMitra Dashboard

This module provides direct functions to fetch financial data from Yahoo Finance
including income statements, balance sheets, and cash flow statements.
"""

import yfinance as yf
import pandas as pd
import streamlit as st
import format_utils

def get_income_statement(symbol, is_indian=False):
    """
    Fetch income statement data for a company directly from Yahoo Finance
    
    Args:
        symbol (str): Stock symbol
        is_indian (bool): Whether it's an Indian stock
        
    Returns:
        pd.DataFrame: Formatted income statement
    """
    try:
        # Get the ticker object
        ticker = yf.Ticker(symbol)
        
        # Get income statement (financials)
        income_stmt = ticker.financials
        
        if income_stmt is None or income_stmt.empty:
            # Try income_stmt property
            income_stmt = ticker.income_stmt
            
            if income_stmt is None or income_stmt.empty:
                # Try quarterly data as fallback
                income_stmt = ticker.quarterly_financials
                if income_stmt is None or income_stmt.empty:
                    income_stmt = ticker.quarterly_income_stmt

        if income_stmt is not None and not income_stmt.empty:
            # Convert to millions or crores
            scale_factor = 10000000 if is_indian else 1000000  # ₹ Crores for Indian, $ Millions for others
            
            # Format the data
            df = income_stmt.copy()
            
            # Make sure columns are dates
            if isinstance(df.columns, pd.DatetimeIndex):
                df.columns = df.columns.strftime('%b %Y')
                
            # Get up to 5 most recent columns
            if len(df.columns) > 5:
                df = df[df.columns[:5]]
                
            # Scale values
            for col in df.columns:
                df[col] = df[col].apply(lambda x: x / scale_factor if pd.notna(x) else None)
                
            # Format numbers to 2 decimal places for display
            for col in df.columns:
                for idx in df.index:
                    val = df.loc[idx, col]
                    if pd.notna(val):
                        df.loc[idx, col] = format_utils.format_number(val)
                        
            return df
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching income statement: {str(e)}")
        return None
        
def get_balance_sheet(symbol, is_indian=False):
    """
    Fetch balance sheet data for a company directly from Yahoo Finance
    
    Args:
        symbol (str): Stock symbol
        is_indian (bool): Whether it's an Indian stock
        
    Returns:
        pd.DataFrame: Formatted balance sheet
    """
    try:
        # Get the ticker object
        ticker = yf.Ticker(symbol)
        
        # Get balance sheet
        balance_sheet = ticker.balance_sheet
        
        if balance_sheet is None or balance_sheet.empty:
            # Try quarterly data as fallback
            balance_sheet = ticker.quarterly_balance_sheet

        if balance_sheet is not None and not balance_sheet.empty:
            # Convert to millions or crores
            scale_factor = 10000000 if is_indian else 1000000  # ₹ Crores for Indian, $ Millions for others
            
            # Format the data
            df = balance_sheet.copy()
            
            # Make sure columns are dates
            if isinstance(df.columns, pd.DatetimeIndex):
                df.columns = df.columns.strftime('%b %Y')
                
            # Get up to 5 most recent columns
            if len(df.columns) > 5:
                df = df[df.columns[:5]]
                
            # Scale values
            for col in df.columns:
                df[col] = df[col].apply(lambda x: x / scale_factor if pd.notna(x) else None)
                
            # Format numbers to 2 decimal places for display
            for col in df.columns:
                for idx in df.index:
                    val = df.loc[idx, col]
                    if pd.notna(val):
                        df.loc[idx, col] = format_utils.format_number(val)
                        
            return df
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching balance sheet: {str(e)}")
        return None
        
def get_cash_flow(symbol, is_indian=False):
    """
    Fetch cash flow data for a company directly from Yahoo Finance
    
    Args:
        symbol (str): Stock symbol
        is_indian (bool): Whether it's an Indian stock
        
    Returns:
        pd.DataFrame: Formatted cash flow statement
    """
    try:
        # Get the ticker object
        ticker = yf.Ticker(symbol)
        
        # Get cash flow statement
        cash_flow = ticker.cashflow
        
        if cash_flow is None or cash_flow.empty:
            # Try quarterly data as fallback
            cash_flow = ticker.quarterly_cashflow

        if cash_flow is not None and not cash_flow.empty:
            # Convert to millions or crores
            scale_factor = 10000000 if is_indian else 1000000  # ₹ Crores for Indian, $ Millions for others
            
            # Format the data
            df = cash_flow.copy()
            
            # Make sure columns are dates
            if isinstance(df.columns, pd.DatetimeIndex):
                df.columns = df.columns.strftime('%b %Y')
                
            # Get up to 5 most recent columns
            if len(df.columns) > 5:
                df = df[df.columns[:5]]
                
            # Scale values
            for col in df.columns:
                df[col] = df[col].apply(lambda x: x / scale_factor if pd.notna(x) else None)
                
            # Format numbers to 2 decimal places for display
            for col in df.columns:
                for idx in df.index:
                    val = df.loc[idx, col]
                    if pd.notna(val):
                        df.loc[idx, col] = format_utils.format_number(val)
                        
            return df
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching cash flow statement: {str(e)}")
        return None