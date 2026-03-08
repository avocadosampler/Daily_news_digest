"""
Article Summariser Module
Uses LLM to analyze and summarize scraped articles with sentiment analysis.
Processes articles in batches of 50 for efficiency.
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

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = "google/gemini-2.5-flash"
BATCH_SIZE = 50  # Process 50 articles per API call

# Validate API key
if not OPENROUTER_API_KEY:
    logger.error("OPENROUTER_API_KEY not found in environment variables")
    raise ValueError("Missing OPENROUTER_API_KEY in .env file")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)


def call_llm():
    """
    Analyzes scraped articles using an LLM to generate summaries and sentiment analysis.
    
    Processes articles in batches of 50 for efficiency. Reads JSON from 'days_news.txt',
    sends batches to LLM, and saves analysis in JSON format to a dated output file.
    
    Raises:
        FileNotFoundError: If days_news.txt doesn't exist
        IOError: If file operations fail
        json.JSONDecodeError: If JSON parsing fails
        Exception: If LLM API calls fail
    """
    # Read scraped articles from JSON file
    try:
        with open('days_news.txt', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error("days_news.txt not found. Run scraper first.")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from days_news.txt: {e}")
        raise
    except IOError as e:
        logger.error(f"Failed to read days_news.txt: {e}")
        raise
    
    articles = data.get('articles', [])
    
    if not articles:
        logger.warning("No articles found to analyze")
        return
    
    logger.info(f"Found {len(articles)} articles to analyze")
    
    # System prompt for batch processing
    system_content = (
        "You are a professional journalist specializing in tech news. "
        "You will receive a batch of articles in JSON format. "
        "For each article, provide a 2-3 sentence summary and sentiment analysis. "
        "Return your response as a JSON array where each object contains: "
        "url, summary, and sentiment fields. "
        "Maintain the same order as the input articles."
    )
    
    # Create output file with timestamp
    output_filename = f"analysed_articles_{dt.datetime.strftime(dt.datetime.now(), '%d_%m_%Y')}.txt"
    logger.info(f"Starting batch analysis - processing {BATCH_SIZE} articles per API call")
    
    all_analyses = []
    successful_batches = 0
    failed_batches = 0
    
    # Process articles in batches
    for batch_num in range(0, len(articles), BATCH_SIZE):
        batch = articles[batch_num:batch_num + BATCH_SIZE]
        batch_end = min(batch_num + BATCH_SIZE, len(articles))
        
        logger.info(f"Processing batch {batch_num // BATCH_SIZE + 1}: articles {batch_num + 1}-{batch_end}")
        
        # Prepare batch for LLM (simplified format to reduce tokens)
        batch_input = []
        for idx, article in enumerate(batch):
            batch_input.append({
                "index": batch_num + idx,
                "url": article['url'],
                "content": article['content'][:3000]  # Limit content to first 3000 chars to manage token usage
            })
        
        try:
            # Call LLM API for batch analysis
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {'role': 'system', 'content': system_content},
                    {'role': 'user', 'content': f"Analyze these articles and return JSON:\n\n{json.dumps(batch_input, ensure_ascii=False)}"}
                ],
                temperature=0.1,
                max_tokens=4000,  # Increased for batch processing
                extra_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "HN Scraper",
                }
            )
            
            # Parse LLM response
            analysis_text = response.choices[0].message.content
            
            # Extract JSON from response (handle markdown code blocks if present)
            if '```json' in analysis_text:
                analysis_text = analysis_text.split('```json')[1].split('```')[0].strip()
            elif '```' in analysis_text:
                analysis_text = analysis_text.split('```')[1].split('```')[0].strip()
            
            batch_analyses = json.loads(analysis_text)
            all_analyses.extend(batch_analyses)
            successful_batches += 1
            
            logger.info(f"Successfully analyzed batch {batch_num // BATCH_SIZE + 1}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON for batch {batch_num // BATCH_SIZE + 1}: {e}")
            logger.debug(f"Response was: {analysis_text[:500]}")
            failed_batches += 1
            
            # Add placeholder entries for failed batch
            for idx, article in enumerate(batch):
                all_analyses.append({
                    "url": article['url'],
                    "summary": "[Analysis failed]",
                    "sentiment": "unknown"
                })
        except Exception as e:
            logger.error(f"Error analyzing batch {batch_num // BATCH_SIZE + 1}: {e}")
            failed_batches += 1
            
            # Add placeholder entries for failed batch
            for idx, article in enumerate(batch):
                all_analyses.append({
                    "url": article['url'],
                    "summary": "[Analysis failed]",
                    "sentiment": "unknown"
                })
    
    # Save all analyses as JSON to text file
    try:
        output_data = {
            "analysis_date": dt.datetime.now().isoformat(),
            "total_articles": len(all_analyses),
            "successful_batches": successful_batches,
            "failed_batches": failed_batches,
            "analyses": all_analyses
        }
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis complete. Processed {len(all_analyses)} articles in {successful_batches + failed_batches} batches")
        logger.info(f"Success: {successful_batches} batches, Failed: {failed_batches} batches")
        logger.info(f"Results saved to {output_filename}")
        
    except IOError as e:
        logger.error(f"Failed to write analysis file: {e}")
        raise

