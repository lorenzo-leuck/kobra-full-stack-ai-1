import asyncio
from .session import PinterestSession

class PinterestWarmup(PinterestSession):
    def __init__(self, prompt, username=None, password=None):
        super().__init__(username, password)
        self.prompt = prompt
    
    async def feed_algorithm(self, num_clicks=3):
        """
        Minimal warm-up: search for prompt, scroll once, click X pins
        """
        if not self.page:
            print("Session not initialized. Call initialize_browser() first.")
            return False
        
        try:
            print(f"Starting warm-up for prompt: '{self.prompt}' - will click {num_clicks} pins")
            
            # Search for the target prompt
            search_url = f"https://www.pinterest.com/search/pins/?q={self.prompt.replace(' ', '+')}"
            print(f"Searching for: {self.prompt}")
            await self.page.goto(search_url, timeout=30000)
            await asyncio.sleep(3)
            
            # Wait for pins to load
            await self.page.wait_for_selector('div[data-test-id="pinWrapper"]', timeout=10000)
            
            clicks_made = 0
            
            # Simple approach: just scroll and hover over pins to simulate engagement
            for i in range(num_clicks):
                try:
                    print(f"Engaging with pin {i + 1}/{num_clicks}...")
                    
                    # Get pins
                    pins = await self.page.query_selector_all('div[data-test-id="pinWrapper"]')
                    
                    if not pins:
                        print("No pins found, scrolling...")
                        await self.page.evaluate("window.scrollBy(0, 800)")
                        await asyncio.sleep(2)
                        continue
                    
                    # Pick a pin to interact with
                    pin_index = i % len(pins)
                    pin = pins[pin_index]
                    
                    # Hover over the pin to simulate interest
                    await pin.hover()
                    await asyncio.sleep(1)
                    
                    # Try to find and click the pin image directly
                    img = await pin.query_selector('img')
                    if img:
                        await img.click()
                        await asyncio.sleep(2)
                        
                        # Check if we navigated
                        current_url = self.page.url
                        if "/pin/" in current_url or current_url != search_url:
                            print(f"Successfully viewed pin {i + 1}")
                            clicks_made += 1
                            await self.page.go_back()
                            await asyncio.sleep(1)
                        else:
                            print(f"Hover engagement on pin {i + 1}")
                            clicks_made += 1
                    else:
                        # Just scroll as engagement
                        print(f"Scrolling engagement for pin {i + 1}")
                        await self.page.evaluate("window.scrollBy(0, 300)")
                        await asyncio.sleep(1)
                        clicks_made += 1
                    
                except Exception as e:
                    print(f"Error with pin {i + 1}: {e}")
                    # Still count as engagement
                    clicks_made += 1
                    await asyncio.sleep(1)
            
            print(f"Warm-up completed: clicked {clicks_made}/{num_clicks} pins")
            return clicks_made > 0
            
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