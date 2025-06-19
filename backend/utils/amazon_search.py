"""
Amazon Search Utility

This module provides a simple function to search Amazon for products
and return a list of product URLs for the top-k results.
"""

import asyncio
from typing import List
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
try:
    from .playwright_manager import playwright_manager
except ImportError:
    from playwright_manager import playwright_manager


def search_amazon_urls(keyword: str, k: int = 5) -> List[str]:
    """
    Search Amazon for products and return top-k product URLs using synchronous Playwright.
    
    Args:
        keyword: Search keyword/phrase
        k: Number of results to return (default: 5)
        
    Returns:
        List of product URLs for top-k search results
        
    Example:
        >>> urls = search_amazon_urls("wireless headphones", 3)
        >>> print(urls)
        ['https://www.amazon.com/dp/B08ASIN123', 'https://www.amazon.com/dp/B08ASIN456', ...]
    """
    search_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
    urls = []
    
    try:
        # Use singleton browser instance
        browser = playwright_manager.get_sync_browser(headless=True)
        
        # Create a new context
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        page = context.new_page()
        
        try:
            page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for search results with better error handling
            try:
                page.wait_for_selector('[data-component-type="s-search-result"]', timeout=5000)
            except:
                print(f"Warning: Search results may not have loaded fully for '{keyword}'")
            
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
            # Close context but keep browser open for reuse
            context.close()
    
    except Exception as e:
        print(f"Error searching Amazon: {str(e)}")
    
    return urls


async def search_amazon_urls_async(keyword: str, k: int = 5) -> List[str]:
    """
    Search Amazon for products and return top-k product URLs using async Playwright.
    
    Args:
        keyword: Search keyword/phrase
        k: Number of results to return (default: 5)
        
    Returns:
        List of product URLs for top-k search results
    """
    search_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
    urls = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to search page
                await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
                
                # Wait for search results to load (with better error handling)
                try:
                    await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=5000)
                except:
                    # Try alternative selector or continue anyway
                    print(f"Warning: Search results may not have loaded fully for '{keyword}'")
                
                # Extract product URLs from search results
                items = await page.query_selector_all('[data-component-type="s-search-result"]')
                
                if not items:
                    print(f"No search results found for '{keyword}'")
                
                for item in items[:k]:
                    try:
                        # Look for product link
                        link = await item.query_selector('h2 a')
                        if link:
                            href = await link.get_attribute('href')
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
                await context.close()
                await browser.close()
    
    except Exception as e:
        print(f"Error searching Amazon: {str(e)}")
    
    return urls


if __name__ == "__main__":
    # Example usage
    keyword = "wireless headphones"
    k = 5
    
    print(f"Searching Amazon for '{keyword}' (top {k} results)...")
    urls = search_amazon_urls(keyword, k)
    
    if urls:
        print(f"\nFound {len(urls)} product URLs:")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")
    else:
        print("No URLs found.")