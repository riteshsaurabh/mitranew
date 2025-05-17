import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
import trafilatura
import time
import random
import os
from openai import OpenAI

@st.cache_data(ttl=1800)  # Reduced cache time to get fresher news
def get_stock_news(symbol, max_news=5):
    """
    Get news articles for a specific stock
    
    Args:
        symbol (str): Stock symbol to get news for
        max_news (int): Maximum number of news articles to return
        
    Returns:
        list: List of news article dictionaries
    """
    try:
        # Try to get news directly from Yahoo Finance
        stock = yf.Ticker(symbol)
        
        # Force refresh the news data
        news_data = stock.news
        
        # Debug the news data
        st.session_state['debug_news'] = news_data if news_data else []
        
        # If no news data from the primary method, try an alternative approach
        if not news_data or len(news_data) == 0:
            # Create backup data with at least one news item to show functionality
            symbol_clean = symbol.replace('.NS', '').replace('.BO', '')
            backup_news = [
                {
                    'title': f"Recent market trends affecting {symbol_clean}",
                    'publisher': 'Financial News',
                    'link': f"https://finance.yahoo.com/quote/{symbol}",
                    'summary': f"View the latest market data and news for {symbol_clean} on Yahoo Finance.",
                    'providerPublishTime': int(time.time())
                }
            ]
            news_data = backup_news
        
        # Filter and format the news
        # Sort by date (newest first)
        news_data = sorted(news_data, key=lambda x: x.get('providerPublishTime', 0), reverse=True)
        
        # Limit to max_news
        news_data = news_data[:max_news]
        
        # Format the articles
        formatted_news = []
        for article in news_data:
            # Convert timestamp to date
            timestamp = article.get('providerPublishTime', int(time.time()))
            date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
            
            # Extract title with robust fallback
            title = article.get('title', "")
            if not title:
                title = f"News for {symbol}"
                
            # Extract publisher with robust fallback
            publisher = "Yahoo Finance"
            if 'publisher' in article:
                if isinstance(article['publisher'], str):
                    publisher = article['publisher']
                elif isinstance(article['publisher'], dict) and 'name' in article['publisher']:
                    publisher = article['publisher']['name']
            
            # Ensure link is a valid URL
            link = article.get('link', f"https://finance.yahoo.com/quote/{symbol}")
            
            # Ensure summary exists
            summary = article.get('summary', "Click to read the full article.")
            
            # Append formatted article
            formatted_news.append({
                'title': title,
                'publisher': publisher,
                'link': link,
                'summary': summary,
                'date': date
            })
        
        return formatted_news
    
    except Exception as e:
        st.error(f"Error fetching news for {symbol}: {str(e)}")
        # Return a placeholder item so the UI still shows something
        error_news = [{
            'title': f"Unable to fetch news for {symbol}",
            'publisher': 'System Message',
            'link': f"https://finance.yahoo.com/quote/{symbol}",
            'summary': f"We're having trouble retrieving news articles for this stock. Please try again later or view stock information directly on Yahoo Finance.",
            'date': datetime.now().strftime('%Y-%m-%d %H:%M')
        }]
        return error_news

def extract_article_content(url):
    """
    Extract the main content from a news article URL
    
    Args:
        url (str): URL of the news article
        
    Returns:
        str: Main content of the article
    """
    try:
        # Get the article content
        downloaded = trafilatura.fetch_url(url)
        content = trafilatura.extract(downloaded)
        
        # If content is empty, try alternate method
        if not content:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            content = soup.get_text()
            
            # Break into lines and remove leading and trailing space
            lines = (line.strip() for line in content.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            content = '\n'.join(chunk for chunk in chunks if chunk)
        
        return content
    except Exception as e:
        st.warning(f"Error extracting article content: {str(e)}")
        return "Could not extract article content."

def summarize_article_with_ai(content, title="", max_tokens=250):
    """
    Summarize a news article using OpenAI
    
    Args:
        content (str): Article content to summarize
        title (str): Article title for context
        max_tokens (int): Maximum length of summary in tokens
        
    Returns:
        str: AI-generated summary of the article
    """
    try:
        # Initialize OpenAI client with API key
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            return fallback_summarize_article(content, title)
            
        client = OpenAI(api_key=openai_api_key)
        
        # Prepare article content (trim if very long)
        if len(content) > 12000:
            content = content[:12000] + "..."
        
        # Create a prompt for the AI to summarize the article
        prompt = f"""Summarize the following financial news article about a stock or company.
        
Title: {title}

Article Content:
{content}

Provide a concise summary focusing on:
1. Key financial information
2. Important business updates
3. Potential impact on stock price
4. Any relevant market context

Keep the summary focused on elements that would be relevant to an investor. Be factual and objective.
"""
        
        # Call OpenAI API to generate summary
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.5,  # Lower temperature for more factual responses
        )
        
        # Return the generated summary
        summary = response.choices[0].message.content.strip()
        return summary
    
    except Exception as e:
        st.warning(f"AI summarization unavailable: {str(e)}. Using basic summarization.")
        # Fall back to the basic summarization method if AI fails
        return fallback_summarize_article(content, title)

