import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

# File to store watchlist data
WATCHLIST_FILE = "watchlists.json"

def load_watchlists():
    """Load watchlists from file"""
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, 'r') as f:
                return json.load(f)
        except:
            return {'watchlists': []}
    else:
        return {'watchlists': []}
    
def save_watchlists(data):
    """Save watchlists to file"""
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(data, f)

def get_watchlists():
    """Get all watchlists"""
    return load_watchlists()['watchlists']

def create_watchlist(name, description=""):
    """Create a new watchlist"""
    data = load_watchlists()
    
    # Check if watchlist with same name exists
    for watchlist in data['watchlists']:
        if watchlist['name'] == name:
            return False
    
    # Create new watchlist
    watchlist_id = len(data['watchlists']) + 1
    new_watchlist = {
        'id': watchlist_id,
        'name': name,
        'description': description,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'stocks': []
    }
    
    data['watchlists'].append(new_watchlist)
    save_watchlists(data)
    return True

def add_to_watchlist(watchlist_id, symbol, company_name=""):
    """Add a stock to a watchlist"""
    data = load_watchlists()
    
    # Find watchlist
    for watchlist in data['watchlists']:
        if watchlist['id'] == watchlist_id:
            # Check if stock already in watchlist
            for stock in watchlist['stocks']:
                if stock['symbol'] == symbol:
                    return True
            
            # Add stock
            watchlist['stocks'].append({
                'symbol': symbol,
                'company_name': company_name,
                'added_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            save_watchlists(data)
            return True
    
    return False

def remove_from_watchlist(watchlist_id, symbol):
    """Remove a stock from a watchlist"""
    data = load_watchlists()
    
    # Find watchlist
    for watchlist in data['watchlists']:
        if watchlist['id'] == watchlist_id:
            # Remove stock
            watchlist['stocks'] = [s for s in watchlist['stocks'] if s['symbol'] != symbol]
            save_watchlists(data)
            return True
    
    return False

def delete_watchlist(watchlist_id):
    """Delete a watchlist"""
    data = load_watchlists()
    
    # Remove watchlist
    data['watchlists'] = [w for w in data['watchlists'] if w['id'] != watchlist_id]
    save_watchlists(data)
    return True

def render_watchlist_section(current_stock):
    """Render the watchlist section of the dashboard"""
    st.header("Stock Watchlists")
    
    # Create columns for watchlist management
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Add New Watchlist")
        
        watchlist_name = st.text_input("Watchlist Name", key="new_watchlist_name")
        watchlist_desc = st.text_area("Description (optional)", key="new_watchlist_desc", height=100)
        
        if st.button("Create Watchlist"):
            if watchlist_name:
                if create_watchlist(watchlist_name, watchlist_desc):
                    st.success(f"Watchlist '{watchlist_name}' created!")
                    st.rerun()
                else:
                    st.error(f"Watchlist '{watchlist_name}' already exists")
            else:
                st.error("Please enter a watchlist name")
    
    with col1:
        # Save current stock to watchlist section
        st.subheader(f"Save {current_stock} to Watchlist")
        
        watchlists = get_watchlists()
        
        if not watchlists:
            st.info("You don't have any watchlists yet. Create one to get started!")
        else:
            watchlist_options = [w['name'] for w in watchlists]
            selected_watchlist = st.selectbox(
                "Select a watchlist",
                options=watchlist_options,
                key="add_to_watchlist_select"
            )
            
            # Find the selected watchlist ID
            selected_id = None
            for w in watchlists:
                if w['name'] == selected_watchlist:
                    selected_id = w['id']
                    break
            
            if st.button(f"Add {current_stock} to {selected_watchlist}"):
                if add_to_watchlist(selected_id, current_stock):
                    st.success(f"Added {current_stock} to {selected_watchlist}")
                    st.rerun()
                else:
                    st.error(f"Failed to add {current_stock} to watchlist")
    
    # Display all watchlists
    st.subheader("My Watchlists")
    
    watchlists = get_watchlists()
    
    if not watchlists:
        st.info("You don't have any watchlists yet. Create one to get started!")
    else:
        # Create tabs for each watchlist
        tab_names = [w['name'] for w in watchlists]
        tabs = st.tabs(tab_names)
        
        for i, watchlist in enumerate(watchlists):
            with tabs[i]:
                # Display watchlist description
                if watchlist['description']:
                    st.write(watchlist['description'])
                
                # Delete watchlist button
                if st.button("Delete Watchlist", key=f"delete_watchlist_{watchlist['id']}"):
                    if delete_watchlist(watchlist['id']):
                        st.success(f"Deleted watchlist '{watchlist['name']}'")
                        st.rerun()
                    else:
                        st.error("Failed to delete watchlist")
                
                # Display stocks
                if not watchlist['stocks']:
                    st.info("This watchlist is empty. Add some stocks to get started!")
                else:
                    # Create data for table
                    data = []
                    for stock in watchlist['stocks']:
                        data.append({
                            'Symbol': stock['symbol'],
                            'Company': stock.get('company_name', ''),
                            'Added': stock.get('added_at', 'N/A')
                        })
                    
                    # Display as dataframe
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Add option to select a stock to view
                    stock_symbols = [s['symbol'] for s in watchlist['stocks']]
                    
                    selected_stock = st.selectbox(
                        "Select a stock to view",
                        options=stock_symbols,
                        key=f"select_stock_{watchlist['id']}"
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("View Stock", key=f"view_stock_{watchlist['id']}"):
                            st.session_state['selected_stock'] = selected_stock
                            st.rerun()
                    
                    with col2:
                        if st.button("Remove Stock", key=f"remove_stock_{watchlist['id']}"):
                            if remove_from_watchlist(watchlist['id'], selected_stock):
                                st.success(f"Removed {selected_stock} from watchlist")
                                st.rerun()
                            else:
                                st.error(f"Failed to remove {selected_stock} from watchlist")

# Initialize with a default watchlist if none exists
if __name__ == "__main__":
    if not os.path.exists(WATCHLIST_FILE):
        create_watchlist("Default Watchlist", "My default watchlist")
        add_to_watchlist(1, "AAPL", "Apple Inc.")
        add_to_watchlist(1, "MSFT", "Microsoft Corporation") 
        add_to_watchlist(1, "GOOGL", "Alphabet Inc.")
        print("Created default watchlist with sample stocks")