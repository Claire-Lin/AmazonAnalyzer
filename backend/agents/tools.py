import json
import asyncio
from typing import List, Dict, Any, Optional
import sys
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
try:
    from .prompts import get_product_analysis_prompt, get_competitor_analysis_prompt, get_market_positioning_prompt, get_product_optimizer_prompt
    from .session_context import get_session_id
    from .websocket_utils import send_websocket_notification_sync
except ImportError:
    from prompts import get_product_analysis_prompt, get_competitor_analysis_prompt, get_market_positioning_prompt, get_product_optimizer_prompt
    from session_context import get_session_id
    from websocket_utils import send_websocket_notification_sync

# Load environment variables from project root
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)
print(f"OPENAI_API_KEY loaded: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")

# Add the utils directory to the path so we can import utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from amazon_scraper import AmazonScraper
from amazon_search import search_amazon_urls

# Import WebSocket manager for real-time updates
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from services.websocket_manager import websocket_manager
except ImportError:
    websocket_manager = None

# Initialize LLM model for analysis
llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.3
)

async def amazon_scraper_async(url: str, session_id: Optional[str] = None) -> str:
    """
    Scrape Amazon product data.
    Input: Amazon URL 
    Returns: JSON string with title, price, specs, and reviews
    """
    # Get session_id from context if not provided
    if session_id is None:
        session_id = get_session_id()
        print(f"📍 amazon_scraper - Retrieved session_id from context: {session_id}")
    
    # Send WebSocket notification
    print(f"🔍 amazon_scraper - session_id: {session_id}, websocket_manager: {websocket_manager is not None}")
    if websocket_manager and session_id:
        try:
            send_websocket_notification_sync(
                websocket_manager=websocket_manager,
                session_id=session_id,
                agent_name="data_collector",
                status="working",
                progress=0.2,
                current_task="Scraping product data",
                thinking_step=f"Extracting product information from {url}..."
            )
        except Exception as e:
            print(f"WebSocket notification failed: {e}")
    
    print(f"Scraping Amazon product data for: {url}")
    try:
        scraper = AmazonScraper(headless=True)
        product_data = await scraper.scrape_product(url)
        
        # If scraping failed completely, return error information
        if not product_data.get('title') and not product_data.get('success', True):
            print("⚠️ Scraping failed, unable to extract product data")
            # Return the actual failed scraping result instead of mock data
            if not product_data.get('success', True):
                pass  # Keep the original error result
        
        # Send completion notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="data_collector",
                    status="working",
                    progress=0.4,
                    current_task="Product data extracted",
                    thinking_step=f"Successfully scraped: {product_data.get('title', 'Unknown product')}"
                )
            except Exception as e:
                print(f"WebSocket notification failed: {e}")
        
        return json.dumps(product_data, indent=2)
    except Exception as e:
        # Send error notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="data_collector",
                    status="error",
                    progress=0.0,
                    current_task="Scraping failed",
                    error_message=f"Failed to scrape product: {str(e)}"
                )
            except Exception as ws_e:
                print(f"WebSocket notification failed: {ws_e}")
        
        return json.dumps({
            "error": f"Failed to scrape Amazon product: {str(e)}",
            "success": False,
            "url": url
        }, indent=2)

async def amazon_search_async(keyword: str, k: int = 5, session_id: Optional[str] = None) -> str:
    """
    Search Amazon for products.
    Input: Search keyword and number of results (k)
    Returns: String with top-k Amazon product URLs
    """
    # Get session_id from context if not provided
    if session_id is None:
        session_id = get_session_id()
    
    # Send WebSocket notification
    if websocket_manager and session_id:
        try:
            send_websocket_notification_sync(
                websocket_manager=websocket_manager,
                session_id=session_id,
                agent_name="data_collector",
                status="working",
                progress=0.6,
                current_task="Searching for competitors",
                thinking_step=f"Searching Amazon for '{keyword}' (top {k} results)..."
            )
        except Exception as e:
            print(f"WebSocket notification failed: {e}")

    print(f"Searching Amazon for keyword: {keyword} (top {k} results)")
    try:
        # Import the internal async function
        from amazon_search import _search_amazon_async
        urls = await _search_amazon_async(keyword, k)
        
        # Send completion notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="data_collector",
                    status="working",
                    progress=0.8,
                    current_task="Competitor URLs found",
                    thinking_step=f"Found {len(urls) if urls else 0} competitor products for '{keyword}'"
                )
            except Exception as e:
                print(f"WebSocket notification failed: {e}")
        
        return "\n".join(urls) if urls else f"No search results found for keyword: {keyword}"
    except Exception as e:
        # Send error notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="data_collector",
                    status="error",
                    progress=0.0,
                    current_task="Search failed",
                    error_message=f"Failed to search Amazon: {str(e)}"
                )
            except Exception:
                pass
        
        return f"Error searching Amazon: {str(e)}"


