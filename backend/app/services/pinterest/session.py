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
            # Check if we're already on Pinterest homepage
            current_url = self.page.url
            if "pinterest.com" in current_url and "/login" not in current_url:
                print("Already on Pinterest homepage, no need to navigate")
            else:
                print("Navigating to Pinterest feed...")
                await self.page.goto("https://www.pinterest.com/", timeout=30000)
            
            await asyncio.sleep(3)
            
            # Wait for the feed to load
            print("Waiting for feed to load...")
            try:
                await self.page.wait_for_selector('div[data-test-id="pinWrapper"]', timeout=15000)
            except:
                print("Feed elements not found immediately, continuing anyway...")
            
            img_urls = []  # Use list to preserve order
            scroll_attempts = 0
            
            while len(img_urls) < num_images and scroll_attempts < scroll_attempts_limit:
                print(f"Collecting images: {len(img_urls)}/{num_images}")
                
                # Find pin wrappers in the feed
                pins = await self.page.query_selector_all("div[data-test-id='pinWrapper']")
                print(f"Found {len(pins)} pins in feed")
                
                # Extract URLs from pins in order, avoiding duplicates
                for pin in pins:
                    if len(img_urls) >= num_images:
                        break
                        
                    try:
                        image_element = await pin.query_selector("img")
                        if image_element:
                            # Try to get srcset first for higher quality
                            srcset = await image_element.get_attribute("srcset")
                            if srcset:
                                highest_res_url = None
                                highest_res = 0
                                for part in srcset.split(","):
                                    part = part.strip()
                                    if not part:
                                        continue
                                    parts = part.split(" ")
                                    if len(parts) >= 2:
                                        url = parts[0]
                                        try:
                                            res = int(parts[1].replace("x", ""))
                                            if res > highest_res:
                                                highest_res = res
                                                highest_res_url = url
                                        except ValueError:
                                            pass
                                            
                                if highest_res_url and highest_res_url.startswith("http") and highest_res_url not in img_urls:
                                    img_urls.append(highest_res_url)
                            else:
                                # Fallback to src attribute
                                src = await image_element.get_attribute("src")
                                if src and src.startswith("http"):
                                    # Try to get higher resolution version
                                    if "236x" in src:
                                        src = src.replace("236x", "736x")
                                    elif "474x" in src:
                                        src = src.replace("474x", "736x")
                                    if src not in img_urls:
                                        img_urls.append(src)
                    except Exception as e:
                        print(f"Error processing pin: {e}")
                        continue
                
                if len(img_urls) >= num_images:
                    break
                    
                # Only scroll if we need more images
                print(f"Found {len(img_urls)} images so far, scrolling for more...")
                await self.page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(2)
                scroll_attempts += 1
                
        except Exception as e:
            print(f"Error during feed scraping: {e}")
            return []
        
        img_urls_list = img_urls[:num_images]  # Already a list, just slice
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