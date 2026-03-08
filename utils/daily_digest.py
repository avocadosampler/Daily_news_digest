"""
Daily Digest Module
Creates an executive summary from analyzed articles for a daily newsletter.
Reads from JSON format analysis files.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
import datetime as dt
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

LLM_MODEL = "google/gemini-2.5-flash"

# Validate API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    logger.error("OPENROUTER_API_KEY not found in environment variables")
    raise ValueError("Missing OPENROUTER_API_KEY in .env file")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


def create_daily_digest():
    """
    Generates a concise daily digest from analyzed articles.
    
    Reads article analyses from JSON format, uses LLM to create an executive summary,
    and saves the digest to 'daily_digest.txt'.
    
    Raises:
        FileNotFoundError: If analyzed articles file doesn't exist
        IOError: If file operations fail
        json.JSONDecodeError: If JSON parsing fails
        Exception: If LLM API call fails
    """
    # Find the most recent analysis file
    filename = f"analysed_articles_{dt.datetime.strftime(dt.datetime.now(), '%d_%m_%Y')}.txt"
    
    logger.info(f"Looking for analysis file: {filename}")
    
    # Read analyzed articles from JSON
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"{filename} not found. Run the analysis script first.")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {filename}: {e}")
        raise
    except IOError as e:
        logger.error(f"Failed to read analysis file: {e}")
        raise
    
    analyses = data.get('analyses', [])
    
    if not analyses:
        logger.warning("Analysis file contains no analyses")
        return
    
    logger.info(f"Found {len(analyses)} article analyses")
    
    # Format analyses for digest generation
    formatted_analyses = []
    for analysis in analyses:
        formatted_analyses.append(
            f"URL: {analysis.get('url', 'N/A')}\n"
            f"Summary: {analysis.get('summary', 'N/A')}\n"
            f"Sentiment: {analysis.get('sentiment', 'N/A')}"
        )
    
    analyses_text = "\n\n".join(formatted_analyses)
    
    # Prepare LLM prompt for digest generation
    system_message = (
        "You are a Chief Editor for a major tech publication. "
        "Your task is to read a series of article summaries from the past 24 hours "
        "and write a concise, 3-4 sentence 'Executive Summary' for a morning newsletter. "
        "Focus on the most significant trends or major news items. "
        "Maintain a professional and objective tone."
    )
    
    user_message = f"Here are the summaries from today's news:\n\n{analyses_text}"
    
    logger.info("Generating daily digest...")
    
    try:
        # Call LLM to generate digest
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        digest = response.choices[0].message.content
        
        # Save the digest to file
        try:
            with open('daily_digest.txt', 'w', encoding='utf-8') as f:
                f.write(f"TECH NEWS DAILY DIGEST - {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write("="*50 + "\n\n")
                f.write(digest)
                f.write(f"\n\n{'='*50}\n")
                f.write(f"Based on {len(analyses)} articles\n")
            
            logger.info("Success! Daily digest saved to 'daily_digest.txt'")
            logger.info("\n--- DIGEST PREVIEW ---")
            logger.info(digest)
            
        except IOError as e:
            logger.error(f"Failed to write digest file: {e}")
            raise
    
    except Exception as e:
        logger.error(f"Failed to generate digest: {e}")
        raise

