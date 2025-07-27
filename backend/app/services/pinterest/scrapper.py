import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import asyncio
from playwright.async_api import async_playwright
import time
import random
import json
import os

def download_image(img_url, output_path):
    try:
        urllib.request.urlretrieve(img_url, output_path)
        print(f"Downloaded: {output_path.name}", end="\r")
    except Exception as e:
        print(f"Error Downloading {output_path.name}: {e}")

def download_images(img_urls, name_img):
    output_dir = Path("downloaded_images") / name_img
    output_dir.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for index, img_url in enumerate(img_urls):
            file_name = output_dir / f"{name_img}{index+1}.jpg"
            future = executor.submit(download_image, img_url, file_name)
            futures.append(future)
        
        for future in futures:
            future.result()

async def get_image_urls(url, num_images=10, scroll_attempts_limit=10, headless=True):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        try:
            print(f"Navigating to search URL: {url}")
            await page.goto(url, timeout=30000)
            await asyncio.sleep(2)
            
            img_urls = set()
            scroll_attempts = 0
            
            while len(img_urls) < num_images and scroll_attempts < scroll_attempts_limit:
                print(f"Scroll attempt {scroll_attempts+1}/{scroll_attempts_limit}")
                
                pins = await page.query_selector_all("div[data-test-id='pinWrapper']")
                print(f"Found {len(pins)} pins")
                
                for pin in pins:
                    try:
                        image_element = await pin.query_selector("img")
                        if image_element:
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
                                    img_urls.add(highest_res_url)
                            else:
                                src = await image_element.get_attribute("src")
                                if src and src.startswith("http"):
                                    if "236x" in src:
                                        src = src.replace("236x", "736x")
                                    elif "474x" in src:
                                        src = src.replace("474x", "736x")
                                    img_urls.add(src)
                    except Exception as e:
                        print(f"Error processing pin: {e}")
                        continue
                        
                    if len(img_urls) >= num_images:
                        break
                
                if len(img_urls) >= num_images:
                    break
                    
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(2)
                scroll_attempts += 1
                print(f"Found {len(img_urls)} images so far")
                
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            await browser.close()
            
        return list(img_urls)[:num_images]

async def scrape_pinterest_images(search_query: str, num_images: int = 10, headless: bool = True, download: bool = False, output_name: str = None):
    """
    Main function to scrape Pinterest images for a given search query.
    
    Args:
        search_query: The search terms for Pinterest
        num_images: Number of images to scrape
        headless: Whether to run browser in headless mode
        download: Whether to download the images locally
        output_name: Custom name for output folder (optional)
    
    Returns:
        List of image URLs
    """
    search_terms = search_query.replace(" ", "+")
    pinterest_url = f"https://www.pinterest.com/search/pins/?q={search_terms}&rs=typed"
    
    print(f"Searching Pinterest for: {search_query}")
    print(f"URL: {pinterest_url}")
    print(f"Running in {'headless' if headless else 'visible'} mode")

    img_urls = await get_image_urls(pinterest_url, num_images=num_images, headless=headless)
    if not img_urls:
        print("No images found. Please try a different search query or run without --headless to debug.")
        return []

    print(f"\nNumber of images found: {len(img_urls)}")
    
    if download:
        folder_name = output_name if output_name else search_query.replace(" ", "_")
        download_images(img_urls, folder_name)
        print("\nThe image download has finished.")
    
    return img_urls