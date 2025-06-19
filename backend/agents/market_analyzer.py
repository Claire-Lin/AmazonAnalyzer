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

Your responsibilities:
1. Use product_analysis to analyze the main product's current market status
2. Use competitor_analysis to compare the main product against multiple competitors
3. Provide comprehensive market insights and competitive positioning

Analysis approach:
- First, analyze the main product thoroughly using product_analysis
- Then, perform competitor_analysis with the main product and all competitor data
- Focus on identifying:
  * Market positioning
  * Competitive advantages and weaknesses
  * Price positioning strategy
  * Quality and feature comparison
  * Market opportunities and threats

Important:
- Be data-driven and objective in your analysis
- Identify actionable insights
- Consider both quantitative (price, ratings) and qualitative (features, reviews) factors
- Provide strategic recommendations based on the analysis
"""
)