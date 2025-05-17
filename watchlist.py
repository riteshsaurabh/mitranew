import streamlit as st
import database as db
from database import session, User, Stock, Watchlist, WatchlistStock
from datetime import datetime

def get_user():
    """Get the demo user (for now we use a simple demo user)"""
    user = session.query(User).first()
    if not user:
        # Create a demo user if none exists
        user = User(
            username="demo_user",
            email="demo@example.com",
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        session.add(user)
        session.commit()
    return user

def get_user_watchlists(user_id):
    """Get all watchlists for a user"""
    watchlists = session.query(Watchlist).filter_by(user_id=user_id).all()
    return watchlists

def get_watchlist_stocks(watchlist_id):
    """Get all stocks in a watchlist"""
    stocks = session.query(Stock).join(
        WatchlistStock,
        WatchlistStock.stock_id == Stock.id
    ).filter(
        WatchlistStock.watchlist_id == watchlist_id
    ).all()
    return stocks

def create_new_watchlist(user_id, name, description=None):
    """Create a new watchlist"""
    watchlist = Watchlist(
        user_id=user_id,
        name=name,
        description=description,
        created_at=datetime.utcnow()
    )
    session.add(watchlist)
    session.commit()
    return watchlist

def add_to_watchlist(watchlist_id, symbol):
    """Add a stock to a watchlist"""
    # Find or create the stock
    stock = session.query(Stock).filter_by(symbol=symbol.upper()).first()
    if not stock:
        # Import here to avoid circular import
        import db_utils
        stock = db_utils.add_stock(symbol.upper())
    
    if not stock:
        return False
    
    # Check if stock is already in watchlist
    existing = session.query(WatchlistStock).filter_by(
        watchlist_id=watchlist_id,
        stock_id=stock.id
    ).first()
    
    if existing:
        return True
    
    # Add stock to watchlist
    watchlist_stock = WatchlistStock(
        watchlist_id=watchlist_id,
        stock_id=stock.id,
        added_at=datetime.utcnow()
    )
    
    session.add(watchlist_stock)
    session.commit()
    return True

def remove_from_watchlist(watchlist_id, stock_id):
    """Remove a stock from a watchlist"""
    watchlist_stock = session.query(WatchlistStock).filter_by(
        watchlist_id=watchlist_id,
        stock_id=stock_id
    ).first()
    
    if watchlist_stock:
        session.delete(watchlist_stock)
        session.commit()
        return True
    return False

def delete_watchlist(watchlist_id):
    """Delete a watchlist and all its stocks"""
    # First remove all stocks from watchlist
    session.query(WatchlistStock).filter_by(watchlist_id=watchlist_id).delete()
    
    # Then delete the watchlist
    watchlist = session.query(Watchlist).filter_by(id=watchlist_id).first()
    if watchlist:
        session.delete(watchlist)
        session.commit()
        return True
    return False

def render_watchlist_ui():
    """Render the watchlist UI"""
    st.header("Stock Watchlists")
    
    # Get current user
    user = get_user()
    
    # Create columns for watchlist management
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Add New Watchlist")
        
        watchlist_name = st.text_input("Watchlist Name", key="new_watchlist_name")
        watchlist_desc = st.text_area("Description (optional)", key="new_watchlist_desc", height=100)
        
        if st.button("Create Watchlist"):
            if watchlist_name:
                create_new_watchlist(user.id, watchlist_name, watchlist_desc)
                st.success(f"Watchlist '{watchlist_name}' created!")
                st.rerun()
            else:
                st.error("Please enter a watchlist name")
    
    with col1:
        # Get user's watchlists
        watchlists = get_user_watchlists(user.id)
        
        if not watchlists:
            st.info("You don't have any watchlists yet. Create one to get started!")
        else:
            # Create tabs for each watchlist using a list of strings
            watchlist_names = []
            for wl in watchlists:
                # Extract the name as a regular Python string 
                watchlist_names.append(str(wl.name) if wl.name else f"Watchlist {wl.id}")
            watchlist_tabs = st.tabs(watchlist_names)
            
            for i, wl in enumerate(watchlists):
                with watchlist_tabs[i]:
                    # Watchlist description
                    if wl.description:
                        st.write(wl.description)
                    
                    # Add stock to watchlist
                    new_stock = st.text_input(
                        "Add Stock Symbol", 
                        key=f"add_stock_{wl.id}",
                        placeholder="Enter stock symbol (e.g., AAPL)"
                    )
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button("Add to Watchlist", key=f"add_btn_{wl.id}"):
                            if new_stock:
                                if add_to_watchlist(wl.id, new_stock):
                                    st.success(f"Added {new_stock.upper()} to watchlist!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to add {new_stock.upper()} to watchlist")
                            else:
                                st.error("Please enter a stock symbol")
                    
                    with col2:
                        if st.button("Delete Watchlist", key=f"del_watchlist_{wl.id}"):
                            if delete_watchlist(wl.id):
                                st.success(f"Deleted watchlist '{wl.name}'")
                                st.rerun()
                            else:
                                st.error("Failed to delete watchlist")
                    
                    # Display stocks in watchlist
                    stocks = get_watchlist_stocks(wl.id)
                    
                    if not stocks:
                        st.info("This watchlist is empty. Add some stocks to get started!")
                    else:
                        # Create a table of stocks
                        stock_data = []
                        for stock in stocks:
                            # Add button for viewing stock
                            view_btn = st.button("View", key=f"view_{wl.id}_{stock.id}")
                            
                            # Add button for removing stock
                            remove_btn = st.button("Remove", key=f"remove_{wl.id}_{stock.id}")
                            
                            if remove_btn:
                                if remove_from_watchlist(wl.id, stock.id):
                                    st.success(f"Removed {stock.symbol} from watchlist")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to remove {stock.symbol} from watchlist")
                            
                            if view_btn:
                                # Store the selected stock symbol in session state for the main app to use
                                st.session_state["selected_stock"] = stock.symbol
                                st.rerun()
                            
                            added_at = session.query(WatchlistStock).filter_by(
                                watchlist_id=wl.id, 
                                stock_id=stock.id
                            ).first().added_at
                            
                            stock_data.append({
                                "Symbol": stock.symbol,
                                "Company": stock.company_name,
                                "Sector": stock.sector if stock.sector else "N/A",
                                "Added": added_at.strftime("%Y-%m-%d") if added_at else "N/A"
                            })
                        
                        # Display stock data as a table
                        import pandas as pd
                        df = pd.DataFrame(stock_data)
                        st.dataframe(df, use_container_width=True)