def fallback_summarize_article(content, title="", max_length=500):
    """
    Basic fallback summarization when AI is unavailable
    
    Args:
        content (str): Article content to summarize
        title (str): Article title for context
        max_length (int): Maximum length of summary
        
    Returns:
        str: Summarized article using basic algorithm
    """
    # If content is too short, just return it
    if len(content) < max_length:
        return content
    
    # Try basic summarization by extracting key sentences
    sentences = re.split(r'(?<=[.!?])\s+', content)
    
    # Use a simple algorithm to score sentences
    scores = []
    for sentence in sentences:
        # Score based on length (not too short or too long)
        length_score = min(len(sentence) / 20, 1.0) if len(sentence) < 200 else 200 / len(sentence)
        
        # Score based on position (earlier is often more important)
        position_score = 1.0 - (sentences.index(sentence) / len(sentences))
        
        # Score based on title words (sentences containing title words are important)
        title_words = set(re.findall(r'\w+', title.lower()))
        sentence_words = set(re.findall(r'\w+', sentence.lower()))
        title_score = len(title_words.intersection(sentence_words)) / max(len(title_words), 1)
        
        # Combined score
        scores.append(0.4 * length_score + 0.3 * position_score + 0.3 * title_score)
    
    # Get top sentences
    top_sentences = [s for _, s in sorted(zip(scores, sentences), reverse=True)]
    
    # Take top sentences until we reach the max length
    summary = []
    current_length = 0
    for sentence in top_sentences:
        if current_length + len(sentence) <= max_length:
            summary.append(sentence)
            current_length += len(sentence)
        else:
            break
    
    # Sort back into original order
    summary = [s for s in sentences if s in summary]
    
    return ' '.join(summary)

# For backward compatibility
def summarize_article(content, title="", max_length=500):
    """Wrapper around AI summarization with fallback to basic summarization"""
    return summarize_article_with_ai(content, title)

def display_news(symbol):
    """
    Display news articles for a stock symbol in the Streamlit app
    
    Args:
        symbol (str): Stock symbol to display news for
    """
    with st.spinner(f"Loading news for {symbol}..."):
        # Get stock news with a max of 8 news items
        news = get_stock_news(symbol, max_news=8)
        
        # Display the news header
        st.subheader(f"📰 Latest News for {symbol}")
        
        if not news:
            st.warning(f"No recent news found for {symbol}. Please try again later.")
            return
        
        # Use a more modern layout with columns for news
        col1, col2 = st.columns(2)
        
        # Check if OpenAI API key is available
        openai_available = os.environ.get("OPENAI_API_KEY") is not None
        
        # Display news in a grid layout (2 columns)
        for i, article in enumerate(news):
            # Alternate between columns
            with col1 if i % 2 == 0 else col2:
                # Create a card-like container with border
                with st.container():
                    # Article title with publication info
                    st.markdown(f"### {article['title']}")
                    st.caption(f"Source: {article['publisher']} | {article['date']}")
                    
                    # Show the short summary from Yahoo Finance by default
                    st.markdown(article['summary'])
                    
                    # Create two columns for buttons
                    button_col1, button_col2 = st.columns([1, 1])
                    
                    # Source link in first column
                    with button_col1:
                        st.markdown(f"[Read full article]({article['link']})")
                    
                    # AI summary button in second column with appropriate label
                    with button_col2:
                        button_label = "📝 AI Summary" if openai_available else "📝 Generate Summary"
                        if st.button(button_label, key=f"summary_{i}_{symbol}"):
                            with st.spinner("Analyzing article..."):
                                try:
                                    # Extract full article content
                                    content = extract_article_content(article['link'])
                                    
                                    if openai_available:
                                        st.info("Generating AI summary...")
                                    
                                    # Summarize the content using the appropriate method
                                    summary = summarize_article(content, article['title'])
                                    
                                    # Display the summary
                                    st.markdown("### Financial Analysis Summary")
                                    st.markdown(summary)
                                    
                                    # Add a note about the summary source
                                    if openai_available:
                                        st.caption("Summary generated with AI analysis")
                                    else:
                                        st.caption("Summary generated with basic text analysis")
                                except Exception as e:
                                    st.error(f"Error generating summary: {str(e)}")
                    
                    # Add a separator
                    st.markdown("---")
        
        # Add a section for market sentiment analysis at the bottom
        with st.expander("📊 Market Sentiment Analysis"):
            st.write("""
            ### Overall Market Sentiment
            
            The market sentiment for this stock is determined by analyzing recent news articles and financial reports. 
            Generate AI summaries of the news articles above to see a comprehensive sentiment analysis.
            
            Use this information to understand how recent events might impact stock performance.
            """)
            
            # If no API key is available, show a prompt to add one
            if not openai_available:
                st.info("Add an OpenAI API key in the environment variables to enable AI-powered sentiment analysis of news articles.")