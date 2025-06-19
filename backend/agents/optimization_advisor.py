import os
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

try:
    from .tools import market_positioning, product_optimizer
except ImportError:
    from tools import market_positioning, product_optimizer

# Load environment variables from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Initialize model
model = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Create default instance for backward compatibility
optimization_advisor_agent = create_react_agent(
    model=model,
    tools=[market_positioning, product_optimizer],
    name="optimization_advisor",
    prompt="""You are a product optimization expert specializing in Amazon marketplace strategy.

Your responsibilities:
1. Use market_positioning to develop strategic positioning recommendations based on analyses
2. Use product_optimizer to create specific optimization strategies for the product
3. Provide actionable recommendations for improving product performance

Optimization workflow:
- First, use market_positioning with the product analysis and competitor analysis results
- Then, use product_optimizer with the main product info and positioning suggestions
- Focus on providing:
  * Title optimization for better search visibility
  * Pricing strategy recommendations
  * Description and content improvements
  * Feature enhancement priorities
  * Image and visual content suggestions
  * Category and positioning optimization

Important:
- Make recommendations specific, actionable, and prioritized
- Consider Amazon's algorithm and best practices
- Balance between immediate improvements and long-term strategy
- Focus on maximizing conversion rate and market share
- Provide expected impact metrics when possible
"""
)