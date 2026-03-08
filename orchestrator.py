"""
Orchestrator Module
Coordinates the daily news digest pipeline using Prefect workflow orchestration.

Pipeline stages:
1. Scrape articles from Hacker News
2. Analyze and summarize articles using LLM
3. Generate executive summary digest
"""

from prefect import task, flow
import logging

from utils.news_scraper import scrape_function
from utils.article_summariser import call_llm
from utils.daily_digest import create_daily_digest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@task
def initial_data_collection():
    """
    Task 1: Scrape articles from Hacker News.
    
    Fetches yesterday's front page articles and saves them to days_news.txt.
    """
    try:
        logger.info("Starting article scraping...")
        scrape_function()
        logger.info("Scraping completed successfully")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise


@task
def summarisation():
    """
    Task 2: Analyze and summarize scraped articles.
    
    Uses LLM to generate summaries and sentiment analysis for each article.
    """
    try:
        logger.info("Starting article analysis...")
        call_llm()
        logger.info("Analysis completed successfully")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


@task
def generate_output():
    """
    Task 3: Generate daily digest.
    
    Creates an executive summary from analyzed articles for newsletter.
    """
    try:
        logger.info("Starting digest generation...")
        create_daily_digest()
        logger.info("Digest generation completed successfully")
    except Exception as e:
        logger.error(f"Digest generation failed: {e}")
        raise


@flow
def run_pipeline():
    """
    Main workflow that orchestrates the daily news digest pipeline.
    
    Executes tasks sequentially:
    1. Scrape articles
    2. Analyze articles
    3. Generate digest
    
    Each task depends on the previous one completing successfully.
    """
    try:
        logger.info("Starting daily digest pipeline...")
        initial_data_collection()
        summarisation()
        generate_output()
        logger.info("Pipeline completed successfully!")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == '__main__':
    # Schedule the pipeline to run daily at 06:00 (6 AM)
    run_pipeline.serve(name='generate_daily_digest', cron="0 6 * * *")