def amazon_scraper(url: str, session_id: Optional[str] = None) -> str:
    """
    Scrape Amazon product data using requests-based scraper.
    Input: Amazon URL
    Returns: JSON string with title, price, specs, and reviews
    """
    # Get session_id from context if not provided
    if session_id is None:
        session_id = get_session_id()
        print(f"📍 amazon_scraper - Retrieved session_id from context: {session_id}")
    
    # Send WebSocket notification
    print(f"🔍 amazon_scraper - session_id: {session_id}, websocket_manager: {websocket_manager is not None}")
    if websocket_manager and session_id:
        try:
            send_websocket_notification_sync(
                websocket_manager=websocket_manager,
                session_id=session_id,
                agent_name="data_collector",
                status="working",
                progress=0.2,
                current_task="Scraping product data",
                thinking_step=f"Extracting product information from {url}..."
            )
        except Exception as e:
            print(f"WebSocket notification failed: {e}")
    
    print(f"Scraping Amazon product data for: {url}")
    try:
        scraper = AmazonScraper(headless=True)
        product_data = asyncio.run(scraper.scrape_product(url))
        
        # Handle bot detection gracefully
        if product_data.get('bot_detected'):
            print("🤖 Bot detected - providing basic product info for analysis")
            # For bot-detected products, provide minimal info but don't fail completely
            product_data['analysis_note'] = 'Product data limited due to anti-bot measures'
            product_data['success'] = True  # Mark as success for analysis to continue
        elif not product_data.get('title') and not product_data.get('success', True):
            print("⚠️ Scraping failed, unable to extract product data")
            # Return the actual failed scraping result
        
        # Send completion notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="data_collector",
                    status="working",
                    progress=0.4,
                    current_task="Product data extracted",
                    thinking_step=f"Successfully scraped: {product_data.get('title', 'Unknown product')}"
                )
            except Exception as e:
                print(f"WebSocket notification failed: {e}")
        
        return json.dumps(product_data, indent=2)
    except Exception as e:
        # Send error notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="data_collector",
                    status="error",
                    progress=0.0,
                    current_task="Scraping failed",
                    error_message=f"Failed to scrape product: {str(e)}"
                )
            except Exception as ws_e:
                print(f"WebSocket notification failed: {ws_e}")
        
        return json.dumps({
            "error": f"Failed to scrape Amazon product: {str(e)}",
            "success": False,
            "url": url
        }, indent=2)


