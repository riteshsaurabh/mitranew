"""
Emoji-based Mood Tracker for Financial Sentiment
This module provides functions to analyze and display financial sentiment using emojis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Define emoji mappings for different sentiment levels
SENTIMENT_EMOJIS = {
    "very_bullish": "🚀",  # Rocket - Strong upward momentum
    "bullish": "😁",       # Grinning face - Positive outlook
    "neutral": "😐",       # Neutral face - Stable/sideways market
    "bearish": "😟",       # Worried face - Negative outlook
    "very_bearish": "🧸",  # Teddy bear - Bear market reference
    "volatile": "🎢",      # Roller coaster - High volatility
    "recovery": "🌱",      # Seedling - Market recovery
    "uncertain": "🤔",     # Thinking face - Market uncertainty
    "fear": "😱",          # Fearful face - Market panic
    "greed": "🤑"          # Money face - Market greed
}

# Colors for different sentiment states
SENTIMENT_COLORS = {
    "very_bullish": "#00C853",  # Green
    "bullish": "#8BC34A",       # Light green
    "neutral": "#9E9E9E",       # Gray
    "bearish": "#FF9800",       # Orange
    "very_bearish": "#F44336",  # Red
    "volatile": "#9C27B0",      # Purple
    "recovery": "#4CAF50",      # Medium green
    "uncertain": "#607D8B",     # Blue gray
    "fear": "#D32F2F",          # Dark red
    "greed": "#FFD700"          # Gold
}

def analyze_price_sentiment(data):
    """
    Analyze price sentiment based on recent price movements
    
    Args:
        data (pd.DataFrame): Historical price data
        
    Returns:
        dict: Sentiment analysis results
    """
    if data.empty or len(data) < 5:
        return {
            "sentiment": "uncertain",
            "emoji": SENTIMENT_EMOJIS["uncertain"],
            "color": SENTIMENT_COLORS["uncertain"],
            "description": "Not enough data to determine sentiment"
        }
    
    # Calculate key metrics
    try:
        # Short term momentum (1-day, 5-day change)
        last_close = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2]
        five_day_ago = data['Close'].iloc[-6] if len(data) >= 6 else data['Close'].iloc[0]
        
        one_day_change_pct = ((last_close - prev_close) / prev_close) * 100
        five_day_change_pct = ((last_close - five_day_ago) / five_day_ago) * 100
        
        # Volatility (20-day)
        volatility = data['Close'].pct_change().rolling(window=20).std().iloc[-1] * 100
        
        # 50-day vs 200-day MA (if enough data)
        has_long_term_data = len(data) >= 200
        has_medium_term_data = len(data) >= 50
        
        # Initialize medium/long term signals
        ma_signal = "neutral"
        
        if has_long_term_data and has_medium_term_data:
            ma_50 = data['Close'].rolling(window=50).mean().iloc[-1]
            ma_200 = data['Close'].rolling(window=200).mean().iloc[-1]
            ma_signal = "bullish" if ma_50 > ma_200 else "bearish"
        
        # Determine overall sentiment
        sentiment = "neutral"
        description = "Market appears stable"
        
        # Very bullish: Strong positive momentum across timeframes
        if one_day_change_pct > 2 and five_day_change_pct > 5 and ma_signal == "bullish":
            sentiment = "very_bullish"
            description = "Strong bullish momentum across timeframes"
        
        # Bullish: Generally positive signals
        elif (one_day_change_pct > 0.5 or five_day_change_pct > 2) and ma_signal != "bearish":
            sentiment = "bullish"
            description = "Positive momentum indicating bullish trend"
        
        # Very bearish: Strong negative momentum across timeframes
        elif one_day_change_pct < -2 and five_day_change_pct < -5 and ma_signal == "bearish":
            sentiment = "very_bearish"
            description = "Strong bearish momentum across timeframes"
        
        # Bearish: Generally negative signals
        elif (one_day_change_pct < -0.5 or five_day_change_pct < -2) and ma_signal != "bullish":
            sentiment = "bearish"
            description = "Negative momentum indicating bearish trend"
        
        # High volatility
        if volatility > 3:
            if abs(one_day_change_pct) > 3:
                sentiment = "volatile"
                description = "High volatility with significant price swings"
        
        # Recovery pattern: Recent uptick after downtrend
        if five_day_change_pct > 3 and one_day_change_pct > 0 and ma_signal == "bearish":
            sentiment = "recovery"
            description = "Potential recovery forming after downtrend"
            
        # Check for fear/greed based on volatility and magnitude of moves
        if one_day_change_pct < -3.5 and volatility > 2.5:
            sentiment = "fear"
            description = "Market showing signs of fear and panic selling"
        elif one_day_change_pct > 3.5 and volatility > 2:
            sentiment = "greed"
            description = "Market showing signs of excessive optimism/greed"
            
        return {
            "sentiment": sentiment,
            "emoji": SENTIMENT_EMOJIS[sentiment],
            "color": SENTIMENT_COLORS[sentiment],
            "description": description,
            "metrics": {
                "1_day_change": f"{one_day_change_pct:.2f}%",
                "5_day_change": f"{five_day_change_pct:.2f}%",
                "volatility": f"{volatility:.2f}%",
                "last_close": last_close
            }
        }
    
    except Exception as e:
        return {
            "sentiment": "uncertain",
            "emoji": SENTIMENT_EMOJIS["uncertain"],
            "color": SENTIMENT_COLORS["uncertain"],
            "description": f"Error analyzing sentiment: {str(e)}"
        }

def analyze_volume_sentiment(data):
    """
    Analyze volume sentiment based on recent trading activity
    
    Args:
        data (pd.DataFrame): Historical price and volume data
        
    Returns:
        dict: Volume sentiment analysis
    """
    if data.empty or len(data) < 5 or 'Volume' not in data.columns:
        return {
            "sentiment": "uncertain",
            "emoji": "📊",
            "description": "Not enough volume data"
        }
    
    try:
        # Calculate volume metrics
        avg_volume_20d = data['Volume'].rolling(window=20).mean().iloc[-1]
        recent_volume = data['Volume'].iloc[-1]
        volume_ratio = recent_volume / avg_volume_20d
        
        sentiment = "neutral"
        emoji = "📊"
        description = "Average trading volume"
        
        if volume_ratio > 2.0:
            sentiment = "high_interest"
            emoji = "📈"
            description = "Unusually high trading volume"
        elif volume_ratio > 1.5:
            sentiment = "increased_interest"
            emoji = "👀"
            description = "Above average trading volume"
        elif volume_ratio < 0.5:
            sentiment = "low_interest"
            emoji = "💤"
            description = "Below average trading activity"
            
        return {
            "sentiment": sentiment,
            "emoji": emoji,
            "description": description,
            "metrics": {
                "volume": f"{int(recent_volume):,}",
                "avg_volume": f"{int(avg_volume_20d):,}",
                "volume_ratio": f"{volume_ratio:.2f}x"
            }
        }
    
    except Exception as e:
        return {
            "sentiment": "uncertain",
            "emoji": "📊",
            "description": f"Error analyzing volume: {str(e)}"
        }

def analyze_news_sentiment(stock_symbol, news_data=None):
    """
    Analyze sentiment from financial news
    
    Args:
        stock_symbol (str): Stock symbol to check news for
        news_data (list): List of news articles with sentiment (optional)
        
    Returns:
        dict: News sentiment analysis
    """
    if news_data is None or len(news_data) == 0:
        return {
            "sentiment": "neutral",
            "emoji": "📰",
            "description": "No recent news found"
        }
    
    try:
        # Calculate average sentiment from news articles that have sentiment scores
        sentiment_news = [article for article in news_data 
                         if 'sentiment_score' in article and article['sentiment_score'] is not None]
        
        if not sentiment_news:
            return {
                "sentiment": "neutral",
                "emoji": "📰",
                "description": "No sentiment data in news"
            }
        
        avg_sentiment = sum(article['sentiment_score'] for article in sentiment_news) / len(sentiment_news)
        
        sentiment = "neutral"
        emoji = "📰"
        description = "Neutral news sentiment"
        
        if avg_sentiment > 0.3:
            sentiment = "positive"
            emoji = "📰😁"
            description = "Positive news sentiment"
        elif avg_sentiment > 0.1:
            sentiment = "slightly_positive"
            emoji = "📰🙂"
            description = "Slightly positive news sentiment"
        elif avg_sentiment < -0.3:
            sentiment = "negative"
            emoji = "📰😟"
            description = "Negative news sentiment"
        elif avg_sentiment < -0.1:
            sentiment = "slightly_negative"
            emoji = "📰🙁"
            description = "Slightly negative news sentiment"
            
        return {
            "sentiment": sentiment,
            "emoji": emoji,
            "description": description,
            "avg_sentiment": avg_sentiment
        }
    
    except Exception as e:
        return {
            "sentiment": "neutral",
            "emoji": "📰",
            "description": f"Error analyzing news sentiment: {str(e)}"
        }

def get_sentiment_emoji(percent_change):
    """
    Get sentiment emoji based on percentage change
    
    Args:
        percent_change (float): Price change percentage
        
    Returns:
        str: Emoji representing the sentiment
    """
    if percent_change > 3:
        return "🚀"  # Very bullish
    elif percent_change > 1:
        return "😁"  # Bullish
    elif percent_change > 0:
        return "🙂"  # Slightly bullish
    elif percent_change == 0:
        return "😐"  # Neutral
    elif percent_change > -1:
        return "🙁"  # Slightly bearish
    elif percent_change > -3:
        return "😟"  # Bearish
    else:
        return "🧸"  # Very bearish (bear market)

def get_market_mood_index(price_sentiment, volume_sentiment, news_sentiment=None):
    """
    Calculate an overall market mood index based on multiple sentiment indicators
    
    Args:
        price_sentiment (dict): Price sentiment analysis
        volume_sentiment (dict): Volume sentiment analysis
        news_sentiment (dict): News sentiment analysis (optional)
        
    Returns:
        float: Market mood index from -100 (extremely bearish) to +100 (extremely bullish)
    """
    # Sentiment value mapping to numeric scores
    price_scores = {
        "very_bullish": 100,
        "bullish": 60,
        "recovery": 40,
        "neutral": 0,
        "uncertain": 0,
        "volatile": -20,
        "bearish": -60,
        "very_bearish": -100,
        "fear": -80,
        "greed": 80
    }
    
    # Volume contribution based on sentiment
    volume_impact = {
        "high_interest": 1.2,  # Amplifies existing sentiment
        "increased_interest": 1.1,
        "neutral": 1.0,
        "low_interest": 0.8,  # Dampens existing sentiment
        "uncertain": 1.0
    }
    
    # News sentiment mapping to numeric scores
    news_scores = {
        "positive": 30,
        "slightly_positive": 15,
        "neutral": 0,
        "slightly_negative": -15,
        "negative": -30
    }
    
    # Calculate base mood score from price sentiment
    base_score = price_scores.get(price_sentiment["sentiment"], 0)
    
    # Apply volume sentiment as a multiplier to base score
    volume_multiplier = volume_impact.get(volume_sentiment["sentiment"], 1.0)
    weighted_price_score = base_score * volume_multiplier
    
    # Include news sentiment if available
    if news_sentiment and news_sentiment["sentiment"] in news_scores:
        news_score = news_scores[news_sentiment["sentiment"]]
        # News has 30% weight in the final score
        final_score = (weighted_price_score * 0.7) + (news_score * 0.3)
    else:
        final_score = weighted_price_score
    
    # Ensure score is within -100 to 100 range
    return max(min(final_score, 100), -100)

def display_sentiment_dashboard(stock_symbol, price_data, news_data=None):
    """
    Display a comprehensive sentiment dashboard with emojis
    
    Args:
        stock_symbol (str): Stock symbol
        price_data (pd.DataFrame): Historical price data
        news_data (list): List of news articles (optional)
    """
    # Make sure we have data
    if price_data.empty:
        st.error("Cannot analyze sentiment: No price data available")
        return
    
    # Get sentiment analyses
    price_sentiment = analyze_price_sentiment(price_data)
    volume_sentiment = analyze_volume_sentiment(price_data)
    news_sentiment = analyze_news_sentiment(stock_symbol, news_data)
    
    # Calculate market mood index
    mood_index = get_market_mood_index(price_sentiment, volume_sentiment, news_sentiment)
    
    # Create gauge color based on mood index
    if mood_index > 70:
        gauge_color = "#00C853"  # Very bullish - green
    elif mood_index > 30:
        gauge_color = "#8BC34A"  # Bullish - light green
    elif mood_index > -30:
        gauge_color = "#9E9E9E"  # Neutral - gray
    elif mood_index > -70:
        gauge_color = "#FF9800"  # Bearish - orange
    else:
        gauge_color = "#F44336"  # Very bearish - red
    
    # Create emoji based mood meter
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(25, 57, 138, 0.05), rgba(78, 205, 196, 0.08));
              border-radius: 15px; 
              padding: 20px; 
              margin-bottom: 20px;
              border: 1px solid rgba(78, 205, 196, 0.15);">
        <h3 style="margin-top:0; color:#19398A; font-weight:600; margin-bottom:15px; 
                  display: flex; align-items: center;">
            <span style="font-size: 1.5rem; margin-right: 10px;">🧠</span> 
            Emoji Mood Tracker
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Create columns for sentiment cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Format metrics for display
        one_day_change = price_sentiment.get('metrics', {}).get('1_day_change', 'N/A')
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {price_sentiment['color']}15, {price_sentiment['color']}05); 
                  padding: 15px; 
                  border-radius: 10px; 
                  border-left: 4px solid {price_sentiment['color']};
                  margin-bottom: 15px;">
            <p style="color: #71717a; font-size: 0.8rem; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.05em;">
                Price Sentiment
            </p>
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 2.5rem; margin-right: 15px;">{price_sentiment['emoji']}</span>
                <div>
                    <h3 style="color: #19398A; margin: 0; font-size: 1.2rem; font-weight: 600;">
                        {price_sentiment['sentiment'].replace('_', ' ').title()}
                    </h3>
                    <p style="margin: 0; color: #71717a; font-size: 0.8rem;">
                        {one_day_change} (1 day)
                    </p>
                </div>
            </div>
            <p style="margin: 0; color: #71717a; font-size: 0.8rem;">
                {price_sentiment['description']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Format metrics for display
        volume_ratio = volume_sentiment.get('metrics', {}).get('volume_ratio', 'N/A')
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(25, 57, 138, 0.05), rgba(78, 205, 196, 0.08)); 
                  padding: 15px; 
                  border-radius: 10px; 
                  border-left: 4px solid #4ECDC4;
                  margin-bottom: 15px;">
            <p style="color: #71717a; font-size: 0.8rem; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.05em;">
                Volume Analysis
            </p>
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 2.5rem; margin-right: 15px;">{volume_sentiment['emoji']}</span>
                <div>
                    <h3 style="color: #19398A; margin: 0; font-size: 1.2rem; font-weight: 600;">
                        {volume_sentiment['sentiment'].replace('_', ' ').title()}
                    </h3>
                    <p style="margin: 0; color: #71717a; font-size: 0.8rem;">
                        {volume_ratio} vs avg
                    </p>
                </div>
            </div>
            <p style="margin: 0; color: #71717a; font-size: 0.8rem;">
                {volume_sentiment['description']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(255, 107, 26, 0.05), rgba(255, 107, 26, 0.02)); 
                  padding: 15px; 
                  border-radius: 10px; 
                  border-left: 4px solid #FF6B1A;
                  margin-bottom: 15px;">
            <p style="color: #71717a; font-size: 0.8rem; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.05em;">
                News Sentiment
            </p>
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 2.5rem; margin-right: 15px;">{news_sentiment['emoji']}</span>
                <div>
                    <h3 style="color: #19398A; margin: 0; font-size: 1.2rem; font-weight: 600;">
                        {news_sentiment['sentiment'].replace('_', ' ').title()}
                    </h3>
                    <p style="margin: 0; color: #71717a; font-size: 0.8rem;">
                        Based on recent news
                    </p>
                </div>
            </div>
            <p style="margin: 0; color: #71717a; font-size: 0.8rem;">
                {news_sentiment['description']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Create mood meter gauge
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = mood_index,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Market Mood Index", 'font': {'size': 16, 'color': '#19398A'}},
        gauge = {
            'axis': {'range': [-100, 100], 'tickwidth': 1, 'tickcolor': "#19398A"},
            'bar': {'color': gauge_color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [-100, -70], 'color': '#F44336'},  # Very bearish - red
                {'range': [-70, -30], 'color': '#FF9800'},   # Bearish - orange
                {'range': [-30, 30], 'color': '#9E9E9E'},    # Neutral - gray
                {'range': [30, 70], 'color': '#8BC34A'},     # Bullish - light green
                {'range': [70, 100], 'color': '#00C853'}     # Very bullish - green
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': mood_index
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#19398A", "family": "Arial"}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mood interpretation
    mood_description = "Market sentiment appears neutral"
    if mood_index > 70:
        mood_description = "Extremely bullish mood - strong positive sentiment"
    elif mood_index > 30:
        mood_description = "Bullish mood - generally positive outlook"
    elif mood_index > 10:
        mood_description = "Slightly bullish - cautiously optimistic"
    elif mood_index > -10:
        mood_description = "Neutral market sentiment - no clear direction"
    elif mood_index > -30:
        mood_description = "Slightly bearish - mild caution advised"
    elif mood_index > -70:
        mood_description = "Bearish mood - negative sentiment prevails"
    else:
        mood_description = "Extremely bearish - strong negative sentiment"
        
    st.markdown(f"""
    <div style="background: white; padding: 15px; border-radius: 10px; margin-top: 5px; margin-bottom: 20px; 
              border: 1px solid {gauge_color}; text-align: center;">
        <p style="margin: 0; color: #19398A; font-weight: 500;">
            {mood_description}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Detailed metrics 
    with st.expander("View Detailed Sentiment Metrics"):
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        
        with metrics_col1:
            st.subheader("Price Metrics")
            # Convert dictionary to DataFrame safely
            if 'metrics' in price_sentiment and isinstance(price_sentiment['metrics'], dict):
                metrics_dict = price_sentiment['metrics']
                metrics_df = pd.DataFrame({
                    "Metric": list(metrics_dict.keys()),
                    "Value": list(metrics_dict.values())
                })
                st.dataframe(metrics_df, hide_index=True)
            else:
                st.write("No detailed metrics available")
            
        with metrics_col2:
            st.subheader("Volume Metrics")
            # Convert dictionary to DataFrame safely
            if 'metrics' in volume_sentiment and isinstance(volume_sentiment['metrics'], dict):
                vol_metrics_dict = volume_sentiment['metrics']
                vol_metrics_df = pd.DataFrame({
                    "Metric": list(vol_metrics_dict.keys()),
                    "Value": list(vol_metrics_dict.values())
                })
                st.dataframe(vol_metrics_df, hide_index=True)
            else:
                st.write("No detailed metrics available")
            
        with metrics_col3:
            st.subheader("Sentiment Factors")
            
            # Get sentiment values with fallbacks
            price_sent = price_sentiment.get('sentiment', 'neutral')
            volume_sent = volume_sentiment.get('sentiment', 'neutral')
            news_sent = news_sentiment.get('sentiment', 'neutral')
            
            # Create dataframe with sentiment information
            factors_df = pd.DataFrame({
                "Factor": ["Price Sentiment", "Volume Impact", "News Sentiment", "Overall Mood"],
                "Value": [
                    price_sent.replace('_', ' ').title(),
                    volume_sent.replace('_', ' ').title(),
                    news_sent.replace('_', ' ').title(),
                    f"{mood_index:.1f} / 100"
                ]
            })
            st.dataframe(factors_df, hide_index=True)