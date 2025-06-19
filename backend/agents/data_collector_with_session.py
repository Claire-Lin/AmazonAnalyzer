import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langgraph.prebuilt import create_react_agent
import functools

try:
    from .tools import amazon_scraper as _amazon_scraper, amazon_search as _amazon_search
except ImportError:
    from tools import amazon_scraper as _amazon_scraper, amazon_search as _amazon_search

# Load environment variables from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Initialize model
model = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY")
)

def create_data_collector_agent(session_id: Optional[str] = None):
    """Create a data collector agent with session context"""
    
    # Create session-aware tool wrappers
    def amazon_scraper_with_session(url_or_asin: str) -> str:
        """Scrape Amazon product data"""
        return _amazon_scraper(url_or_asin, session_id=session_id)
    
    def amazon_search_with_session(keyword: str, k: int = 5) -> str:
        """Search Amazon for products"""
        return _amazon_search(keyword, k)
    
    # Create tools with session context
    tools = [
        Tool(
            name="amazon_scraper",
            func=amazon_scraper_with_session,
            description="Scrape Amazon product data. Input: Amazon URL or ASIN. Returns: JSON string with title, price, specs, and reviews"
        ),
        Tool(
            name="amazon_search",
            func=amazon_search_with_session,
            description="Search Amazon for products. Input: search keyword. Returns: List of product URLs"
        )
    ]
    
    # Create agent
    agent = create_react_agent(
        model=model,
        tools=tools,
        name="data_collector",
        prompt="""You are a data collection specialist for Amazon product analysis.

Your responsibilities:
1. Use amazon_scraper to extract product information (title, price, specs, reviews) from Amazon URLs or ASINs
2. Use amazon_search to find competitor products based on relevant keywords
3. Collect comprehensive data for both main product and competitors

When collecting data:
- Always start by scraping the main product URL provided by the user
- Generate 3-5 relevant search keywords based on the main product's title and category
- Search for competitors using those keywords
- Scrape data for top 3-5 competitors
- Organize all collected data clearly

Important:
- Be thorough in data collection
- Ensure all product information is captured
- Focus on factual data extraction without analysis
"""
    )
    
    return agent

# Create default instance for backward compatibility
data_collector_agent = create_data_collector_agent()