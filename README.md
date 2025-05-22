# Money-Mitra Finance Dashboard

A financial analysis dashboard for stock market data.

## Setup

1. Install dependencies:
```
pip install streamlit pandas yfinance plotly numpy requests
```

2. Set up environment variables (for EODHD API):
```
# Linux/Mac
export EODHD_API_KEY="your_api_key_here"

# Windows
set EODHD_API_KEY=your_api_key_here
```

## Running the app

```
streamlit run combined_app.py
```

## Features

- Stock price charts with candlesticks and moving averages
- Company overview information
- Financial statements (income statement, balance sheet, cash flow)
- News and analyst recommendations
- Support for US, NSE, and BSE listed stocks
- Multiple data sources (Yahoo Finance and EODHD)

## Security Note

Never commit API keys to version control. Use environment variables or the app's UI to provide the EODHD API key. 