def amazon_search(keyword: str, k: int = 5, session_id: Optional[str] = None) -> str:
    """
    Synchronous Amazon search using sync Playwright.
    Search Amazon for products.
    Input: Search keyword and number of results (k)
    Returns: String with top-k Amazon product URLs
    """
    from playwright.sync_api import sync_playwright
    
    # Get session_id from context if not provided
    if session_id is None:
        session_id = get_session_id()
    
    # Send WebSocket notification
    if websocket_manager and session_id:
        try:
            send_websocket_notification_sync(
                websocket_manager=websocket_manager,
                session_id=session_id,
                agent_name="data_collector",
                status="working",
                progress=0.6,
                current_task="Searching for competitors",
                thinking_step=f"Searching Amazon for '{keyword}' (top {k} results)..."
            )
        except Exception as e:
            print(f"WebSocket notification failed: {e}")

    print(f"Searching Amazon for keyword: {keyword} (top {k} results)")
    search_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
    urls = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = context.new_page()
            
            try:
                page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
                
                # Wait for search results with increased timeout
                page.wait_for_selector('[data-component-type="s-search-result"]', timeout=60000)
                
                # Extract search results
                items = page.query_selector_all('[data-component-type="s-search-result"]')
                
                for item in items[:k]:
                    try:
                        # Try multiple selectors for product links
                        selectors = [
                            'h2 a',
                            '.a-link-normal',
                            'a[data-asin]',
                            'h2 .a-link-normal',
                            '.s-link-style a'
                        ]
                        
                        title_element = None
                        for selector in selectors:
                            title_element = item.query_selector(selector)
                            if title_element:
                                break
                        
                        if title_element:
                            href = title_element.get_attribute('href')
                            if href:
                                # Convert relative URL to absolute URL
                                if href.startswith('/'):
                                    url = f"https://www.amazon.com{href}"
                                else:
                                    url = href
                                urls.append(url)
                    except:
                        continue
                        
            except Exception as e:
                print(f"Error during search: {e}")
            finally:
                context.close()
                browser.close()
        
        # Send completion notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="data_collector",
                    status="working",
                    progress=0.8,
                    current_task="Competitor URLs found",
                    thinking_step=f"Found {len(urls)} competitor products for '{keyword}'"
                )
            except Exception as e:
                print(f"WebSocket notification failed: {e}")
        
        return "\n".join(urls) if urls else f"No search results found for keyword: {keyword}"
        
    except Exception as e:
        # Send error notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="data_collector",
                    status="error",
                    progress=0.0,
                    current_task="Search failed",
                    error_message=f"Failed to search Amazon: {str(e)}"
                )
            except Exception:
                pass
        
        print(f"Error in amazon_search: {e}")
        return f"Error searching Amazon: {str(e)}"


def product_analysis(product_info: str, session_id: Optional[str] = None) -> str:
    """
    Analyze product current status.
    Input: Main product information (string)
    Returns: Product status analysis result (string)
    """
    # Send WebSocket notification
    if websocket_manager and session_id:
        try:
            send_websocket_notification_sync(
                websocket_manager=websocket_manager,
                session_id=session_id,
                agent_name="market_analyzer",
                status="working",
                progress=0.2,
                current_task="Analyzing product",
                thinking_step="Evaluating product features, pricing, and market positioning..."
            )
        except Exception:
            pass

    print(f"Analyzing product...")
    try:
        # Get analysis prompt from prompts module
        analysis_prompt = get_product_analysis_prompt(product_info)

        # Get analysis from LLM
        response = llm.invoke(analysis_prompt)
        
        # Send completion notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="market_analyzer",
                    status="working",
                    progress=0.4,
                    current_task="Product analysis complete",
                    thinking_step="Generated comprehensive product status analysis"
                )
            except Exception:
                pass
        
        return f"## Product Analysis\n\n{response.content}"

    except Exception as e:
        # Send error notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="market_analyzer",
                    status="error",
                    progress=0.0,
                    current_task="Analysis failed",
                    error_message=f"Failed to analyze product: {str(e)}"
                )
            except Exception:
                pass
        
        return f"Error analyzing product: {str(e)}\n\nFallback analysis: The product appears to be positioned in the market with standard features. Further analysis would require more detailed product information and market data."

def competitor_analysis(main_product_info: str, competitor_infos: str, session_id: Optional[str] = None) -> str:
    """
    Analyze competitors against main product.
    Input: Main product info and multiple competitor infos (strings)
    Returns: Competitor analysis result (string)
    """
    # Debug logging
    print(f"🔍 competitor_analysis called")
    
    # Send WebSocket notification
    if websocket_manager and session_id:
        try:
            send_websocket_notification_sync(
                websocket_manager=websocket_manager,
                session_id=session_id,
                agent_name="market_analyzer",
                status="working",
                progress=0.6,
                current_task="Analyzing competitors",
                thinking_step=f"Comparing against competitors..."
            )
        except Exception:
            pass

    print(f"Analyzing competitors for main product...")
    try:
        # Get analysis prompt from prompts module
        analysis_prompt = get_competitor_analysis_prompt(main_product_info, competitor_infos)
        
        # Debug: show what we're sending to the LLM
        print(f"📝 Competitor analysis prompt preview: {analysis_prompt[:200]}...")

        # Get analysis from LLM
        response = llm.invoke(analysis_prompt)
        
        # Send completion notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="market_analyzer",
                    status="working",
                    progress=0.8,
                    current_task="Competitor analysis complete",
                    thinking_step="Generated detailed competitive positioning analysis"
                )
            except Exception:
                pass
        
        return f"## Competitor Analysis\n\n{response.content}"

    except Exception as e:
        # Send error notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="market_analyzer",
                    status="error",
                    progress=0.0,
                    current_task="Competitor analysis failed",
                    error_message=f"Failed to analyze competitors: {str(e)}"
                )
            except Exception:
                pass
        
        return f"Error analyzing competitors: {str(e)}\n\nFallback analysis: Competitive analysis requires detailed product and competitor information. The main product appears to be positioned within a competitive market with various competing features and pricing strategies."

