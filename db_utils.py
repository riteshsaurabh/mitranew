import database as db
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

def initialize_database():
    """Initialize the database by creating all tables"""
    db.create_tables()
    print("Database tables created successfully")

def add_stock(symbol):
    """
    Add a stock to the database if it doesn't exist
    
    Args:
        symbol (str): Stock ticker symbol
        
    Returns:
        database.Stock: Stock database object
    """
    # Check if stock already exists
    existing_stock = db.session.query(db.Stock).filter_by(symbol=symbol.upper()).first()
    if existing_stock:
        return existing_stock
    
    # Get stock information from Yahoo Finance
    stock_info = yf.Ticker(symbol.upper()).info
    
    # Create new stock record
    new_stock = db.Stock(
        symbol=symbol.upper(),
        company_name=stock_info.get('longName', symbol.upper()),
        sector=stock_info.get('sector', None),
        industry=stock_info.get('industry', None),
        last_updated=datetime.utcnow()
    )
    
    db.session.add(new_stock)
    db.session.commit()
    
    return new_stock

def update_stock_prices(symbol, period="1y"):
    """
    Update stock prices in the database
    
    Args:
        symbol (str): Stock ticker symbol
        period (str): Time period to fetch data for
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get stock from database
        stock = db.session.query(db.Stock).filter_by(symbol=symbol.upper()).first()
        
        # If stock doesn't exist, add it
        if not stock:
            stock = add_stock(symbol)
        
        # Get historical data from Yahoo Finance
        yf_stock = yf.Ticker(symbol.upper())
        hist_data = yf_stock.history(period=period)
        
        if hist_data.empty:
            return False
        
        # Delete existing price history for this stock
        db.session.query(db.StockPrice).filter_by(stock_id=stock.id).delete()
        
        # Add new price records
        for date, row in hist_data.iterrows():
            # Convert date to datetime if it's not already
            if not isinstance(date, datetime):
                # Handle pd.Timestamp objects
                if hasattr(date, 'to_pydatetime'):
                    date = date.to_pydatetime()
                else:
                    # Convert to string first to avoid pandas type issues
                    date = datetime.strptime(str(date)[:19], "%Y-%m-%d %H:%M:%S")
            
            # Create new stock price record
            # Convert numpy types to Python native types safely
            try:
                open_price = float(row['Open']) if 'Open' in row else None
            except (TypeError, ValueError):
                open_price = None
                
            try:
                high_price = float(row['High']) if 'High' in row else None
            except (TypeError, ValueError):
                high_price = None
                
            try:
                low_price = float(row['Low']) if 'Low' in row else None
            except (TypeError, ValueError):
                low_price = None
                
            try:
                close_price = float(row['Close']) if 'Close' in row else None
            except (TypeError, ValueError):
                close_price = None
                
            try:
                volume = int(row['Volume']) if 'Volume' in row else None
            except (TypeError, ValueError):
                volume = None
            
            price = db.StockPrice(
                stock_id=stock.id,
                date=date,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume
            )
            
            db.session.add(price)
        
        # Update stock last_updated timestamp
        stock.last_updated = datetime.utcnow()
        
        # Commit changes
        db.session.commit()
        
        return True
    
    except Exception as e:
        print(f"Error updating stock prices: {e}")
        db.session.rollback()
        return False

def get_stored_stock_data(symbol, days=30):
    """
    Get stock data from the database
    
    Args:
        symbol (str): Stock ticker symbol
        days (int): Number of days of data to retrieve
        
    Returns:
        pandas.DataFrame: Stock price data
    """
    try:
        # Get stock from database
        stock = db.session.query(db.Stock).filter_by(symbol=symbol.upper()).first()
        
        if not stock:
            return pd.DataFrame()
        
        # Calculate start date
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get price data from database
        prices = db.session.query(db.StockPrice).filter(
            db.StockPrice.stock_id == stock.id,
            db.StockPrice.date >= start_date,
            db.StockPrice.date <= end_date
        ).order_by(db.StockPrice.date).all()
        
        if not prices:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = {
            'Open': [price.open_price for price in prices],
            'High': [price.high_price for price in prices],
            'Low': [price.low_price for price in prices],
            'Close': [price.close_price for price in prices],
            'Volume': [price.volume for price in prices]
        }
        
        df = pd.DataFrame(data, index=[price.date for price in prices])
        
        return df
    
    except Exception as e:
        print(f"Error getting stored stock data: {e}")
        return pd.DataFrame()

def create_user(username, email):
    """
    Create a new user
    
    Args:
        username (str): Username
        email (str): Email address
        
    Returns:
        database.User: User database object or None if error
    """
    try:
        # Check if user already exists
        existing_user = db.session.query(db.User).filter(
            (db.User.username == username) | (db.User.email == email)
        ).first()
        
        if existing_user:
            return None
        
        # Create new user
        new_user = db.User(
            username=username,
            email=email,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return new_user
    
    except Exception as e:
        print(f"Error creating user: {e}")
        db.session.rollback()
        return None

def create_watchlist(user_id, name, description=None):
    """
    Create a new watchlist for a user
    
    Args:
        user_id (int): User ID
        name (str): Watchlist name
        description (str): Watchlist description
        
    Returns:
        database.Watchlist: Watchlist database object or None if error
    """
    try:
        # Check if user exists
        user = db.session.query(db.User).filter_by(id=user_id).first()
        
        if not user:
            return None
        
        # Create new watchlist
        new_watchlist = db.Watchlist(
            user_id=user_id,
            name=name,
            description=description,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_watchlist)
        db.session.commit()
        
        return new_watchlist
    
    except Exception as e:
        print(f"Error creating watchlist: {e}")
        db.session.rollback()
        return None

def add_stock_to_watchlist(watchlist_id, symbol):
    """
    Add a stock to a watchlist
    
    Args:
        watchlist_id (int): Watchlist ID
        symbol (str): Stock ticker symbol
        
    Returns:
        database.WatchlistStock: WatchlistStock database object or None if error
    """
    try:
        # Check if watchlist exists
        watchlist = db.session.query(db.Watchlist).filter_by(id=watchlist_id).first()
        
        if not watchlist:
            return None
        
        # Get or add stock
        stock = db.session.query(db.Stock).filter_by(symbol=symbol.upper()).first()
        
        if not stock:
            stock = add_stock(symbol)
        
        # Check if stock is already in watchlist
        existing = db.session.query(db.WatchlistStock).filter_by(
            watchlist_id=watchlist_id,
            stock_id=stock.id
        ).first()
        
        if existing:
            return existing
        
        # Add stock to watchlist
        watchlist_stock = db.WatchlistStock(
            watchlist_id=watchlist_id,
            stock_id=stock.id,
            added_at=datetime.utcnow()
        )
        
        db.session.add(watchlist_stock)
        db.session.commit()
        
        return watchlist_stock
    
    except Exception as e:
        print(f"Error adding stock to watchlist: {e}")
        db.session.rollback()
        return None

def get_user_watchlists(user_id):
    """
    Get all watchlists for a user
    
    Args:
        user_id (int): User ID
        
    Returns:
        list: List of watchlist dictionaries
    """
    try:
        # Get watchlists
        watchlists = db.session.query(db.Watchlist).filter_by(user_id=user_id).all()
        
        result = []
        for watchlist in watchlists:
            # Get stocks in watchlist
            stocks_query = db.session.query(db.Stock).join(
                db.WatchlistStock,
                db.WatchlistStock.stock_id == db.Stock.id
            ).filter(
                db.WatchlistStock.watchlist_id == watchlist.id
            ).all()
            
            stocks = [{'symbol': stock.symbol, 'name': stock.company_name} for stock in stocks_query]
            
            result.append({
                'id': watchlist.id,
                'name': watchlist.name,
                'description': watchlist.description,
                'created_at': watchlist.created_at,
                'stocks': stocks
            })
        
        return result
    
    except Exception as e:
        print(f"Error getting user watchlists: {e}")
        return []

def add_stock_note(user_id, symbol, content):
    """
    Add a note to a stock
    
    Args:
        user_id (int): User ID
        symbol (str): Stock ticker symbol
        content (str): Note content
        
    Returns:
        database.StockNote: StockNote database object or None if error
    """
    try:
        # Check if user exists
        user = db.session.query(db.User).filter_by(id=user_id).first()
        
        if not user:
            return None
        
        # Get or add stock
        stock = db.session.query(db.Stock).filter_by(symbol=symbol.upper()).first()
        
        if not stock:
            stock = add_stock(symbol)
        
        # Create note
        note = db.StockNote(
            user_id=user_id,
            stock_id=stock.id,
            content=content,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(note)
        db.session.commit()
        
        return note
    
    except Exception as e:
        print(f"Error adding stock note: {e}")
        db.session.rollback()
        return None

def get_stock_notes(user_id, symbol):
    """
    Get all notes for a stock by a user
    
    Args:
        user_id (int): User ID
        symbol (str): Stock ticker symbol
        
    Returns:
        list: List of note dictionaries
    """
    try:
        # Get stock
        stock = db.session.query(db.Stock).filter_by(symbol=symbol.upper()).first()
        
        if not stock:
            return []
        
        # Get notes
        notes = db.session.query(db.StockNote).filter_by(
            user_id=user_id,
            stock_id=stock.id
        ).order_by(db.StockNote.created_at.desc()).all()
        
        result = [{
            'id': note.id,
            'content': note.content,
            'created_at': note.created_at,
            'updated_at': note.updated_at
        } for note in notes]
        
        return result
    
    except Exception as e:
        print(f"Error getting stock notes: {e}")
        return []

# Initialize the database
if __name__ == "__main__":
    initialize_database()
    print("Database initialization complete")