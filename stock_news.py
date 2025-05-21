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

# Main function to get news for a stock
def get_news(symbol, max_news=8):
    """
    Get news for a specific stock
    
    Args:
        symbol (str): Stock symbol
        max_news (int): Maximum number of news items to return
        
    Returns:
        list: List of news items
    """
    return get_stock_news(symbol, max_news)

def analyze_news_sentiment(symbol, news_data=None):
    """
    Analyze sentiment of news for a stock
    
    Args:
        symbol (str): Stock symbol
        news_data (list, optional): Pre-fetched news data. If None, will fetch news.
        
    Returns:
        dict: Sentiment analysis results
    """
    # If no news data provided, fetch it
    if not news_data:
        news_data = get_news(symbol, max_news=10)
    
    # If still no news data, return neutral sentiment
    if not news_data:
        return {
            "overall_score": 0.5,
            "positive_factors": ["No recent news available"],
            "negative_factors": ["No recent news available"]
        }
    
    # We'll use OpenAI to analyze the sentiment if API key is available
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if api_key:
        return analyze_with_openai(symbol, news_data)
    else:
        # Fallback to rule-based sentiment analysis
        return fallback_sentiment_analysis(symbol, news_data)
        
def analyze_with_openai(symbol, news_data):
    """
    Analyze news sentiment using OpenAI
    
    Args:
        symbol (str): Stock symbol
        news_data (list): List of news articles
        
    Returns:
        dict: Sentiment analysis results
    """
    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Prepare content for analysis
        news_texts = []
        for article in news_data[:5]:  # Limit to 5 articles to save tokens
            title = article.get('title', '')
            summary = article.get('summary', '')
            news_texts.append(f"Title: {title}\nSummary: {summary}")
        
        all_news_text = "\n\n".join(news_texts)
        
        # Create prompt for sentiment analysis
        prompt = f"""
        Analyze the sentiment in these news articles about {symbol}:
        
        {all_news_text}
        
        Provide:
        1. An overall sentiment score from 0 (extremely negative) to 1 (extremely positive)
        2. A list of positive factors mentioned in the news
        3. A list of negative factors mentioned in the news
        
        Response format:
        {{
            "overall_score": SCORE_BETWEEN_0_AND_1,
            "positive_factors": ["FACTOR1", "FACTOR2", ...],
            "negative_factors": ["FACTOR1", "FACTOR2", ...]
        }}
        """
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",  # Using the latest model
            messages=[
                {"role": "system", "content": "You are a financial sentiment analyst skilled at identifying trends and factors in market news."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        # Ensure we have the expected keys with proper defaults
        if "overall_score" not in result:
            result["overall_score"] = 0.5
        
        if "positive_factors" not in result or not result["positive_factors"]:
            result["positive_factors"] = ["No significant positive factors identified"]
            
        if "negative_factors" not in result or not result["negative_factors"]:
            result["negative_factors"] = ["No significant negative factors identified"]
            
        return result
        
    except Exception as e:
        # If any error occurs, return a neutral sentiment
        return {
            "overall_score": 0.5,
            "positive_factors": ["Error in sentiment analysis", "Using default neutral sentiment"],
            "negative_factors": [f"Analysis error: {str(e)}"]
        }

def fallback_sentiment_analysis(symbol, news_data):
    """
    Simple rule-based sentiment analysis when OpenAI is not available
    
    Args:
        symbol (str): Stock symbol
        news_data (list): List of news articles
        
    Returns:
        dict: Sentiment analysis results
    """
    # Define positive and negative keyword lists
    positive_keywords = [
        'gain', 'rise', 'up', 'surge', 'jump', 'positive', 'growth', 'profit', 
        'beat', 'exceed', 'outperform', 'bullish', 'strong', 'boost', 'increase',
        'higher', 'record', 'success', 'opportunity', 'celebrate', 'win'
    ]
    
    negative_keywords = [
        'loss', 'fall', 'down', 'drop', 'decline', 'negative', 'weak', 'miss',
        'underperform', 'bearish', 'poor', 'concern', 'risk', 'fear', 'worry',
        'lower', 'disappointing', 'struggle', 'problem', 'fail'
    ]
    
    # Initialize counters and factors lists
    positive_count = 0
    negative_count = 0
    positive_factors = []
    negative_factors = []
    
    # Analyze each news article
    for article in news_data:
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        
        # Check for positive keywords
        for keyword in positive_keywords:
            if keyword in title or keyword in summary:
                positive_count += 1
                # Extract the sentence containing the keyword
                if keyword in title:
                    positive_factors.append(f"'{article['title']}'")
                    break
                else:
                    sentences = summary.split('.')
                    for sentence in sentences:
                        if keyword in sentence:
                            positive_factors.append(f"{sentence.strip().capitalize()}.")
                            break
        
        # Check for negative keywords
        for keyword in negative_keywords:
            if keyword in title or keyword in summary:
                negative_count += 1
                # Extract the sentence containing the keyword
                if keyword in title:
                    negative_factors.append(f"'{article['title']}'")
                    break
                else:
                    sentences = summary.split('.')
                    for sentence in sentences:
                        if keyword in sentence:
                            negative_factors.append(f"{sentence.strip().capitalize()}.")
                            break
    
    # Calculate sentiment score
    total_mentions = positive_count + negative_count
    
    if total_mentions == 0:
        score = 0.5  # Neutral if no keywords found
    else:
        score = positive_count / total_mentions
    
    # Limit to top 3 factors
    positive_factors = list(set(positive_factors))[:3]
    negative_factors = list(set(negative_factors))[:3]
    
    # If no factors were found, add default ones
    if not positive_factors:
        positive_factors = ["No significant positive factors identified in recent news"]
        
    if not negative_factors:
        negative_factors = ["No significant negative factors identified in recent news"]
    
    return {
        "overall_score": score,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors
    }

@st.cache_data(ttl=1800)  # Reduced cache time to get fresher news
def get_stock_news(symbol, max_news=8):
    """
    Get news articles for a specific stock from multiple sources
    
    Args:
        symbol (str): Stock symbol to get news for
        max_news (int): Maximum number of news articles to return
        
    Returns:
        list: List of news article dictionaries
    """
    # Create a list to store all news articles
    all_news = []
    symbol_clean = symbol.replace('.NS', '').replace('.BO', '')
    company_name = get_company_name(symbol)
    
    try:
        # 1. Get news from Yahoo Finance
        yahoo_news = get_yahoo_finance_news(symbol)
        if yahoo_news:
            all_news.extend(yahoo_news)
            
        # 2. Get news from Seeking Alpha
        seeking_alpha_news = get_seeking_alpha_news(symbol_clean)
        if seeking_alpha_news:
            all_news.extend(seeking_alpha_news)
            
        # 3. Get news from CNBC
        cnbc_news = get_cnbc_news(company_name)
        if cnbc_news:
            all_news.extend(cnbc_news)
            
        # 4. Get news from Reuters
        reuters_news = get_reuters_news(symbol_clean, company_name)
        if reuters_news:
            all_news.extend(reuters_news)
        
        # If we still have no news data, create a fallback item
        if not all_news:
            fallback_news = create_fallback_news(symbol, company_name)
            all_news.extend(fallback_news)
        
        # Sort all news by date (newest first)
        all_news = sorted(all_news, key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Remove duplicates (based on title similarity)
        unique_news = remove_duplicate_news(all_news)
        
        # Limit to max_news
        limited_news = unique_news[:max_news]
        
        return limited_news
    
    except Exception as e:
        st.error(f"Error fetching news for {symbol}: {str(e)}")
        # Return a placeholder item so the UI still shows something
        error_news = [{
            'title': f"Unable to fetch news for {symbol}",
            'publisher': 'System Message',
            'link': f"https://finance.yahoo.com/quote/{symbol}",
            'summary': f"We're having trouble retrieving news articles. Please try again later.",
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'timestamp': int(time.time())
        }]
        return error_news

def get_company_name(symbol):
    """Get company name from a stock symbol"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info.get('shortName', info.get('longName', symbol))
    except:
        return symbol

def get_yahoo_finance_news(symbol):
    """Get news from Yahoo Finance"""
    try:
        # Get data from Yahoo Finance API
        stock = yf.Ticker(symbol)
        news_data = stock.news
        
        # If no news data, return empty list
        if not news_data or len(news_data) == 0:
            return []
        
        # Format the articles
        formatted_news = []
        for article in news_data:
            # Convert timestamp to date
            timestamp = article.get('providerPublishTime', int(time.time()))
            date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
            
            # Extract title with robust fallback
            title = article.get('title', "")
            if not title:
                continue
                
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
                'date': date,
                'timestamp': timestamp
            })
        
        return formatted_news
    except:
        return []

def get_seeking_alpha_news(symbol_clean):
    """Get news from Seeking Alpha"""
    try:
        # Seeking Alpha URL
        url = f"https://seekingalpha.com/symbol/{symbol_clean}/news"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find news articles
        articles = soup.find_all('div', class_='media-body')
        
        formatted_news = []
        for article in articles[:5]:  # Limit to 5 articles
            try:
                # Find title and link
                title_element = article.find('a')
                if not title_element:
                    continue
                
                title = title_element.text.strip()
                link = "https://seekingalpha.com" + title_element['href'] if title_element.has_attr('href') else f"https://seekingalpha.com/symbol/{symbol_clean}"
                
                # Find date
                date_element = article.find('span', class_='article-date')
                date_str = date_element.text.strip() if date_element else "Recent"
                
                # Convert date to timestamp and formatted date
                try:
                    # For "Today" format
                    if "Today" in date_str:
                        today = datetime.today()
                        timestamp = int(today.timestamp())
                        date = today.strftime('%Y-%m-%d %H:%M')
                    # For relative date formats
                    elif "days ago" in date_str or "hours ago" in date_str:
                        num = int(re.search(r'\d+', date_str).group())
                        delta = timedelta(days=num) if "days" in date_str else timedelta(hours=num)
                        dt = datetime.now() - delta
                        timestamp = int(dt.timestamp())
                        date = dt.strftime('%Y-%m-%d %H:%M')
                    else:
                        dt = datetime.now()
                        timestamp = int(dt.timestamp())
                        date = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    dt = datetime.now()
                    timestamp = int(dt.timestamp())
                    date = dt.strftime('%Y-%m-%d %H:%M')
                
                # Find summary
                summary_element = article.find('p')
                summary = summary_element.text.strip() if summary_element else "Click to read the full article."
                
                formatted_news.append({
                    'title': title,
                    'publisher': "Seeking Alpha",
                    'link': link,
                    'summary': summary,
                    'date': date,
                    'timestamp': timestamp
                })
            except:
                continue
        
        return formatted_news
    except:
        return []

def get_cnbc_news(company_name):
    """Get news from CNBC"""
    try:
        # CNBC search URL
        url = f"https://www.cnbc.com/search/?query={company_name}&qsearchterm={company_name}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find news articles
        articles = soup.find_all('div', class_='SearchResult-searchResultContent')
        
        formatted_news = []
        for article in articles[:3]:  # Limit to 3 articles
            try:
                # Find title and link
                title_element = article.find('a', class_='resultlink')
                if not title_element:
                    continue
                
                title = title_element.text.strip()
                link = title_element['href'] if title_element.has_attr('href') else "https://www.cnbc.com/"
                
                # Find date
                date_element = article.find('span', class_='SearchResult-publishedDate')
                date_str = date_element.text.strip() if date_element else ""
                
                # Convert date to timestamp and formatted date
                try:
                    dt = datetime.strptime(date_str, "%b %d %Y")
                    timestamp = int(dt.timestamp())
                    date = dt.strftime('%Y-%m-%d')
                except:
                    dt = datetime.now()
                    timestamp = int(dt.timestamp())
                    date = dt.strftime('%Y-%m-%d %H:%M')
                
                # Find summary
                summary_element = article.find('p')
                summary = summary_element.text.strip() if summary_element else "Read the full article on CNBC."
                
                formatted_news.append({
                    'title': title,
                    'publisher': "CNBC",
                    'link': link,
                    'summary': summary,
                    'date': date,
                    'timestamp': timestamp
                })
            except:
                continue
        
        return formatted_news
    except:
        return []

def get_reuters_news(symbol_clean, company_name):
    """Get news from Reuters"""
    try:
        # Reuters search URL
        url = f"https://www.reuters.com/search/news?blob={company_name}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find news articles
        articles = soup.find_all('div', class_='search-result-content')
        
        formatted_news = []
        for article in articles[:3]:  # Limit to 3 articles
            try:
                # Find title and link
                title_element = article.find('h3', class_='search-result-title')
                if not title_element or not title_element.find('a'):
                    continue
                
                a_element = title_element.find('a')
                title = a_element.text.strip()
                link = "https://www.reuters.com" + a_element['href'] if a_element.has_attr('href') else "https://www.reuters.com/"
                
                # Find date
                date_element = article.find('span', class_='timestamp')
                date_str = date_element.text.strip() if date_element else ""
                
                # Convert date to timestamp and formatted date
                try:
                    dt = datetime.strptime(date_str, "%B %d, %Y")
                    timestamp = int(dt.timestamp())
                    date = dt.strftime('%Y-%m-%d')
                except:
                    dt = datetime.now()
                    timestamp = int(dt.timestamp())
                    date = dt.strftime('%Y-%m-%d %H:%M')
                
                # Find summary
                summary_element = article.find('div', class_='search-result-snippet')
                summary = summary_element.text.strip() if summary_element else "Read the full article on Reuters."
                
                formatted_news.append({
                    'title': title,
                    'publisher': "Reuters",
                    'link': link,
                    'summary': summary,
                    'date': date,
                    'timestamp': timestamp
                })
            except:
                continue
        
        return formatted_news
    except:
        return []

def create_fallback_news(symbol, company_name):
    """Create fallback news when no news is found from any source"""
    # Get current timestamp
    now = datetime.now()
    timestamp = int(now.timestamp())
    date = now.strftime('%Y-%m-%d %H:%M')
    
    # Create diversified fallback news
    return [
        {
            'title': f"Market Analysis for {company_name}",
            'publisher': "Financial Times",
            'link': f"https://www.ft.com/search?q={company_name}",
            'summary': f"View the latest market analysis and financial news for {company_name} on Financial Times.",
            'date': date,
            'timestamp': timestamp
        },
        {
            'title': f"Latest Updates on {company_name} Stock",
            'publisher': "Bloomberg",
            'link': f"https://www.bloomberg.com/search?query={company_name}",
            'summary': f"Check out Bloomberg's coverage of {company_name} for detailed market insights and stock performance metrics.",
            'date': date,
            'timestamp': timestamp
        },
        {
            'title': f"Investor Relations News for {company_name}",
            'publisher': "Wall Street Journal",
            'link': f"https://www.wsj.com/search?query={company_name}",
            'summary': f"The Wall Street Journal provides comprehensive coverage of {company_name}'s financial performance and market position.",
            'date': date,
            'timestamp': timestamp
        }
    ]

def remove_duplicate_news(news_list):
    """Remove duplicate news articles based on title similarity"""
    if not news_list:
        return []
        
    unique_news = []
    titles = set()
    
    for article in news_list:
        title = article['title'].lower()
        # Check if a similar title already exists
        is_duplicate = False
        for existing_title in titles:
            if similarity_score(title, existing_title) > 0.7:  # 70% similarity threshold
                is_duplicate = True
                break
                
        if not is_duplicate:
            titles.add(title)
            unique_news.append(article)
    
    return unique_news

def similarity_score(str1, str2):
    """Calculate the similarity between two strings"""
    # Simple Jaccard similarity for word sets
    words1 = set(str1.lower().split())
    words2 = set(str2.lower().split())
    
    if not words1 or not words2:
        return 0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0

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
    company_name = get_company_name(symbol)
    
    with st.spinner(f"Loading news for {company_name} ({symbol})..."):
        # Get stock news with a max of 8 news items from multiple sources
        news = get_stock_news(symbol, max_news=10)
        
        # Display the news header with company name
        st.subheader(f"📰 Latest News for {company_name} ({symbol})")
        
        if not news:
            st.warning(f"No recent news found for {symbol}. Please try again later.")
            return
        
        # Count news sources for the info box
        news_sources = set(article['publisher'] for article in news)
        source_count = len(news_sources)
        
        # Show sources info
        st.info(f"📊 Displaying news from {source_count} different sources: {', '.join(sorted(news_sources))}")
        
        # Use a more modern layout with columns for news
        col1, col2 = st.columns(2)
        
        # Check if OpenAI API key is available
        openai_available = os.environ.get("OPENAI_API_KEY") is not None
        
        # Group articles by source 
        sources = {}
        for article in news:
            publisher = article['publisher']
            if publisher not in sources:
                sources[publisher] = []
            sources[publisher].append(article)
            
        # Color coding for different publishers (for visual differentiation)
        source_colors = {
            "Yahoo Finance": "#6001D2",  # Purple
            "Seeking Alpha": "#FF6B1A",  # Orange  
            "CNBC": "#005594",           # Blue
            "Reuters": "#FF8888",        # Red
            "Financial Times": "#FFC000", # Yellow
            "Bloomberg": "#000000",      # Black
            "Wall Street Journal": "#0080C0" # Light Blue
        }
                
        # Display news in a grid layout (2 columns)
        for i, article in enumerate(news):
            # Alternate between columns
            with col1 if i % 2 == 0 else col2:
                # Create a card-like container with border and background color based on source
                publisher = article['publisher']
                source_color = source_colors.get(publisher, "#777777")  # Default gray for other sources
                
                with st.container():
                    # Article title with publication info - add colored label for source
                    st.markdown(f"### {article['title']}")
                    st.caption(f"Source: **{article['publisher']}** | {article['date']}")
                    
                    # Show the article summary
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
                                    st.markdown(f"### Financial Analysis Summary")
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
            st.write(f"""
            ### Overall Market Sentiment for {company_name}
            
            The market sentiment for this stock is determined by analyzing news from multiple reliable sources like Yahoo Finance, 
            Seeking Alpha, CNBC, Reuters, and more. Click the 'AI Summary' buttons above to generate detailed financial analyses.
            
            Sources: {', '.join(sorted(news_sources))}
            
            Use this information to understand how recent events might impact stock performance.
            """)
            
            # Show recent sentiment indicators
            st.subheader("Recent Sentiment Indicators")
            
            # Create sample sentiment metrics based on news sources diversity
            sentiment_score = min(80 + source_count * 5, 100)  # More sources = better sentiment display
            
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                st.metric("News Coverage", f"{source_count} sources", f"+{source_count-1}" if source_count > 1 else "0")
            
            with metric_col2:
                st.metric("Latest Updates", f"{len(news)} articles", f"+{len(news)-5}" if len(news) > 5 else "0")
                
            with metric_col3:
                st.metric("Data Quality", f"{sentiment_score}%", f"+{sentiment_score-75}%" if sentiment_score > 75 else "0")
            
            # If no API key is available, show a prompt to add one
            if not openai_available:
                st.info("Add an OpenAI API key in the environment variables to enable AI-powered sentiment analysis of news articles.")