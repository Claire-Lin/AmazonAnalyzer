"""
Singleton Playwright manager to handle browser instances safely
"""
import asyncio
import threading
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Playwright
from playwright.async_api import async_playwright as async_playwright_api


class PlaywrightManager:
    """Manages a singleton Playwright instance to avoid racing conditions"""
    
    _instance = None
    _lock = threading.Lock()
    _browser: Optional[Browser] = None
    _playwright: Optional[Playwright] = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_sync_browser(self, headless: bool = True) -> Browser:
        """Get or create a sync browser instance"""
        with self._lock:
            if self._browser is None or not self._browser.is_connected():
                if self._playwright is None:
                    self._playwright = sync_playwright().start()
                
                # Launch browser with anti-detection settings
                self._browser = self._playwright.chromium.launch(
                    headless=headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-gpu',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process'
                    ]
                )
            return self._browser
    
    def close(self):
        """Close the browser and playwright instance"""
        with self._lock:
            if self._browser:
                self._browser.close()
                self._browser = None
            if self._playwright:
                self._playwright.stop()
                self._playwright = None


# Global instance
playwright_manager = PlaywrightManager()