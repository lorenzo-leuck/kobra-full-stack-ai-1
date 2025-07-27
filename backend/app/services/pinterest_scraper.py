from playwright.async_api import async_playwright
from app.config import settings
import asyncio
from typing import List, Dict, Any
import logging
import random
from urllib.parse import quote


class PinterestScraper:
    def __init__(self):
        self.base_url = settings.PINTEREST_BASE_URL
        self.browser = None
        self.context = None
        self.page = None
        
    async def initialize(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.page = await self.context.new_page()
        
    async def close(self):
        if self.browser:
            await self.browser.close()
            
    async def simulate_pinterest_activity(self, visual_prompt: str) -> None:
        search_query = quote(visual_prompt)
        search_url = f"{self.base_url}/search/pins/?q={search_query}"
        
        await self.page.goto(search_url)
        await self.page.wait_for_load_state("networkidle")
        
        # Simulate scrolling to generate more results
        for _ in range(3):
            await self.page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
    async def scrape_pins(self, max_pins: int = 30) -> List[Dict[Any, Any]]:
        pins = []
        
        # Wait for pin elements to load
        await self.page.wait_for_selector("div[data-test-id='pin']", timeout=10000)
        
        # Extract pin data
        pin_elements = await self.page.query_selector_all("div[data-test-id='pin']")
        
        for i, pin in enumerate(pin_elements):
            if i >= max_pins:
                break
                
            try:
                # Extract pin ID
                pin_id_element = await pin.query_selector("a[data-test-id='pinWrapper']")
                pin_id = "unknown"
                if pin_id_element:
                    href = await pin_id_element.get_attribute("href")
                    if href:
                        pin_id = href.split("/")[2]
                
                # Extract image URL
                img_element = await pin.query_selector("img")
                image_url = await img_element.get_attribute("src") if img_element else None
                
                # Extract description
                description_element = await pin.query_selector("div[data-test-id='pinTitle']")
                description = await description_element.inner_text() if description_element else ""
                
                # Extract source URL
                source_url_element = await pin.query_selector("a[data-test-id='pinWrapper']")
                source_url = f"{self.base_url}{await source_url_element.get_attribute('href')}" if source_url_element else None
                
                if image_url:
                    pins.append({
                        "pin_id": pin_id,
                        "image_url": image_url,
                        "description": description,
                        "source_url": source_url
                    })
            except Exception as e:
                logging.error(f"Error extracting pin data: {e}")
                continue
                
        return pins
