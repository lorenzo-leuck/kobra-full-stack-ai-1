import asyncio
from .session import PinterestSession

class PinterestWarmup(PinterestSession):
    def __init__(self, prompt, username=None, password=None):
        super().__init__(username, password)
        self.prompt = prompt
    
    async def feed_algorithm(self):
        """
        Minimal warm-up: search for prompt, scroll once, click 3 pins
        """
        if not self.page:
            print("Session not initialized. Call initialize_browser() first.")
            return False
        
        try:
            print(f"Starting warm-up for prompt: '{self.prompt}'")
            
            # Search for the target prompt
            search_url = f"https://www.pinterest.com/search/pins/?q={self.prompt.replace(' ', '+')}"
            print(f"Searching for: {self.prompt}")
            await self.page.goto(search_url, timeout=30000)
            await asyncio.sleep(3)
            
            # Wait for pins to load
            await self.page.wait_for_selector('div[data-test-id="pinWrapper"]', timeout=10000)
            
            # Scroll once to load more pins
            print("Scrolling to load more pins...")
            await self.page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(2)
            
            # Find pins and click on 3 of them
            pins = await self.page.query_selector_all('div[data-test-id="pinWrapper"]')
            print(f"Found {len(pins)} pins")
            
            clicks_made = 0
            for i, pin in enumerate(pins[:5]):  # Try first 5 pins
                if clicks_made >= 3:
                    break
                    
                try:
                    print(f"Clicking pin {clicks_made + 1}...")
                    await pin.click()
                    await asyncio.sleep(2)  # View the pin for 2 seconds
                    
                    # Go back to search results
                    await self.page.go_back()
                    await asyncio.sleep(1)
                    clicks_made += 1
                    
                except Exception as e:
                    print(f"Error clicking pin {i}: {e}")
                    continue
            
            print(f"Warm-up completed: clicked {clicks_made} pins")
            return True
            
        except Exception as e:
            print(f"Error during warm-up: {e}")
            return False
    
    async def scrape_after_warmup(self, num_images=10, download=True, output_name=None):
        """
        Refresh page and scrape feed after warm-up
        """
        try:
            print("Refreshing page and navigating to feed...")
            await self.page.goto("https://www.pinterest.com/", timeout=30000)
            await asyncio.sleep(3)
            
            # Use the parent class method to scrape feed
            folder_name = output_name or f"warmup_{self.prompt.replace(' ', '_')}"
            return await self.scrape_feed(
                num_images=num_images,
                download=download,
                output_name=folder_name
            )
            
        except Exception as e:
            print(f"Error during post-warmup scraping: {e}")
            return []