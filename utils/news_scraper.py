"""
News Scraper Module
Scrapes articles from Hacker News front page for a given date and extracts article content.
Outputs articles in JSON format.
"""

import trafilatura
import datetime as dt
import requests
from bs4 import BeautifulSoup
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def scrape_function():
    """
    Scrapes articles from Hacker News front page for yesterday's date.
    
    This function:
    1. Fetches the HN front page for yesterday
    2. Extracts all article links from the page
    3. Follows pagination to get all articles
    4. Downloads and extracts article content using trafilatura
    5. Saves articles in JSON format to 'days_news.txt'
    
    Output format: JSON array of objects with 'url' and 'content' fields
    
    Raises:
        requests.RequestException: If network requests fail
        IOError: If file writing fails
    """
    base_url = 'https://news.ycombinator.com/'
    yesterdays_date = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(days=1), '%Y-%m-%d')
    full_url = base_url + 'front?day=' + yesterdays_date
    
    logger.info(f"Starting scrape for date: {yesterdays_date}")
    
    try:
        # Fetch the initial page
        resp = requests.get(full_url, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch HN front page: {e}")
        raise
    
    try:
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        
        if not table:
            logger.warning("No table found on page - may be empty or structure changed")
            return
        
        # Extract all article links from the page
        titlelines = table.find_all('span', {'class': 'titleline'})
        all_links = []
        
        for titleline in titlelines:
            link_tag = titleline.find('a')
            if link_tag and link_tag.get('href'):
                all_links.append(link_tag.get('href'))
        
        more = soup.find('a', {'class': 'morelink'})

        # Follow pagination to get all articles
        while more:
            try:
                new_url = base_url + more.get('href')
                response = requests.get(new_url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                table = soup.find('table')
                if table:
                    titlelines = table.find_all('span', {'class': 'titleline'})
                    for titleline in titlelines:
                        link_tag = titleline.find('a')
                        if link_tag and link_tag.get('href'):
                            all_links.append(link_tag.get('href'))
                
                more = soup.find('a', {'class': 'morelink'})
            except requests.RequestException as e:
                logger.warning(f"Failed to fetch pagination page: {e}")
                break
    except Exception as e:
        logger.error(f"Error parsing HTML: {e}")
        raise


    logger.info(f"Found {len(all_links)} total links")
    
    # Store articles in a list of dictionaries
    articles_data = []
    
    # Process each article link
    successful_articles = 0
    for i, link in enumerate(all_links, 1):
        logger.info(f"Processing link {i}/{len(all_links)}: {link}")
        
        try:
            # Fetch and extract article content
            downloaded = trafilatura.fetch_url(link)
            
            if downloaded:
                result = trafilatura.extract(downloaded, include_comments=False)
                
                # Only save articles with substantial content (>500 chars)
                if result and len(result) > 500:
                    article_obj = {
                        "url": link,
                        "content": result,
                        "scraped_at": dt.datetime.now().isoformat()
                    }
                    articles_data.append(article_obj)
                    logger.info(f"Successfully saved article from {link}")
                    successful_articles += 1
                else:
                    logger.debug(f"Skipped: {link} (No content or too short)")
            else:
                logger.warning(f"Failed to fetch: {link}")
        except Exception as e:
            logger.error(f"Error processing {link}: {e}")
            continue
    
    # Save articles as JSON to text file
    try:
        output_data = {
            "scrape_date": dt.datetime.now().isoformat(),
            "total_articles": len(articles_data),
            "articles": articles_data
        }
        
        with open('days_news.txt', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Scraping complete. Saved {successful_articles}/{len(all_links)} articles in JSON format")
    except IOError as e:
        logger.error(f"Failed to write JSON output file: {e}")
        raise
