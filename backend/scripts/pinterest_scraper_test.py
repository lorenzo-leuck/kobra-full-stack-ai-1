#!/usr/bin/env python3

import argparse
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
            await asyncio.sleep(2)  # Give page time to load
            
            img_urls = set()
            scroll_attempts = 0
            
            while len(img_urls) < num_images and scroll_attempts < scroll_attempts_limit:
                print(f"Scroll attempt {scroll_attempts+1}/{scroll_attempts_limit}")
                
                # Try to find pin wrappers
                pins = await page.query_selector_all("div[data-test-id='pinWrapper']")
                print(f"Found {len(pins)} pins")
                
                for pin in pins:
                    try:
                        # Get the image element within the pin
                        image_element = await pin.query_selector("img")
                        if image_element:
                            # Try to get srcset first for higher quality
                            srcset = await image_element.get_attribute("srcset")
                            if srcset:
                                # Parse srcset to get highest resolution image
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
                                # Fallback to src attribute
                                src = await image_element.get_attribute("src")
                                if src and src.startswith("http"):
                                    # Try to get higher resolution version
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
                    
                # Scroll down to load more pins
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(2)  # Wait for new content to load
                scroll_attempts += 1
                print(f"Found {len(img_urls)} images so far")
                
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            await browser.close()
            
        return list(img_urls)[:num_images]

        browser.close()
        return list(img_urls)[:num_images]

def parse_args():
    parser = argparse.ArgumentParser(description="Pinterest Search Image Scraper")
    parser.add_argument("search_query", type=str, help="Search terms for Pinterest (e.g., 'modern kitchen design')")
    parser.add_argument("num_images", type=int, help="Number of images to download")
    parser.add_argument("--headless", action="store_true", help="Run headless (without GUI)")
    parser.add_argument("--output-name", type=str, help="Custom name for output folder (default: uses search query)")
    parser.add_argument("--use-explore", action="store_true", help="Use Pinterest explore URL format")
    return parser.parse_args()

async def main_async():
    args = parse_args()
    
    search_terms = args.search_query.replace(" ", "+")
    
    # Use the explore URL format which seems to work better
    pinterest_url = f"https://www.pinterest.com/search/pins/?q={search_terms}&rs=typed"
    
    print(f"Searching Pinterest for: {args.search_query}")
    print(f"URL: {pinterest_url}")
    print(f"Running in {'headless' if args.headless else 'visible'} mode")

    img_urls = await get_image_urls(pinterest_url, num_images=args.num_images, headless=args.headless)
    if not img_urls:
        print("No images found. Please try a different search query or run without --headless to debug.")
        return

    print(f"\nNumber of images found: {len(img_urls)}")
    
    output_name = args.output_name if args.output_name else args.search_query.replace(" ", "_")
    download_images(img_urls, output_name)
    print("\nThe image download has finished.")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
