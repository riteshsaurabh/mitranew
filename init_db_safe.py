import os
import sys
import time
from database import Base, engine, User, Stock, StockPrice, Watchlist, WatchlistStock, StockNote
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(engine)
        print("Database tables created successfully")
        return True
    except SQLAlchemyError as e:
        print(f"Error creating tables: {e}")
        return False

def create_demo_user():
    """Create a demo user if no users exist"""
    from database import session
    
    try:
        # Check if any users exist
        user_count = session.query(User).count()
        
        if user_count == 0:
            # Create demo user
            demo_user = User(
                username="demo_user",
                email="demo@example.com",
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            
            session.add(demo_user)
            session.commit()
            
            print(f"Created demo user with ID: {demo_user.id}")
            return demo_user
        else:
            # Get the first user
            user = session.query(User).first()
            print(f"Using existing user: {user.username}")
            return user
            
    except SQLAlchemyError as e:
        print(f"Error creating demo user: {e}")
        session.rollback()
        return None

def create_default_watchlist(user_id):
    """Create a default watchlist for the user if none exists"""
    from database import session
    
    try:
        # Check if user has any watchlists
        watchlist_count = session.query(Watchlist).filter_by(user_id=user_id).count()
        
        if watchlist_count == 0:
            # Create default watchlist
            watchlist = Watchlist(
                user_id=user_id,
                name="My Watchlist",
                description="Popular technology stocks",
                created_at=datetime.utcnow()
            )
            
            session.add(watchlist)
            session.commit()
            
            print(f"Created default watchlist: {watchlist.name}")
            return watchlist
        else:
            # Get the first watchlist
            watchlist = session.query(Watchlist).filter_by(user_id=user_id).first()
            print(f"Using existing watchlist: {watchlist.name}")
            return watchlist
            
    except SQLAlchemyError as e:
        print(f"Error creating default watchlist: {e}")
        session.rollback()
        return None

def add_stock_to_db(symbol):
    """Add a stock to the database if it doesn't exist"""
    from database import session
    import yfinance as yf
    
    try:
        # Check if stock already exists
        existing_stock = session.query(Stock).filter_by(symbol=symbol.upper()).first()
        
        if existing_stock:
            print(f"Using existing stock: {existing_stock.symbol}")
            return existing_stock
        
        # Get stock info from Yahoo Finance
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        # Create new stock
        stock = Stock(
            symbol=symbol.upper(),
            company_name=info.get('longName', symbol.upper()),
            sector=info.get('sector'),
            industry=info.get('industry'),
            last_updated=datetime.utcnow()
        )
        
        session.add(stock)
        session.commit()
        
        print(f"Added stock: {stock.symbol}")
        return stock
        
    except Exception as e:
        print(f"Error adding stock {symbol}: {e}")
        session.rollback()
        return None

def add_stock_to_watchlist(watchlist_id, stock_id):
    """Add a stock to a watchlist if it's not already in it"""
    from database import session
    
    try:
        # Check if stock is already in watchlist
        existing = session.query(WatchlistStock).filter_by(
            watchlist_id=watchlist_id,
            stock_id=stock_id
        ).first()
        
        if existing:
            return existing
        
        # Add stock to watchlist
        watchlist_stock = WatchlistStock(
            watchlist_id=watchlist_id,
            stock_id=stock_id,
            added_at=datetime.utcnow()
        )
        
        session.add(watchlist_stock)
        session.commit()
        
        return watchlist_stock
        
    except SQLAlchemyError as e:
        print(f"Error adding stock to watchlist: {e}")
        session.rollback()
        return None

def main():
    """Initialize the database with sample data"""
    # Create tables
    if not create_tables():
        print("Failed to create database tables. Exiting.")
        return
    
    # Create demo user
    user = create_demo_user()
    if not user:
        print("Failed to create or find demo user. Exiting.")
        return
    
    # Create default watchlist
    watchlist = create_default_watchlist(user.id)
    if not watchlist:
        print("Failed to create or find default watchlist. Exiting.")
        return
    
    # Add popular stocks
    popular_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    
    for symbol in popular_stocks:
        stock = add_stock_to_db(symbol)
        if stock:
            watchlist_stock = add_stock_to_watchlist(watchlist.id, stock.id)
            if watchlist_stock:
                print(f"Added {symbol} to watchlist")
    
    print("Database initialization complete!")

if __name__ == "__main__":
    # Add a short delay to ensure database connection is ready
    time.sleep(1)
    main()