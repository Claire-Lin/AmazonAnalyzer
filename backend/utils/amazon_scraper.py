"""
Amazon Product Scraper

This module provides a class to scrape product information from Amazon product pages.
It now uses requests instead of Playwright to avoid bot detection and async issues.
"""

import requests
import re
import json
import time
import random
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor


class AmazonScraper:
    """
    A scraper for Amazon product pages using requests
    """
    
    def __init__(self, headless: bool = True):
        """
        Initialize the Amazon scraper
        
        Args:
            headless: Kept for compatibility, not used in requests implementation
        """
        self.headless = headless
        self.session = requests.Session()
        
        # Set up headers to avoid bot detection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
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
        }
        self.session.headers.update(headers)
    
    def _get_url_from_asin(self, asin: str) -> str:
        """Convert ASIN to Amazon URL"""
        return f"https://www.amazon.com/dp/{asin}"
    
    def _is_asin(self, input_str: str) -> bool:
        """Check if input is an ASIN"""
        return bool(re.match(r'^[A-Z0-9]{10}$', input_str))
    
    def scrape_product(self, url_or_asin: str) -> Dict[str, Any]:
        """
        Scrape product data from Amazon (synchronous version)
        
        Args:
            url_or_asin: Amazon URL or ASIN
            
        Returns:
            Dictionary containing product data
        """
        # Convert ASIN to URL if needed
        if self._is_asin(url_or_asin):
            url = self._get_url_from_asin(url_or_asin)
            asin = url_or_asin
        else:
            url = url_or_asin
            # Extract ASIN from URL
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
            asin = asin_match.group(1) if asin_match else None
            # Clean URL if ASIN found
            if asin:
                url = f"https://www.amazon.com/dp/{asin}"
        
        try:
            # Add random delay
            delay = random.uniform(1, 3)
            print(f"Waiting {delay:.1f} seconds before scraping...")
            time.sleep(delay)
            
            print(f"Scraping Amazon product: {url}")
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check for bot detection
                page_text = soup.get_text().lower()
                if any(word in page_text for word in ['robot', 'captcha', 'sorry, we just need to make sure']):
                    print(f"❌ Bot detection triggered for {url}")
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'url': url,
                        'asin': asin,
                        'error': 'Bot detection triggered',
                        'success': False
                    }
                
                # Extract product data
                product_data = {
                    'timestamp': datetime.now().isoformat(),
                    'url': url,
                    'asin': asin,
                    'success': True
                }
                
                # Title
                title_element = soup.find('span', {'id': 'productTitle'})
                if title_element:
                    product_data['title'] = title_element.get_text().strip()
                
                # Price
                price_selectors = [
                    'span.a-price-whole',
                    'span.a-price.a-text-price.a-size-medium.apexPriceToPay',
                    'span.a-price-range',
                    'span.a-price.a-text-price',
                    'span.a-color-price'
                ]
                for selector in price_selectors:
                    price_element = soup.select_one(selector)
                    if price_element:
                        price_text = price_element.get_text().strip()
                        # Extract numeric price
                        price_match = re.search(r'[\$£€]?([\d,]+\.?\d*)', price_text)
                        if price_match:
                            product_data['price'] = price_match.group(1).replace(',', '')
                            break
                
                # Brand
                brand_selectors = [
                    'a#bylineInfo',
                    'span.a-size-base.po-break-word',
                    'div.a-section.a-spacing-none span.a-size-base'
                ]
                for selector in brand_selectors:
                    brand_element = soup.select_one(selector)
                    if brand_element:
                        brand_text = brand_element.get_text().strip()
                        # Clean brand text
                        brand_text = brand_text.replace('Brand:', '').replace('Visit the', '').replace('Store', '').strip()
                        if brand_text:
                            product_data['brand'] = brand_text
                            break
                
                # Rating
                rating_element = soup.find('span', {'class': 'a-icon-alt'})
                if rating_element:
                    rating_text = rating_element.get_text()
                    rating_match = re.search(r'([\d.]+) out of', rating_text)
                    if rating_match:
                        product_data['rating'] = float(rating_match.group(1))
                
                # Review count
                review_element = soup.find('span', {'id': 'acrCustomerReviewText'})
                if review_element:
                    review_text = review_element.get_text()
                    review_match = re.search(r'([\d,]+)', review_text)
                    if review_match:
                        product_data['review_count'] = int(review_match.group(1).replace(',', ''))
                
                # Features/bullets
                feature_elements = soup.find_all('span', {'class': 'a-list-item'})
                if feature_elements:
                    features = []
                    for element in feature_elements[:5]:  # First 5 features
                        text = element.get_text().strip()
                        if text and len(text) > 10:  # Filter out short/empty items
                            features.append(text)
                    if features:
                        product_data['features'] = features
                
                # Category
                breadcrumb = soup.find('div', {'id': 'wayfinding-breadcrumbs_feature_div'})
                if breadcrumb:
                    links = breadcrumb.find_all('a')
                    if links:
                        categories = [link.get_text().strip() for link in links]
                        product_data['category'] = ' > '.join(categories)
                
                # Check if we got minimal data
                if not product_data.get('title'):
                    print(f"⚠️ Could not extract product title from {url}")
                    product_data['success'] = False
                    product_data['error'] = 'Could not extract product information'
                
                return product_data
                
            elif response.status_code == 404:
                return {
                    'timestamp': datetime.now().isoformat(),
                    'url': url,
                    'asin': asin,
                    'error': 'Product not found (404)',
                    'success': False
                }
            elif response.status_code == 503:
                return {
                    'timestamp': datetime.now().isoformat(),
                    'url': url,
                    'asin': asin,
                    'error': 'Service unavailable (503) - Likely rate limited',
                    'success': False
                }
            else:
                return {
                    'timestamp': datetime.now().isoformat(),
                    'url': url,
                    'asin': asin,
                    'error': f'HTTP error {response.status_code}',
                    'success': False
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'asin': asin,
                'error': f'Request failed: {str(e)}',
                'success': False
            }
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'asin': asin,
                'error': f'Unexpected error: {str(e)}',
                'success': False
            }
    
    async def scrape_product_async(self, url_or_asin: str) -> Dict[str, Any]:
        """
        Async wrapper for scrape_product
        
        Args:
            url_or_asin: Amazon URL or ASIN
            
        Returns:
            Dictionary containing product data
        """
        # Run the sync version in a thread pool
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(executor, self.scrape_product, url_or_asin)
            return result


# For testing
if __name__ == "__main__":
    scraper = AmazonScraper()
    
    # Test with an ASIN
    test_asin = "B0B1VQ1ZQY"
    print(f"Testing scraper with ASIN: {test_asin}")
    result = scraper.scrape_product(test_asin)
    print(json.dumps(result, indent=2))