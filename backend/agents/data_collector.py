import os
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

try:
    from .tools import amazon_scraper, amazon_search
except ImportError:
    from tools import amazon_scraper, amazon_search

# Load environment variables from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Initialize model
model = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Create default instance for backward compatibility
data_collector_agent = create_react_agent(
    model=model,
    tools=[amazon_scraper, amazon_search],
    name="data_collector",
    prompt="""You are a data collection specialist for Amazon product analysis.

Your responsibilities:
1. Use amazon_scraper to extract product information (title, price, specs, reviews) from Amazon URLs
2. Use amazon_search to find competitor products based on relevant keywords
3. Collect comprehensive data for both main product and competitors

WORKFLOW:
1. First, scrape the main product URL provided by the user using amazon_scraper
2. Extract key information from the main product
3. Generate 3-5 relevant search keywords based on:
   - Product title/name
   - Product category
   - Key features
4. Use amazon_search with ALL keywords at once:
   - Create a comma-separated list of keywords
   - Example: "laptop stand,laptop cooling pad,laptop riser"
   - The tool will search each keyword and return combined results
5. After collecting all competitor URLs, scrape the top 3-5 competitors using amazon_scraper
6. Compile all data into a structured format

EXAMPLE TOOL USAGE:
If the product is a "Gaming Laptop Stand with RGB", you would:
1. amazon_scraper("https://amazon.com/...")  # Main product only - MUST be URL
2. amazon_search("gaming laptop stand", 3)  # Search for competitors with 3 results
3. amazon_search("laptop cooling pad", 3)  # Additional keywords for more results
... # continue with other keywords
4. amazon_scraper("https://amazon.com/...") # Competitor URLs from search results
5. Repeat for each competitor URL found in the search results
6. Return a structured summary of all collected data

OUTPUT FORMAT:
Provide a comprehensive summary with the following EXACT structure:

Main Product Data: [scraped data or error details]

Search Keywords Used: [list of keywords]

Competitor URLs Found: [list of URLs from all searches]

Competitor Data:
Competitor 1: [scraped data including title, price, brand]
Competitor 2: [scraped data including title, price, brand]
Competitor 3: [scraped data including title, price, brand]
[etc.]

Output format:
{
    "main_product_data": {...},
    "competitor_data": [competitor1, competitor2, competitor3, ...],
}
"""
)

# main function for testing
def main():
    # Example usage
    product_url = "https://www.amazon.com/Tamagotchi-Nano-Peanuts-Silicone-Case/dp/B0FB7FQWJL/?_encoding=UTF8&pd_rd_w=z2Ksk&content-id=amzn1.sym.0ee7ac10-1e05-43b4-8708-e2b0e6430ef1&pf_rd_p=0ee7ac10-1e05-43b4-8708-e2b0e6430ef1&pf_rd_r=CH7HD7239THZ01SHTZ6N&pd_rd_wg=2kLkB&pd_rd_r=9344b5f4-da0d-45b3-b124-2e19d8d944eb&ref_=pd_hp_d_btf_exports_top_sellers_unrec"
    for event in data_collector_agent.stream({
        "messages": [
            {
                "role": "user",
                "content": product_url
            }
        ]
    }):
        print(event)
if __name__ == "__main__":
    main()