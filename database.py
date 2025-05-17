import os
import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Get database URL from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")

# Create engine with a fallback if DATABASE_URL is not set
if DATABASE_URL is None:
    print("Warning: DATABASE_URL environment variable not set. Using SQLite in-memory database.")
    engine = create_engine("sqlite:///:memory:")
else:
    engine = create_engine(DATABASE_URL)

# Create base class for models
Base = declarative_base()

# Define models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    stock_notes = relationship("StockNote", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"

class Stock(Base):
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, nullable=False)
    company_name = Column(String)
    sector = Column(String)
    industry = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    price_history = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    watchlists = relationship("WatchlistStock", back_populates="stock")
    notes = relationship("StockNote", back_populates="stock")
    
    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', company_name='{self.company_name}')>"

class StockPrice(Base):
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    date = Column(DateTime, nullable=False)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    
    # Relationships
    stock = relationship("Stock", back_populates="price_history")
    
    def __repr__(self):
        return f"<StockPrice(stock='{self.stock.symbol}', date='{self.date}', close='{self.close_price}')>"

class Watchlist(Base):
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="watchlists")
    stocks = relationship("WatchlistStock", back_populates="watchlist", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Watchlist(name='{self.name}', user='{self.user.username}')>"

class WatchlistStock(Base):
    __tablename__ = "watchlist_stocks"
    
    id = Column(Integer, primary_key=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"))
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="stocks")
    stock = relationship("Stock", back_populates="watchlists")
    
    def __repr__(self):
        return f"<WatchlistStock(watchlist='{self.watchlist.name}', stock='{self.stock.symbol}')>"

class StockNote(Base):
    __tablename__ = "stock_notes"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="stock_notes")
    stock = relationship("Stock", back_populates="notes")
    
    def __repr__(self):
        return f"<StockNote(stock='{self.stock.symbol}', user='{self.user.username}')>"

# Create database session
Session = sessionmaker(bind=engine)
session = Session()

# Function to create tables
def create_tables():
    Base.metadata.create_all(engine)

# Function to drop tables
def drop_tables():
    Base.metadata.drop_all(engine)