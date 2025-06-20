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
from playwright.sync_api import sync_playwright


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
    
    async def scrape_product(self, url: str) -> Dict[str, Any]:
        """
        Scrape product data from a given Amazon URL
        
        Args:
            url: Amazon product URL
            
        Returns:
            Dictionary containing product data
        """
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(
                headless=self.headless, 
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # Set a random user agent
            user_agent = self.user_agents[0]
            context = await browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US'
            )
            page: Page = await context.new_page()
            
            # Navigate with more lenient settings
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                # Wait a bit for dynamic content
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Navigation error: {e}")
                # Try without wait_until
                await page.goto(url, timeout=60000)
            
            # Check for and handle "Continue shopping" button
            try:
                continue_button = await page.query_selector('button:has-text("Continue shopping")')
                if continue_button:
                    print("Found 'Continue shopping' button, clicking it...")
                    await continue_button.click()
                    await page.wait_for_timeout(2000)
            except:
                pass
            
            try:
                await page.wait_for_selector('#productTitle', timeout=60000)
            except Exception as e:
                print(f"Product page did not load correctly: {e}")
                print(f"Current URL: {page.url}")
                # Take a screenshot for debugging
                await page.screenshot(path='debug_screenshot.png')
                print("Screenshot saved as debug_screenshot.png")
                await browser.close()
                return {'success': False, 'error': f'Page load timeout: {str(e)}'}
            
            self.data = await self._extract_product_data(page)
            await browser.close()
        return self.data


# Convenience functions for direct use
def scrape_amazon_product(url: str, headless: bool = True) -> Dict[str, Any]:
    """
    Scrape a single Amazon product
    
    Args:
        url: Amazon product URL
        headless: Whether to run browser in headless mode
        
    Returns:
        Dictionary containing product data
    """
    scraper = AmazonScraper(headless=headless)
    return asyncio.run(scraper.scrape_product(url))




# Example usage
if __name__ == "__main__":
    # Test with url
    url = "https://www.amazon.com/dp/B08SWDN5FS/ref=sspa_dk_detail_0?pd_rd_i=B08SWDN5FS&pd_rd_w=7ooYl&content-id=amzn1.sym.953c7d66-4120-4d22-a777-f19dbfa69309&pf_rd_p=953c7d66-4120-4d22-a777-f19dbfa69309&pf_rd_r=QB4D7523XBB2S2P11T3F&pd_rd_wg=eG4PU&pd_rd_r=92e66331-65b5-401b-99e2-b3cb92faefd6&s=toys-and-games&sp_csd=d2lkZ2V0TmFtZT1zcF9kZXRhaWwy&th=1"  
    print(f"Scraping product with url: {url}")
    result = scrape_amazon_product(url)
    print(json.dumps(result, indent=2))