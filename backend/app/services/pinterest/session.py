import os
import asyncio
from playwright.async_api import async_playwright
from .scrapper import download_images, extract_image_urls_from_pins

class PinterestSession:
    def __init__(self, username=None, password=None):
        self.username = username or os.getenv("PINTEREST_USERNAME")
        self.password = password or os.getenv("PINTEREST_PASSWORD")
        self.browser = None
        self.context = None
        self.page = None
    
    async def login(self):
        print(f"Logging in with username: {self.username}")
        print(f"Password: {'*' * len(self.password) if self.password else 'Not provided'}")
        
        # This is just a placeholder for now
        # The actual login implementation will be added later
        return True
    
    async def initialize_browser(self, headless=True):
        """
        Initialize browser session as async context manager
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        self.page = await self.context.new_page()
        
        print("Browser initialized")
        return self
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def scrape_feed(self, num_images=10, scroll_attempts_limit=10, download=False, output_name="feed_images"):
        """
        Scrape images from the user's Pinterest feed after login.
        
        Args:
            num_images: Number of images to scrape
            scroll_attempts_limit: Maximum scroll attempts
            download: Whether to download images locally
            output_name: Name for the output folder
        
        Returns:
            List of image URLs
        """
        if not self.page:
            print("Session not initialized. Call initialize() first.")
            return []
        
        try:
            print("Navigating to Pinterest feed...")
            await self.page.goto("https://www.pinterest.com/", timeout=30000)
            await asyncio.sleep(3)
            
            img_urls = set()
            scroll_attempts = 0
            
            while len(img_urls) < num_images and scroll_attempts < scroll_attempts_limit:
                print(f"Scroll attempt {scroll_attempts+1}/{scroll_attempts_limit}")
                
                # Find pin wrappers in the feed
                pins = await self.page.query_selector_all("div[data-test-id='pinWrapper']")
                print(f"Found {len(pins)} pins in feed")
                
                # Use helper function to extract URLs
                new_urls = await extract_image_urls_from_pins(pins)
                img_urls.update(new_urls)
                
                if len(img_urls) >= num_images:
                    break
                    
                # Scroll down to load more pins
                await self.page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(2)
                scroll_attempts += 1
                print(f"Found {len(img_urls)} images so far")
                
        except Exception as e:
            print(f"Error during feed scraping: {e}")
            return []
        
        img_urls_list = list(img_urls)[:num_images]
        print(f"\nTotal images found in feed: {len(img_urls_list)}")
        
        if download and img_urls_list:
            print("Downloading images...")
            download_images(img_urls_list, output_name)
            print("Download completed.")
        
        return img_urls_list
    
    async def close(self):
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright') and self.playwright:
            await self.playwright.stop()
        print("Browser closed")