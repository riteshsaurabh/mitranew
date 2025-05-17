import db_utils
import database as db

print("Initializing database...")
db_utils.initialize_database()

print("Adding sample data...")
# Create a demo user
user = db_utils.create_user("demo_user", "demo@example.com")
if user:
    print(f"Created demo user with ID: {user.id}")
    
    # Create a default watchlist
    watchlist = db_utils.create_watchlist(user.id, "My Watchlist", "Default watchlist for technology stocks")
    if watchlist:
        print(f"Created watchlist: {watchlist.name}")
        
        # Add some popular stocks to the watchlist
        for symbol in ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]:
            result = db_utils.add_stock_to_watchlist(watchlist.id, symbol)
            if result:
                print(f"Added {symbol} to watchlist")
            
            # Update stock prices in the database
            price_update = db_utils.update_stock_prices(symbol)
            if price_update:
                print(f"Updated prices for {symbol}")

print("Database initialization complete!")