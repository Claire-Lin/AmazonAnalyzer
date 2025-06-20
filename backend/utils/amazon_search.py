"""
Amazon Search Utility

This module provides a simple function to search Amazon for products
and return a list of product URLs for the top-k results.
"""

import asyncio
from typing import List
from playwright.async_api import async_playwright


async def _search_amazon_async(keyword: str, k: int = 5) -> List[str]:
    """
    Asynchronously search Amazon for products and return top-k product URLs.
    
    Args:
        keyword: Search keyword/phrase
        k: Number of results to return
        
    Returns:
        List of product URLs for top-k search results
    """
    search_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
    urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        try:
            await page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
            
            # Wait for search results with increased timeout
            await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=60000)
            
            # Extract search results
            items = await page.query_selector_all('[data-component-type="s-search-result"]')
            
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
                        title_element = await item.query_selector(selector)
                        if title_element:
                            break
                    
                    if title_element:
                        href = await title_element.get_attribute('href')
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
    
    return urls


def search_amazon_urls(keyword: str, k: int = 5) -> List[str]:
    """
    Search Amazon for products and return top-k product URLs.
    
    Args:
        keyword: Search keyword/phrase
        k: Number of results to return (default: 5)
        
    Returns:
        List of product URLs for top-k search results
        
    Example:
        >>> urls = search_amazon_urls("wireless headphones", 3)
        >>> print(urls)
        ['https://www.amazon.com/...', 'https://www.amazon.com/...', ...]
    """
    try:
        return asyncio.run(_search_amazon_async(keyword, k))
    except Exception as e:
        print(f"Error searching Amazon: {str(e)}")
        return []


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