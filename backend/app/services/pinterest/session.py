import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

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
            
            pin_data = []  # Store pin data with URLs and metadata
            scroll_attempts = 0
            
            while len(pin_data) < num_images and scroll_attempts < scroll_attempts_limit:
                print(f"Collecting images: {len(pin_data)}/{num_images}")
                
                # Find pin wrappers in the feed
                pins = await self.page.query_selector_all("div[data-test-id='pinWrapper']")
                print(f"Found {len(pins)} pins in feed")
                
                # Extract URLs from pins in order, avoiding duplicates
                for pin in pins:
                    if len(pin_data) >= num_images:
                        break
                        
                    try:
                        image_element = await pin.query_selector("img")
                        if image_element:
                            # Get pin URL (Pinterest link)
                            pin_url = None
                            pin_link = await pin.query_selector("a[href*='/pin/']")
                            if pin_link:
                                href = await pin_link.get_attribute("href")
                                if href:
                                    pin_url = f"https://pinterest.com{href}" if href.startswith("/") else href
                            
                            # Title extraction: rich-pin-information only exists in pin detail view, not feed
                            # For now, titles will be null - can be populated later via pin page navigation if needed
                            title = None
                            
                            # Get description from image alt attribute
                            description = None
                            try:
                                img_element = await pin.query_selector("img")
                                if img_element:
                                    alt_text = await img_element.get_attribute("alt")
                                    if alt_text and alt_text.strip():
                                        # Clean up Pinterest's "This may contain: " prefix
                                        description = alt_text.strip()
                                        if description.startswith("This may contain: "):
                                            description = description.replace("This may contain: ", "", 1)
                            except Exception:
                                pass
                            
                            # Get image URL
                            image_url = None
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
                                            
                                if highest_res_url and highest_res_url.startswith("http"):
                                    image_url = highest_res_url
                            else:
                                # Fallback to src attribute
                                src = await image_element.get_attribute("src")
                                if src and src.startswith("http"):
                                    # Try to get higher resolution version
                                    if "236x" in src:
                                        src = src.replace("236x", "736x")
                                    elif "474x" in src:
                                        src = src.replace("474x", "736x")
                                    image_url = src
                            
                            # Only add if we have both URLs and haven't seen this image before
                            if image_url and pin_url:
                                # Check for duplicates
                                if not any(p['image_url'] == image_url for p in pin_data):
                                    pin_data.append({
                                        'image_url': image_url,
                                        'pin_url': pin_url,
                                        'title': title,  # From h1 on pin page
                                        'description': description,  # From alt text, cleaned
                                        'metadata': {
                                            'collected_at': datetime.now().isoformat()
                                        }
                                    })
                    except Exception as e:
                        print(f"Error processing pin: {e}")
                        continue
                
                if len(pin_data) >= num_images:
                    break
                    
                # Only scroll if we need more images
                print(f"Found {len(pin_data)} images so far, scrolling for more...")
                await self.page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(2)
                scroll_attempts += 1
                
        except Exception as e:
            print(f"Error during feed scraping: {e}")
            return []
        
        pin_data_list = pin_data[:num_images]  # Already a list, just slice
        print(f"\nTotal images found in feed: {len(pin_data_list)}")
        
        return pin_data_list
    
    async def enrich_with_titles(self, pin_data_list):
        """Navigate to each pin URL to extract h1 titles"""
        if not pin_data_list:
            return pin_data_list
            
        print(f"\nEnriching {len(pin_data_list)} pins with titles...")
        enriched_data = []
        
        for i, pin_data in enumerate(pin_data_list):
            try:
                print(f"Fetching title {i+1}/{len(pin_data_list)}...")
                
                # Navigate to pin page
                await self.page.goto(pin_data['pin_url'], timeout=15000)
                await asyncio.sleep(2)
                
                # Extract title from rich-pin-information
                title = None
                try:
                    title_element = await self.page.query_selector('div[data-test-id="rich-pin-information"] h1')
                    if title_element:
                        title = await title_element.text_content()
                        title = title.strip() if title else None
                        print(f"  Found: {title}")
                    else:
                        print("  No title found")
                except Exception:
                    print("  Title extraction failed")
                
                # Update pin data with title
                enriched_pin = pin_data.copy()
                enriched_pin['title'] = title
                enriched_data.append(enriched_pin)
                
            except Exception as e:
                print(f"  Error fetching title for pin {i+1}: {e}")
                # Keep original data without title
                enriched_data.append(pin_data)
                continue
        
        print(f"Title enrichment completed!")
        return enriched_data
    
    async def close(self):
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright') and self.playwright:
            await self.playwright.stop()
        print("Browser closed")