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