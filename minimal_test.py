import yfinance as yf

print("Testing yfinance...")
msft = yf.Ticker("MSFT")
print("Downloaded MSFT ticker information")
print(f"Company name: {msft.info.get('shortName', 'Not found')}")
print("Test completed successfully") 