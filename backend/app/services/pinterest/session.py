import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from .pins import PinterestPins

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
        
        if not self.page:
            print("Browser not initialized. Call initialize_browser() first.")
            return False
            
        try:
            # Navigate to Pinterest login page
            print("Navigating to Pinterest login page...")
            await self.page.goto("https://www.pinterest.com/login/", timeout=30000)
            await asyncio.sleep(3)
            
            # Wait for login form to load
            await self.page.wait_for_selector('input[id="email"]', timeout=10000)
            
            # Fill in email
            print("Entering email...")
            await self.page.fill('input[id="email"]', self.username)
            await asyncio.sleep(1)
            
            # Fill in password
            print("Entering password...")
            await self.page.fill('input[id="password"]', self.password)
            await asyncio.sleep(1)
            
            # Click login button - try multiple selectors
            print("Clicking login button...")
            login_clicked = False
            
            # Try different possible selectors for the login button
            selectors_to_try = [
                'div:has-text("Log in")',  # Based on your inspection
                'button:has-text("Log in")',
                'div.B1n.tg7.fxm.dyH.xl9.stq:has-text("Log in")',  # Exact classes you found
                '[data-test-id="registerFormSubmitButton"]',
                'button[type="submit"]',
                'form button'
            ]
            
            for selector in selectors_to_try:
                try:
                    print(f"Trying selector: {selector}")
                    await self.page.click(selector, timeout=5000)
                    login_clicked = True
                    print(f"Successfully clicked login button with selector: {selector}")
                    break
                except:
                    continue
            
            if not login_clicked:
                print("Could not find login button with any selector")
                return False
            
            # Wait for navigation or error
            await asyncio.sleep(5)
            
            # Check if login was successful by looking for the home page elements
            current_url = self.page.url
            print(f"Current URL after login: {current_url}")
            
            # If we're redirected to home page, login was successful
            if "pinterest.com" in current_url and "/login" not in current_url:
                print("Login appears successful!")
                return True
            else:
                # Check for error messages
                error_elements = await self.page.query_selector_all('[data-test-id="error-message"]')
                if error_elements:
                    error_text = await error_elements[0].inner_text()
                    print(f"Login error: {error_text}")
                else:
                    print("Login may have failed - still on login page")
                return False
                
        except Exception as e:
            print(f"Error during login: {e}")
            return False
    
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
    
    async def scrape_feed(self, num_images=10):
        """
        Scrape Pinterest feed for pin data using PinterestPins service
        
        Args:
            num_images: Number of pins to scrape
            
        Returns:
            List of pin dictionaries with image_url, pin_url, title, description, metadata
        """
        if not self.page:
            print("Session not initialized. Call initialize() first.")
            return []
        
        # Navigate to Pinterest feed if needed
        current_url = self.page.url
        if "pinterest.com" in current_url and "/login" not in current_url:
            print("Already on Pinterest homepage, no need to navigate")
        else:
            print("Refreshing page and navigating to feed...")
            await self.page.goto("https://www.pinterest.com/", timeout=30000)
        
        await asyncio.sleep(3)
        
        # Wait for feed to load
        print("Waiting for feed to load...")
        try:
            await self.page.wait_for_selector('div[data-test-id="pinWrapper"]', timeout=15000)
        except:
            print("Feed elements not found immediately, continuing anyway...")
        
        # Use PinterestPins service to extract pin data
        pins_service = PinterestPins(self.page)
        return await pins_service.scrape_feed(num_images)
    
    async def enrich_with_titles(self, pin_data_list):
        """
        Enrich pin data with titles using PinterestPins service
        
        Args:
            pin_data_list: List of pin dictionaries from scrape_feed()
            
        Returns:
            List of pin dictionaries enriched with titles
        """
        if not self.page:
            print("Session not initialized. Call initialize() first.")
            return pin_data_list
        
        # Use PinterestPins service to enrich with titles
        pins_service = PinterestPins(self.page)
        return await pins_service.enrich_with_titles(pin_data_list)
    
    async def close(self):
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright') and self.playwright:
            await self.playwright.stop()
        print("Browser closed")