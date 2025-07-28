import asyncio
from datetime import datetime


class PinterestPins:
    """Handle Pinterest pin data extraction and enrichment"""
    
    def __init__(self, page):
        self.page = page
    
    async def scrape_feed(self, num_images=10):
        """
        Scrape Pinterest feed for pin data (URLs, descriptions, metadata)
        
        Args:
            num_images (int): Number of pins to collect
            
        Returns:
            list: List of pin dictionaries with image_url, pin_url, title, description, metadata
        """
        print(f"Collecting images: 0/{num_images}")
        
        # Get all pin wrappers from the feed
        pins = await self.page.query_selector_all("div[data-test-id='pinWrapper']")
        print(f"Found {len(pins)} pins in feed")
        
        if not pins:
            print("No pins found in feed")
            return []
        
        pin_data_list = []
        
        for i, pin in enumerate(pins[:num_images]):
            try:
                # Extract image URL (Pinterest CDN URL for AI validation)
                image_element = await pin.query_selector("img")
                if not image_element:
                    continue
                
                image_url = await image_element.get_attribute("src")
                if not image_url or not image_url.startswith("http"):
                    continue
                
                # Upgrade to higher resolution if possible
                if "236x" in image_url:
                    image_url = image_url.replace("236x", "736x")
                elif "474x" in image_url:
                    image_url = image_url.replace("474x", "736x")
                
                # Extract pin URL (Pinterest page URL)
                pin_link = await pin.query_selector("a[href*='/pin/']")
                if not pin_link:
                    continue
                
                pin_url = await pin_link.get_attribute("href")
                if not pin_url:
                    continue
                
                # Make sure it's a full URL
                if pin_url.startswith("/"):
                    pin_url = f"https://pinterest.com{pin_url}"
                
                # Extract description from image alt text (cleaned)
                description = await image_element.get_attribute("alt")
                if description:
                    # Clean Pinterest prefixes
                    if description.startswith("This may contain: "):
                        description = description.replace("This may contain: ", "")
                    description = description.strip()
                else:
                    description = None
                
                # Title will be null initially (enriched later)
                title = None
                
                # Create pin data object
                pin_data = {
                    "image_url": image_url,
                    "pin_url": pin_url,
                    "title": title,
                    "description": description,
                    "metadata": {
                        "collected_at": datetime.now().isoformat()
                    }
                }
                
                pin_data_list.append(pin_data)
                print(f"Collected pin {len(pin_data_list)}/{num_images}")
                
                if len(pin_data_list) >= num_images:
                    break
                    
            except Exception as e:
                print(f"Error processing pin {i+1}: {e}")
                continue
        
        print(f"\nTotal images found in feed: {len(pin_data_list)}")
        return pin_data_list
    
    async def enrich_with_titles(self, pin_data_list):
        """
        Navigate to each pin URL to extract h1 titles
        
        Args:
            pin_data_list (list): List of pin dictionaries from scrape_feed()
            
        Returns:
            list: Pin data enriched with titles
        """
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
