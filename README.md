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

## Deployment Options

### GitHub

1. Fork or clone this repository
2. Push your changes to GitHub
3. Set up Streamlit Cloud to deploy directly from your GitHub repository

### Streamlit Cloud

1. Visit [Streamlit Cloud](https://streamlit.io/cloud)
2. Connect your GitHub account
3. Select this repository
4. Deploy the app
5. Set the EODHD_API_KEY in the Streamlit Cloud secrets management

### Netlify (Static Hosting Only)

This repository includes a basic redirect for Netlify deployment:

1. Connect your GitHub repository to Netlify
2. Use the default settings in netlify.toml
3. Deploy

Note: Netlify will only host the static HTML redirect to your Streamlit deployment.

## Features

- Stock price charts with candlesticks and moving averages
- Company overview information
- Financial statements (income statement, balance sheet, cash flow)
- News and analyst recommendations
- Support for US, NSE, and BSE listed stocks
- Multiple data sources (Yahoo Finance and EODHD)

## Security Note

Never commit API keys to version control. Use environment variables or the app's UI to provide the EODHD API key. 