def market_positioning(product_analysis_result: str, competitor_analysis_result: str, session_id: Optional[str] = None) -> str:
    """
    Generate market positioning suggestions.
    Input: Product status analysis and competitor analysis results
    Returns: Market positioning suggestions (string)
    """
    # Send WebSocket notification
    if websocket_manager and session_id:
        try:
            send_websocket_notification_sync(
                websocket_manager=websocket_manager,
                session_id=session_id,
                agent_name="market_analyzer",
                status="working",
                progress=0.9,
                current_task="Generating positioning strategy",
                thinking_step="Creating market positioning recommendations based on analysis..."
            )
        except Exception:
            pass

    print("Generating market positioning suggestions...")
    try:
        # Get positioning prompt from prompts module
        positioning_prompt = get_market_positioning_prompt(product_analysis_result, competitor_analysis_result)

        # Get positioning strategy from LLM
        response = llm.invoke(positioning_prompt)
        
        # Send completion notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="market_analyzer",
                    status="completed",
                    progress=1.0,
                    current_task="Market positioning complete",
                    thinking_step="Successfully generated positioning strategy recommendations"
                )
            except Exception:
                pass
        
        return response.content

    except Exception as e:
        # Send error notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="market_analyzer",
                    status="error",
                    progress=0.0,
                    current_task="Positioning strategy failed",
                    error_message=f"Failed to generate positioning: {str(e)}"
                )
            except Exception:
                pass
        
        return f"Error generating market positioning: {str(e)}\n\nFallback positioning: Based on the analysis, consider positioning as a premium quality leader with focus on superior features and value proposition. Target quality-conscious consumers and emphasize unique differentiators in marketing messaging."

def product_optimizer(main_product_info: str, market_positioning_suggestions: str, session_id: Optional[str] = None) -> str:
    """
    Generate product optimization strategy.
    Input: Main product info and market positioning suggestions
    Returns: Product optimization strategy (string)
    """
    # Debug logging
    print(f"🔍 product_optimizer called with:")
    print(f"   - main_product_info length: {len(main_product_info) if main_product_info else 0}")
    print(f"   - market_positioning_suggestions length: {len(market_positioning_suggestions) if market_positioning_suggestions else 0}")
    
    # Send WebSocket notification
    if websocket_manager and session_id:
        try:
            send_websocket_notification_sync(
                websocket_manager=websocket_manager,
                session_id=session_id,
                agent_name="optimization_advisor",
                status="working",
                progress=0.5,
                current_task="Creating optimization strategy",
                thinking_step="Generating actionable recommendations for product improvement..."
            )
        except Exception:
            pass

    print("Generating product optimization strategy...")
    try:
        # Get optimization prompt from prompts module
        optimization_prompt = get_product_optimizer_prompt(main_product_info, market_positioning_suggestions)
        
        # Debug: show what we're sending to the LLM
        print(f"📝 Optimization prompt preview: {optimization_prompt[:200]}...")

        # Get optimization strategy from LLM
        response = llm.invoke(optimization_prompt)
        
        # Send completion notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="optimization_advisor",
                    status="completed",
                    progress=1.0,
                    current_task="Optimization strategy complete",
                    thinking_step="Successfully generated comprehensive optimization recommendations"
                )
            except Exception:
                pass
        
        return response.content

    except Exception as e:
        # Send error notification
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="optimization_advisor",
                    status="error",
                    progress=0.0,
                    current_task="Optimization failed",
                    error_message=f"Failed to generate optimization: {str(e)}"
                )
            except Exception:
                pass
        
        return f"Error generating product optimization: {str(e)}\n\nFallback optimization: Focus on improving product title, description, pricing strategy, and image optimization. Consider implementing A+ content, review management, and strategic promotions to enhance product performance on Amazon marketplace."