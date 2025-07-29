import asyncio
from .session import PinterestSession

class PinterestWarmup(PinterestSession):
    def __init__(self, prompt: str, username: str = None, password: str = None, log_callback=None, progress_callback=None):
        super().__init__(username, password)
        self.prompt = prompt
        self.log_callback = log_callback
        self.progress_callback = progress_callback
    
    async def feed_algorithm(self, num_clicks=None):
        """
        """
        if not self.page:
            if self.log_callback:
                self.log_callback("Session not initialized. Call initialize_browser() first.")
            else:
                print("Session not initialized. Call initialize_browser() first.")
            return False
        
        # Always do exactly 5 warmup clicks
        warmup_clicks = 6
        
        try:
            self.log_callback(f"Starting warm-up for prompt: '{self.prompt}' - will click {warmup_clicks} pins")
            
            # Search for the target prompt
            search_url = f"https://www.pinterest.com/search/pins/?q={self.prompt.replace(' ', '+')}"
            self.log_callback(f"Searching for: {self.prompt}")
            await self.page.goto(search_url, timeout=30000)
            await asyncio.sleep(3)
            
            # Wait for pins to load
            await self.page.wait_for_selector('div[data-test-id="pinWrapper"]', timeout=10000)
            
            clicks_made = 0
            
            # Fixed 5 pin interactions
            for i in range(warmup_clicks):
                try:
                    self.log_callback(f"Engaging with pin {i + 1}/{warmup_clicks}...")
                    
                    # Update progress: 10% + (i/warmup_clicks * 23%) = 10% to 33%
                    progress = 10.0 + (i / warmup_clicks) * 23.0
                    if self.progress_callback:
                        self.progress_callback(progress)
                    else:
                        self.log_callback("⚠️ No progress callback available")
                    
                    # Get pins
                    pins = await self.page.query_selector_all('div[data-test-id="pinWrapper"]')
                    
                    if not pins:
                        self.log_callback("No pins found, scrolling...")
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
                        
                        # Check if we navigated to pin page
                        current_url = self.page.url
                        if "/pin/" in current_url:
                            print(f"Successfully viewed pin {i + 1}, now reacting...")
                            
                            # Try to click the heart/react button
                            try:
                                # Try multiple selectors for the react button
                                react_selectors = [
                                    'button[data-test-id="react-button"]',
                                    'button[aria-label="React"]',
                                    'button.yfm.adn.obZ.lnZ.wsz'
                                ]
                                
                                reacted = False
                                for selector in react_selectors:
                                    try:
                                        await self.page.click(selector, timeout=2000)
                                        self.log_callback(f"❤️ Reacted to pin {i + 1}")
                                        reacted = True
                                        break
                                    except:
                                        continue
                                
                                if not reacted:
                                    self.log_callback(f"Couldn't find react button for pin {i + 1}")
                                
                                await asyncio.sleep(1)
                                
                                # Try to save the pin
                                try:
                                    # Try multiple selectors for the save button
                                    save_selectors = [
                                        'div.xuA div.B1n.tg7.IZT.fxm.dyH.wm0:has-text("Save")',  # CSS selector with text
                                        'div.xuA button:has-text("Save")',  # Button with Save text
                                        'div:has(div.B1n.tg7.IZT.fxm.dyH.wm0:text("Save"))',  # Parent div containing Save
                                        'button:has(div:text("Save"))',  # Button containing div with Save text
                                    ]
                                    
                                    saved = False
                                    for selector in save_selectors:
                                        try:
                                            await self.page.click(selector, timeout=2000)
                                            self.log_callback(f"💾 Saved pin {i + 1}")
                                            saved = True
                                            break
                                        except:
                                            continue
                                    
                                    # If CSS selectors don't work, try XPath approach
                                    if not saved:
                                        try:
                                            # Look for Save button using text content
                                            save_elements = await self.page.query_selector_all('div.B1n.tg7.IZT.fxm.dyH.wm0')
                                            for element in save_elements:
                                                text_content = await element.text_content()
                                                if text_content and 'Save' in text_content:
                                                    # Click the parent button/div that contains this Save div
                                                    parent = await element.query_selector('xpath=..')
                                                    if parent:
                                                        await parent.click()
                                                        self.log_callback(f"💾 Saved pin {i + 1} (via text search)")
                                                        saved = True
                                                        break
                                                    else:
                                                        # Try clicking the element itself
                                                        await element.click()
                                                        self.log_callback(f"💾 Saved pin {i + 1} (direct click)")
                                                        saved = True
                                                        break
                                        except Exception as save_error:
                                            self.log_callback(f"XPath save attempt failed for pin {i + 1}: {save_error}")
                                    
                                    if not saved:
                                        self.log_callback(f"Couldn't find save button for pin {i + 1}")
                                    
                                    await asyncio.sleep(1)
                                    
                                except Exception as save_error:
                                    self.log_callback(f"Error saving pin {i + 1}: {save_error}")
                                
                            except Exception as e:
                                self.log_callback(f"Error reacting to pin {i + 1}: {e}")
                            
                            clicks_made += 1
                            await self.page.go_back()
                            await asyncio.sleep(2)
                        else:
                            self.log_callback(f"Hover engagement on pin {i + 1}")
                            clicks_made += 1
                    else:
                        # Just scroll as engagement
                        self.log_callback(f"Scrolling engagement for pin {i + 1}")
                        await self.page.evaluate("window.scrollBy(0, 300)")
                        await asyncio.sleep(1)
                        clicks_made += 1
                    
                except Exception as e:
                    self.log_callback(f"Error with pin {i + 1}: {e}")
                    # Still count as engagement
                    clicks_made += 1
                    await asyncio.sleep(1)
            
            self.log_callback(f"Warm-up completed: engaged with {clicks_made}/{warmup_clicks} pins")
            return clicks_made > 0
            
        except Exception as e:
            self.log_callback(f"Error during warm-up: {e}")
            return False
    
    async def scrape_after_warmup(self, num_images=10, download=False, output_name=None):
        """
        Refresh page and scrape feed after warm-up
        """
        try:
            print("Refreshing page and navigating to feed...")
            await self.page.goto("https://www.pinterest.com/", timeout=30000)
            await asyncio.sleep(3)
            
            # Use the parent class method to scrape feed (refactored version only takes num_images)
            return await self.scrape_feed(num_images=num_images)
            
        except Exception as e:
            print(f"Error during post-warmup scraping: {e}")
            return []