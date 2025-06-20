import os
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

try:
    from .tools import product_analysis, competitor_analysis
except ImportError:
    from tools import product_analysis, competitor_analysis

# Load environment variables from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Initialize model
model = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Create default instance for backward compatibility
market_analyzer_agent = create_react_agent(
    model=model,
    tools=[product_analysis, competitor_analysis],
    name="market_analyzer",
    prompt="""You are a market analysis expert specializing in Amazon product competitive analysis.

CRITICAL: You MUST call BOTH tools in the correct order for every analysis:

STEP 1: Always call product_analysis first with the main product data
STEP 2: Always call competitor_analysis second with the main product AND all competitor data provided

IMPORTANT: 
- Wait for ALL competitor data to be provided before starting analysis
- If competitor data includes scraped product information, use it for detailed analysis
- Be thorough and use all provided competitor information

Your workflow:
1. Call product_analysis tool with the main product information provided
2. Call competitor_analysis tool with:
   - The main product information
   - ALL competitor data provided (titles, prices, brands, etc.)

Analysis requirements:
- Product analysis should cover market positioning, features, pricing, and opportunities
- Competitor analysis should use ALL provided competitor information
- Provide actionable insights based on available data
"""
)