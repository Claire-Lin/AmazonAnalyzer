"""
Amazon Search Utility

This module provides a simple function to search Amazon for products
and return a list of product URLs for the top-k results.
"""

import asyncio
import requests
import re
import time
import random
from typing import List
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup


def search_amazon_urls(keyword: str, k: int = 5) -> List[str]:
    """
    Search Amazon for products and return top-k product URLs using HTTP requests.
    
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
    
    # Create a session with proper headers
    session = requests.Session()
    
    # Comprehensive headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }
    
    session.headers.update(headers)
    
    try:
        # Add random delay to appear more human-like and prevent rate limiting
        delay = random.uniform(2, 5)  # Increased delay between searches
        print(f"Waiting {delay:.1f} seconds before search...")
        time.sleep(delay)
        
        print(f"Searching Amazon for: {keyword}")
        response = session.get(search_url, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check for bot detection
            page_text = soup.get_text().lower()
            if 'robot' in page_text or 'captcha' in page_text or 'sorry' in page_text:
                print(f"❌ Bot detection triggered for search: {keyword}")
                return []
            
            # Try multiple selectors to find product links
            selectors_to_try = [
                '[data-component-type="s-search-result"]',
                '[data-asin]:not([data-asin=""])',
                '.s-result-item[data-asin]',
                '.s-search-result',
                '.sg-col-inner .s-widget-container'
            ]
            
            items = []
            for selector in selectors_to_try:
                try:
                    items = soup.select(selector)
                    if items:
                        print(f"Found {len(items)} items using selector: {selector}")
                        break
                except:
                    continue
            
            if not items:
                print(f"No search results found with any selector for '{keyword}'")
                # Try to find any product links in the page
                all_links = soup.find_all('a', href=True)
                product_links = [link for link in all_links if '/dp/' in link.get('href', '')]
                if product_links:
                    print(f"Found {len(product_links)} product links using fallback method")
                    items = product_links[:k]
                else:
                    return []
            
            # Extract URLs from found items
            for item in items[:k]:
                try:
                    # Try to get ASIN directly from data attribute
                    asin = item.get('data-asin')
                    if asin and len(asin) == 10:  # Valid ASIN length
                        url = f"https://www.amazon.com/dp/{asin}"
                        urls.append(url)
                        print(f"Found URL via ASIN: {url}")
                        continue
                    
                    # Fallback to link extraction
                    link_selectors = [
                        'h2 a[href*="/dp/"]',
                        'a[href*="/dp/"]',
                        'a[href*="/gp/product/"]',
                        'h2 a',
                        '.a-link-normal[href*="/dp/"]'
                    ]
                    
                    found_url = False
                    for link_selector in link_selectors:
                        try:
                            link_elements = item.select(link_selector)
                            for link_element in link_elements:
                                href = link_element.get('href')
                                if href and ('/dp/' in href or '/gp/product/' in href):
                                    # Convert relative URL to absolute URL
                                    if href.startswith('/'):
                                        url = f"https://www.amazon.com{href}"
                                    else:
                                        url = href
                                    
                                    # Clean URL (remove extra parameters for cleaner links)
                                    if '/dp/' in url:
                                        asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
                                        if asin_match:
                                            asin = asin_match.group(1)
                                            url = f"https://www.amazon.com/dp/{asin}"
                                    
                                    urls.append(url)
                                    print(f"Found URL via link: {url}")
                                    found_url = True
                                    break
                            if found_url:
                                break
                        except:
                            continue
                            
                    # If still no URL found, try to extract from href attribute directly
                    if not found_url and hasattr(item, 'get') and item.get('href'):
                        href = item.get('href')
                        if '/dp/' in href:
                            if href.startswith('/'):
                                url = f"https://www.amazon.com{href}"
                            else:
                                url = href
                            urls.append(url)
                            print(f"Found URL via direct href: {url}")
                            
                except Exception as e:
                    print(f"Error extracting URL from item: {e}")
                    continue
        
        elif response.status_code == 503:
            print(f"❌ Amazon blocked request (503) for search: {keyword}")
            return []
        else:
            print(f"❌ HTTP error {response.status_code} for search: {keyword}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed for search '{keyword}': {str(e)}")
        return []
    except Exception as e:
        print(f"❌ Error searching Amazon: {str(e)}")
        return []
    
    return urls


async def search_amazon_urls_async(keyword: str, k: int = 5) -> List[str]:
    """
    Search Amazon for products and return top-k product URLs using async approach.
    
    Args:
        keyword: Search keyword/phrase
        k: Number of results to return (default: 5)
        
    Returns:
        List of product URLs for top-k search results
    """
    # Use the sync version in a thread to avoid event loop conflicts
    
    def run_sync_search():
        return search_amazon_urls(keyword, k)
    
    try:
        # Run the sync search in a separate thread to avoid event loop conflicts
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(executor, run_sync_search)
            return result
    except Exception as e:
        print(f"Error in async search wrapper: {str(e)}")
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