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

@st.cache_data(ttl=3600)
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
        # Try to get news from Yahoo Finance
        stock = yf.Ticker(symbol)
        news = stock.news
        
        # Debug the news data
        st.session_state['debug_news'] = news if news else []
        
        # Filter and format the news
        if news and len(news) > 0:
            # Sort by date (newest first)
            news = sorted(news, key=lambda x: x.get('providerPublishTime', 0), reverse=True)
            
            # Limit to max_news
            news = news[:max_news]
            
            # Format the articles
            formatted_news = []
            for article in news:
                # Convert timestamp to date
                timestamp = article.get('providerPublishTime', 0)
                if timestamp:
                    date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
                else:
                    date = "Unknown date"
                
                # Get title and publisher, with robust error handling
                title = "No title"
                if 'title' in article and article['title']:
                    title = article['title']
                
                publisher = "Unknown publisher"
                if 'publisher' in article and article['publisher']:
                    if isinstance(article['publisher'], str):
                        publisher = article['publisher']
                    elif isinstance(article['publisher'], dict) and 'name' in article['publisher']:
                        publisher = article['publisher']['name']
                
                # Ensure link is a valid URL
                link = "#"
                if 'link' in article and article['link']:
                    link = article['link']
                
                # Ensure summary exists
                summary = "No summary available"
                if 'summary' in article and article['summary']:
                    summary = article['summary']
                
                # Append formatted article
                formatted_news.append({
                    'title': title,
                    'publisher': publisher,
                    'link': link,
                    'summary': summary,
                    'date': date
                })
            
            return formatted_news
        
        # If no news found from Yahoo Finance, return empty list
        return []
    
    except Exception as e:
        st.error(f"Error fetching news for {symbol}: {str(e)}")
        return []

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
        news = get_stock_news(symbol)
        
        if not news:
            st.warning(f"No recent news found for {symbol}")
            return
        
        st.subheader(f"📰 Latest News for {symbol}")
        
        # Check if OpenAI API key is available
        openai_available = os.environ.get("OPENAI_API_KEY") is not None
        
        for i, article in enumerate(news):
            with st.expander(f"{article['title']} - {article['publisher']} ({article['date']})"):
                # Show the short summary from Yahoo Finance by default
                st.markdown(article['summary'])
                
                # Show source link
                st.markdown(f"[Read full article]({article['link']})")
                
                # Show AI summary button with appropriate label based on API key availability
                button_label = "📝 Generate AI Summary" if openai_available else "📝 Generate Summary"
                if st.button(button_label, key=f"summary_{i}_{symbol}"):
                    with st.spinner("Analyzing article content..."):
                        try:
                            # Extract full article content
                            content = extract_article_content(article['link'])
                            
                            if openai_available:
                                st.info("Using AI to generate a comprehensive summary...")
                            
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
        
        st.markdown("---")
        
        # Add a section for market trends based on news sentiment
        st.subheader("📊 Market Sentiment Analysis")
        st.write("Analysis of recent news sentiment for this stock will appear here when you generate article summaries.")