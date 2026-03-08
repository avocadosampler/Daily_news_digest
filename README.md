# Hacker News Daily Digest

An automated pipeline that scrapes articles from Hacker News, analyzes them using AI, and generates a concise daily digest for tech news enthusiasts.

## Overview

This application automates the process of staying up-to-date with tech news by:
1. Scraping yesterday's top articles from Hacker News
2. Extracting and storing article content in structured JSON format
3. Batch-processing articles through an LLM for summarization and sentiment analysis
4. Generating an executive summary digest for quick consumption

## Features

- **Automated Scraping**: Fetches all articles from Hacker News front page with pagination support
- **Efficient Processing**: Analyzes 50 articles per API call to minimize costs
- **JSON Data Format**: Structured data storage for easy parsing and integration
- **Sentiment Analysis**: Provides sentiment insights for each article
- **Daily Digest**: Executive summary highlighting key trends and major news
- **Robust Error Handling**: Comprehensive logging and graceful failure recovery
- **Scheduled Execution**: Runs automatically via Prefect workflow orchestration

## Architecture

```
orchestrator.py          # Main workflow coordinator (Prefect)
├── utils/
│   ├── news_scraper.py       # Scrapes HN articles → JSON
│   ├── article_summariser.py # Batch LLM analysis → JSON
│   └── daily_digest.py       # Generates executive summary
```

## Prerequisites

- Python 3.11+
- OpenRouter API key (for LLM access)
- Required Python packages (see Installation)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install dependencies:
```bash
pip install prefect trafilatura requests beautifulsoup4 openai python-dotenv
```

3. Create a `.env` file in the `utils/` directory:
```env
OPENROUTER_API_KEY=your_api_key_here
```

## Configuration

### Batch Size
Modify the batch size in `utils/article_summariser.py`:
```python
BATCH_SIZE = 50  # Process 50 articles per API call
```

### LLM Model
Change the model in both `article_summariser.py` and `daily_digest.py`:
```python
LLM_MODEL = "google/gemini-2.5-flash"
```

### Schedule
Adjust the cron schedule in `orchestrator.py`:
```python
run_pipeline.serve(name='generate_daily_digest', cron="0 6 * * *")  # Runs at 6 AM daily
```

## Usage

### Run Once
Execute the pipeline manually:
```bash
python orchestrator.py
```

### Run as Scheduled Service
Deploy with Prefect for automated daily execution:
```bash
python orchestrator.py
```

The pipeline will run daily at the scheduled time (default: 6:00 AM).

### Run Individual Components

Scrape articles only:
```bash
python -c "from utils.news_scraper import scrape_function; scrape_function()"
```

Analyze articles only:
```bash
python -c "from utils.article_summariser import call_llm; call_llm()"
```

Generate digest only:
```bash
python -c "from utils.daily_digest import create_daily_digest; create_daily_digest()"
```

## Output Files

### days_news.txt
JSON format containing scraped articles:
```json
{
  "scrape_date": "2026-03-08T10:30:00",
  "total_articles": 150,
  "articles": [
    {
      "url": "https://example.com/article",
      "content": "Article text...",
      "scraped_at": "2026-03-08T10:30:15"
    }
  ]
}
```

### analysed_articles_DD_MM_YYYY.txt
JSON format containing article analyses:
```json
{
  "analysis_date": "2026-03-08T11:00:00",
  "total_articles": 150,
  "successful_batches": 3,
  "failed_batches": 0,
  "analyses": [
    {
      "url": "https://example.com/article",
      "summary": "Brief summary of the article...",
      "sentiment": "positive"
    }
  ]
}
```

### daily_digest.txt
Plain text executive summary:
```
TECH NEWS DAILY DIGEST - 2026-03-08 12:00
==================================================

[Executive summary paragraph highlighting key trends and major news items]

==================================================
Based on 150 articles
```

## How It Works

### 1. Scraping (news_scraper.py)
- Fetches Hacker News front page for yesterday's date
- Follows pagination links to collect all articles
- Extracts article content using Trafilatura
- Filters articles with substantial content (>500 characters)
- Saves structured data in JSON format

### 2. Analysis (article_summariser.py)
- Loads articles from JSON file
- Groups articles into batches of 50
- Sends each batch to LLM with instructions to return JSON
- Parses LLM responses and handles errors gracefully
- Saves all analyses in structured JSON format

### 3. Digest Generation (daily_digest.py)
- Reads analyzed articles from JSON
- Formats summaries for digest generation
- Sends to LLM for executive summary creation
- Saves final digest as readable text file

### 4. Orchestration (orchestrator.py)
- Coordinates all three stages using Prefect
- Provides logging and error tracking
- Enables scheduled execution via cron
- Ensures tasks run sequentially with proper dependencies

## Error Handling

The application includes comprehensive error handling:
- Network timeouts and request failures
- Missing or malformed HTML structure
- File I/O errors
- JSON parsing errors
- LLM API failures
- Missing environment variables

All errors are logged with detailed messages for debugging.

## Performance & Cost Optimization

- **Batch Processing**: Reduces API calls by 98% (50 articles per call vs. 1 per call)
- **Content Truncation**: Limits article content to 3000 characters to manage token usage
- **Smart Filtering**: Only processes articles with substantial content
- **Efficient Model**: Uses Gemini 2.5 Flash for cost-effective processing

## Logging

All modules use Python's logging framework with INFO level by default. Logs include:
- Timestamps
- Log levels (INFO, WARNING, ERROR)
- Detailed error messages
- Progress indicators

## Troubleshooting

### "OPENROUTER_API_KEY not found"
Ensure your `.env` file is in the `utils/` directory with the correct API key.

### "days_news.txt not found"
Run the scraper first before attempting analysis or digest generation.

### "Failed to parse JSON"
Check that the LLM is returning valid JSON. The code handles markdown code blocks automatically.

### Network timeouts
The scraper includes 10-second timeouts. Increase if needed in `news_scraper.py`.

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing style and structure
- Error handling is comprehensive
- Logging is informative
- Documentation is updated

## License

[Your License Here]

## Acknowledgments

- Hacker News for providing the content
- Trafilatura for article extraction
- OpenRouter for LLM API access
- Prefect for workflow orchestration
