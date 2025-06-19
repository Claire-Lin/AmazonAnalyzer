"""
Amazon Product Scraper using Playwright

This module provides functionality to scrape product information from Amazon
using Playwright for reliable browser automation.
"""

import asyncio
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from playwright.async_api import async_playwright, Page, Browser
from playwright.sync_api import sync_playwright, Page as SyncPage
try:
    from .playwright_manager import playwright_manager
except ImportError:
    from playwright_manager import playwright_manager


class AmazonScraper:
    """
    A scraper for Amazon product pages using Playwright
    """
    
    def __init__(self, headless: bool = True):
        """
        Initialize the Amazon scraper
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.data = {}  # Store scraped data for access across methods
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    def _get_url_from_asin(self, asin: str) -> str:
        """Convert ASIN to Amazon URL"""
        return f"https://www.amazon.com/dp/{asin}"
    
    def _is_asin(self, input_str: str) -> bool:
        """Check if input is an ASIN"""
        return bool(re.match(r'^[A-Z0-9]{10}$', input_str))
    
    async def _extract_product_data(self, page: Page) -> Dict[str, Any]:
        """Extract product data from the page"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'url': page.url,
            'title': None,
            'price': None,
            'currency': None,
            'brand': None,
            'asin': None,
            'description': None,
            'color': None,
            'spec': None,
            'reviews': [],
            'technical_details': {},
            'success': True
        }
        
        # Title
        try:
            title_element = await page.query_selector('#productTitle')
            if title_element:
                data['title'] = (await title_element.inner_text()).strip()
        except:
            pass
        
        # Price
        try:
            price_data = await self._extract_price(page)
            data['price'] = price_data.get('price')
            data['currency'] = price_data.get('currency')
        except:
            pass
        
        # Brand
        try:
            brand_element = await page.query_selector('#bylineInfo')
            if brand_element:
                brand_text = await brand_element.inner_text()
                data['brand'] = brand_text.replace('Visit the ', '').replace(' Store', '').strip()
        except:
            pass
        
        # ASIN
        try:
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', page.url)
            if asin_match:
                data['asin'] = asin_match.group(1)
        except:
            pass
        
        # Product Description
        try:
            desc_element = await page.query_selector('#feature-bullets')
            if desc_element:
                data['description'] = (await desc_element.inner_text()).strip()
        except:
            pass
        
        # Product Color/Variant
        try:
            data['color'] = await self._extract_color(page)
        except:
            pass
        
        # Product Specifications
        try:
            data['spec'] = await self._extract_specifications(page)
        except:
            pass
        
        # Product Reviews
        try:
            data['reviews'] = await self._extract_reviews(page, data['color'])
        except:
            pass
        
        return data
    
    async def _extract_price(self, page: Page) -> Dict[str, Any]:
        """Extract price information"""
        
        # First try to get the accurate price from .a-offscreen (Amazon's accessible price)
        try:
            offscreen_element = await page.query_selector('.a-price .a-offscreen')
            if offscreen_element:
                price_text = await offscreen_element.inner_text()
                
                # Extract currency
                currency = 'USD'
                if '€' in price_text:
                    currency = 'EUR'
                elif '£' in price_text:
                    currency = 'GBP'
                elif '¥' in price_text:
                    currency = 'JPY'
                
                # Extract price value - more comprehensive regex
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    return {
                        'price': float(price_match.group()),
                        'currency': currency
                    }
        except:
            pass
        
        # Fallback: Try to combine .a-price-whole and .a-price-fraction
        try:
            price_container = await page.query_selector('.a-price')
            if price_container:
                whole_element = await price_container.query_selector('.a-price-whole')
                fraction_element = await price_container.query_selector('.a-price-fraction')
                
                if whole_element and fraction_element:
                    whole_text = await whole_element.inner_text()
                    fraction_text = await fraction_element.inner_text()
                    
                    # Clean the whole part (remove newlines and dots)
                    whole_clean = re.search(r'\d+', whole_text)
                    fraction_clean = re.search(r'\d+', fraction_text)
                    
                    if whole_clean and fraction_clean:
                        complete_price = f"{whole_clean.group()}.{fraction_clean.group()}"
                        
                        # Extract currency from container
                        container_text = await price_container.inner_text()
                        currency = 'USD'
                        if '€' in container_text:
                            currency = 'EUR'
                        elif '£' in container_text:
                            currency = 'GBP'
                        elif '¥' in container_text:
                            currency = 'JPY'
                        
                        return {
                            'price': float(complete_price),
                            'currency': currency
                        }
        except:
            pass
        
        # Final fallback: Try other selectors
        price_selectors = [
            '.a-price.a-text-price.a-size-medium.apexPriceToPay',
            '.a-price-range',
            '#priceblock_dealprice',
            '#priceblock_ourprice',
            '.a-price.a-text-price.header-price'
        ]
        
        for selector in price_selectors:
            try:
                price_element = await page.query_selector(selector)
                if price_element:
                    price_text = await price_element.inner_text()
                    
                    # Extract currency
                    currency = 'USD'
                    if '€' in price_text:
                        currency = 'EUR'
                    elif '£' in price_text:
                        currency = 'GBP'
                    elif '¥' in price_text:
                        currency = 'JPY'
                    
                    # Extract price value
                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                    if price_match:
                        return {
                            'price': float(price_match.group()),
                            'currency': currency
                        }
            except:
                continue
        
        return {'price': None, 'currency': None}
    
    async def _extract_color(self, page: Page) -> str:
        """Extract product color/variant information"""
        
        # Look for the specific Amazon color/variant element (most accurate)
        try:
            # Primary selector for color name from Amazon's inline twister
            color_selectors = [
                '#inline-twister-expanded-dimension-text-color_name',
                '#inline-twister-expanded-dimension-text-style_name',
                '#inline-twister-expanded-dimension-text-size_name',
                '#inline-twister-expanded-dimension-text-pattern_name'
            ]
            
            for selector in color_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        color_text = (await element.inner_text()).strip()
                        if color_text and len(color_text) < 200:
                            return color_text
                except:
                    continue
        except:
            pass
        
        return None
    
    async def _extract_specifications(self, page: Page) -> str:
        """Extract product specifications from Product Information section"""
        spec_data = []
        
        # Primary method: Extract from Product Details sections (the structured table format)
        product_detail_selectors = [
            '#productDetails_detailBullets_sections1',  # Main product details section
            '#productDetails_techSpec_section_1',       # Technical specifications
            '#productDetails_feature_div',              # Feature details
            '#detailBullets_feature_div'                # Alternative detail bullets
        ]
        
        for section_selector in product_detail_selectors:
            try:
                section = await page.query_selector(section_selector)
                if section:
                    # Look for table rows within this section
                    rows = await section.query_selector_all('tr')
                    
                    for row in rows:
                        try:
                            # Try different cell selectors
                            label_selectors = ['th', 'td.a-span3', '.a-color-secondary']
                            value_selectors = ['td', 'td.a-span9', '.a-color-base']
                            
                            label_element = None
                            value_element = None
                            
                            # Find label element
                            for selector in label_selectors:
                                label_element = await row.query_selector(selector)
                                if label_element:
                                    break
                            
                            # Find value element
                            for selector in value_selectors:
                                elements = await row.query_selector_all(selector)
                                if len(elements) > 1:  # Get the second td element (value)
                                    value_element = elements[1]
                                    break
                                elif len(elements) == 1 and not label_element:
                                    # If only one element and no label found, skip
                                    continue
                                elif len(elements) == 1:
                                    value_element = elements[0]
                                    break
                            
                            if label_element and value_element:
                                label = (await label_element.inner_text()).strip()
                                value = (await value_element.inner_text()).strip()
                                
                                # Clean up the label (remove extra whitespace and special chars)
                                label = re.sub(r'\s+', ' ', label).strip()
                                value = re.sub(r'\s+', ' ', value).strip()
                                
                                # Filter out unwanted entries
                                if (label and value and 
                                    len(label) < 100 and len(value) < 500 and
                                    label.lower() not in ['', 'product information', 'additional information'] and
                                    not label.startswith('Customer') and
                                    not label.startswith('Date')):
                                    
                                    spec_data.append(f"{label}: {value}")
                        except:
                            continue
            except:
                continue
        
        # Secondary method: Look for specific detail bullet points
        try:
            # Look for the detail bullets structure
            detail_bullets = await page.query_selector_all('#detailBullets_feature_div ul li')
            
            for bullet in detail_bullets:
                try:
                    bullet_text = (await bullet.inner_text()).strip()
                    
                    # Look for key-value patterns in bullet points
                    if ':' in bullet_text and len(bullet_text) < 200:
                        # Split on first colon to get key-value pair
                        parts = bullet_text.split(':', 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            
                            if (key and value and 
                                not key.lower().startswith('customer') and
                                not key.lower().startswith('date')):
                                spec_data.append(f"{key}: {value}")
                except:
                    continue
        except:
            pass
        
        # Tertiary method: Extract from any remaining product details tables
        try:
            # Look for any table with product information
            tables = await page.query_selector_all('table')
            
            for table in tables:
                # Check if this table contains product information
                table_text = await table.inner_text()
                if any(keyword in table_text.lower() for keyword in ['dimensions', 'weight', 'asin', 'manufacturer', 'material']):
                    
                    rows = await table.query_selector_all('tr')
                    for row in rows:
                        try:
                            cells = await row.query_selector_all('td, th')
                            if len(cells) >= 2:
                                label = (await cells[0].inner_text()).strip()
                                value = (await cells[1].inner_text()).strip()
                                
                                if (label and value and 
                                    len(label) < 100 and len(value) < 200 and
                                    ':' not in label):  # Avoid duplicate formatting
                                    spec_data.append(f"{label}: {value}")
                        except:
                            continue
        except:
            pass
        
        # Clean and format the specifications
        if spec_data:
            # Remove duplicates while preserving order
            unique_specs = []
            seen = set()
            
            for spec in spec_data:
                # Normalize the spec for duplicate detection
                normalized = spec.lower().strip()
                if normalized not in seen and len(spec.strip()) > 5:
                    unique_specs.append(spec)
                    seen.add(normalized)
            
            # Return formatted specifications
            if unique_specs:
                return '\n'.join(unique_specs[:20])  # Limit to 20 specifications
        
        return None
    
    async def _extract_reviews(self, page: Page, product_color: str) -> List[str]:
        """Extract product reviews that match the current color/variant"""
        reviews = []
        
        # Sections to search for reviews
        review_selectors = [
            '.cr-widget-FocalReviews',
            '.cr-widget-DesktopGlobalReviews'
        ]
        
        for section_selector in review_selectors:
            try:
                section = await page.query_selector(section_selector)
                if not section:
                    continue
                
                # Find individual review containers within the section
                review_containers = await section.query_selector_all('[data-hook="review"]')
                
                for review_container in review_containers:
                    try:
                        # Extract the review text
                        review_text_element = await review_container.query_selector('[data-hook="review-body"] span')
                        if not review_text_element:
                            continue
                        
                        review_text = (await review_text_element.inner_text()).strip()
                        
                        # If no color specified, include all reviews
                        if not product_color:
                            if review_text and len(review_text) > 10:
                                reviews.append(review_text)
                            continue
                        
                        # Check the color information in the review's a-color-secondary element
                        color_match = False
                        try:
                            color_secondary_elements = await review_container.query_selector_all('.a-color-secondary')
                            for color_element in color_secondary_elements:
                                color_element_text = (await color_element.inner_text()).strip()
                                
                                # Check if this element contains color/variant information
                                if any(keyword in color_element_text.lower() for keyword in ['color:', 'style:', 'size:', 'pattern:']):
                                    # Extract the value part after the colon
                                    if ':' in color_element_text:
                                        color_value = color_element_text.split(':', 1)[1].strip()
                                        # Check if the color value matches our product color
                                        if product_color.lower() in color_value.lower() or color_value.lower() in product_color.lower():
                                            color_match = True
                                            break
                        except:
                            pass
                        
                        # If we found a color match in the a-color-secondary elements, include the review
                        if color_match and review_text and len(review_text) > 10:
                            reviews.append(review_text)
                        # If no a-color-secondary color info found, fall back to checking format-strip
                        elif not color_match:
                            try:
                                variant_element = await review_container.query_selector('[data-hook="format-strip"]')
                                if variant_element:
                                    variant_text = (await variant_element.inner_text()).strip().lower()
                                    product_color_lower = product_color.lower()
                                    
                                    # Check if variant info mentions the color
                                    if (product_color_lower in variant_text and 
                                        review_text and len(review_text) > 10):
                                        reviews.append(review_text)
                            except:
                                pass
                            
                    except:
                        continue
                        
            except:
                continue
        
        # Remove duplicates while preserving order
        unique_reviews = []
        seen = set()
        for review in reviews:
            # Use first 100 characters as unique identifier
            review_key = review[:100].lower().strip()
            if review_key not in seen:
                unique_reviews.append(review)
                seen.add(review_key)
        
        # Limit to 10 reviews to avoid too much data
        return unique_reviews[:10]
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources"""
        pass
    
    async def scrape_product_async(self, url_or_asin: str) -> Dict[str, Any]:
        """
        Scrape a single Amazon product asynchronously
        
        Args:
            url_or_asin: Amazon product URL or ASIN
            
        Returns:
            Dictionary containing product data
        """
        # Convert ASIN to URL if necessary
        if self._is_asin(url_or_asin):
            url = self._get_url_from_asin(url_or_asin)
        else:
            url = url_or_asin
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                user_agent=self.user_agents[0],
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to product page
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                # Wait for content to load
                await page.wait_for_selector('#productTitle', timeout=10000)
                
                # Extract data
                product_data = await self._extract_product_data(page)
                
                # Store data in self.data for access across methods
                self.data = product_data
                
                return product_data
                
            except Exception as e:
                return {
                    'timestamp': datetime.now().isoformat(),
                    'url': url,
                    'title': None,
                    'price': None,
                    'currency': None,
                    'brand': None,
                    'asin': None,
                    'description': None,
                    'color': None,
                    'spec': None,
                    'reviews': [],
                    'success': False
                }
            finally:
                try:
                    await context.close()
                except:
                    pass
                try:
                    await browser.close()
                except:
                    pass
    
    def _extract_product_data_sync(self, page: SyncPage) -> Dict[str, Any]:
        """Extract product data from the page (synchronous version)"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'url': page.url,
            'title': None,
            'price': None,
            'currency': None,
            'brand': None,
            'asin': None,
            'description': None,
            'color': None,
            'spec': None,
            'reviews': [],
            'success': False
        }
        
        try:
            # Extract title
            title_element = page.query_selector('#productTitle')
            if not title_element:
                # Try alternative selectors
                title_element = page.query_selector('h1 span.a-size-large')
            if not title_element:
                title_element = page.query_selector('h1')
            
            if title_element:
                data['title'] = title_element.inner_text().strip()
            
            # Extract ASIN
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', page.url)
            if asin_match:
                data['asin'] = asin_match.group(1)
            
            # Extract price
            price_selectors = [
                'span.a-price-whole',
                'span#priceblock_dealprice',
                'span#priceblock_ourprice',
                'span.a-price.a-text-price.a-size-medium.apexPriceToPay',
                'span.a-price-range'
            ]
            
            for selector in price_selectors:
                price_element = page.query_selector(selector)
                if price_element:
                    price_text = price_element.inner_text()
                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                    if price_match:
                        data['price'] = float(price_match.group())
                        data['currency'] = 'USD'
                        break
            
            # Extract brand
            brand_selectors = [
                'a#bylineInfo',
                'span.by-line',
                'div.a-section.a-spacing-none span.a-size-base'
            ]
            
            for selector in brand_selectors:
                brand_element = page.query_selector(selector)
                if brand_element:
                    brand_text = brand_element.inner_text().strip()
                    brand_text = brand_text.replace('Visit the ', '').replace(' Store', '')
                    if brand_text and len(brand_text) < 100:
                        data['brand'] = brand_text
                        break
            
            # Extract color/variant
            color_selectors = [
                '#inline-twister-expanded-dimension-text-color_name',
                '#inline-twister-expanded-dimension-text-style_name'
            ]
            
            for selector in color_selectors:
                color_element = page.query_selector(selector)
                if color_element:
                    data['color'] = color_element.inner_text().strip()
                    break
            
            # Extract description
            feature_div = page.query_selector('#feature-bullets')
            if feature_div:
                bullets = feature_div.query_selector_all('span.a-list-item')
                descriptions = []
                for bullet in bullets[:5]:  # Limit to 5 bullet points
                    text = bullet.inner_text().strip()
                    if text and not text.startswith('Make sure'):
                        descriptions.append(text)
                data['description'] = ' '.join(descriptions)
            
            # Extract specifications
            spec_sections = page.query_selector_all('#productDetails_detailBullets_sections1 tr, #productDetails_techSpec_section_1 tr')
            specs = []
            for row in spec_sections[:10]:  # Limit to 10 specs
                cells = row.query_selector_all('td')
                if len(cells) >= 2:
                    label = cells[0].inner_text().strip()
                    value = cells[1].inner_text().strip()
                    specs.append(f"{label}: {value}")
            data['spec'] = ' | '.join(specs) if specs else None
            
            # Extract reviews
            review_containers = page.query_selector_all('[data-hook="review"]')
            reviews = []
            for container in review_containers[:5]:  # Limit to 5 reviews
                review_text_elem = container.query_selector('[data-hook="review-body"]')
                if review_text_elem:
                    review_text = review_text_elem.inner_text().strip()
                    if review_text:
                        reviews.append(review_text)
            data['reviews'] = reviews
            
            data['success'] = True
            
        except Exception as e:
            print(f"Error extracting data: {e}")
            data['error'] = str(e)
        
        return data
    
    def scrape_product(self, url_or_asin: str) -> Dict[str, Any]:
        """
        DEPRECATED: Use scrape_product_async instead.
        This sync method is kept for backwards compatibility but may cause threading issues.
        """
        print("WARNING: scrape_product is deprecated. Use scrape_product_async instead.")
        return {
            'title': None,
            'price': None,
            'currency': None,
            'brand': None,
            'asin': None,
            'description': None,
            'color': None,
            'spec': None,
            'reviews': [],
            'technical_details': {},
            'success': False,
            'error': 'Sync method deprecated - use async version'
        }
    
    async def scrape_search_results_async(self, keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape Amazon search results asynchronously
        
        Args:
            keyword: Search keyword
            max_results: Maximum number of results to return
            
        Returns:
            List of product data dictionaries
        """
        search_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
        results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                user_agent=self.user_agents[0],
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
                
                # Wait for search results
                await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=10000)
                
                # Extract search results
                items = await page.query_selector_all('[data-component-type="s-search-result"]')
                
                for item in items[:max_results]:
                    try:
                        # Extract basic info from search result
                        result = {}
                        
                        # Title and URL
                        title_element = await item.query_selector('h2 a')
                        if title_element:
                            result['title'] = (await title_element.inner_text()).strip()
                            href = await title_element.get_attribute('href')
                            if href:
                                result['url'] = f"https://www.amazon.com{href}" if href.startswith('/') else href
                                # Extract ASIN from URL
                                asin_match = re.search(r'/dp/([A-Z0-9]{10})', href)
                                if asin_match:
                                    result['asin'] = asin_match.group(1)
                        
                        # Price
                        price_element = await item.query_selector('.a-price-whole')
                        if price_element:
                            price_text = await price_element.inner_text()
                            result['price'] = price_text.strip()
                        
                        # Rating
                        rating_element = await item.query_selector('.a-icon-alt')
                        if rating_element:
                            rating_text = await rating_element.inner_text()
                            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                            if rating_match:
                                result['rating'] = float(rating_match.group(1))
                        
                        # Review count
                        review_element = await item.query_selector('.s-link-style .s-underline-text')
                        if review_element:
                            review_text = await review_element.inner_text()
                            result['review_count'] = review_text.strip()
                        
                        results.append(result)
                    except:
                        continue
                
                # Store search results in self.data for access across methods
                self.data = {'search_results': results, 'search_keyword': keyword}
                
                return results
                
            except Exception as e:
                return [{
                    'success': False,
                    'error': str(e),
                    'search_url': search_url
                }]
            finally:
                try:
                    await context.close()
                except:
                    pass
                try:
                    await browser.close()
                except:
                    pass
    
    def scrape_search_results(self, keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Use scrape_search_results_async instead.
        This sync method is kept for backwards compatibility but may cause threading issues.
        """
        print("WARNING: scrape_search_results is deprecated. Use scrape_search_results_async instead.")
        return []
    
    def get_stored_data(self) -> Dict[str, Any]:
        """
        Get the currently stored data
        
        Returns:
            Dictionary containing stored data
        """
        return self.data
    
    def get_product_title(self) -> Optional[str]:
        """
        Get the title from stored product data
        
        Returns:
            Product title or None if not available
        """
        return self.data.get('title')
    
    def get_product_price(self) -> Optional[float]:
        """
        Get the price from stored product data
        
        Returns:
            Product price or None if not available
        """
        return self.data.get('price')
    
    def clear_data(self) -> None:
        """
        Clear the stored data
        """
        self.data = {}


# Convenience functions for direct use
def scrape_amazon_product(url_or_asin: str, headless: bool = True) -> Dict[str, Any]:
    """
    Scrape a single Amazon product
    
    Args:
        url_or_asin: Amazon product URL or ASIN
        headless: Whether to run browser in headless mode
        
    Returns:
        Dictionary containing product data
    """
    scraper = AmazonScraper(headless=headless)
    return scraper.scrape_product(url_or_asin)


def search_amazon_products(keyword: str, max_results: int = 10, headless: bool = True) -> List[Dict[str, Any]]:
    """
    Search Amazon products
    
    Args:
        keyword: Search keyword
        max_results: Maximum number of results to return
        headless: Whether to run browser in headless mode
        
    Returns:
        List of product data dictionaries
    """
    scraper = AmazonScraper(headless=headless)
    return scraper.scrape_search_results(keyword, max_results)


# Example usage
if __name__ == "__main__":
    # Test with ASIN
    asin = "B08N5WRWNW"  # Echo Dot
    print(f"Scraping product with ASIN: {asin}")
    result = scrape_amazon_product(asin)
    print(json.dumps(result, indent=2))
    
    # Test with search
    print("\nSearching for 'wireless headphones'")
    search_results = search_amazon_products("wireless headphones", max_results=5)
    for i, product in enumerate(search_results, 1):
        print(f"\nProduct {i}:")
        print(f"Title: {product.get('title', 'N/A')}")
        print(f"Price: {product.get('price', 'N/A')}")
        print(f"Rating: {product.get('rating', 'N/A')}")