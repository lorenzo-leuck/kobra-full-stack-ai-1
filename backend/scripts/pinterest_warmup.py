#!/usr/bin/env python3

import argparse
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add app directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "app"))
from services.pinterest.warmup import PinterestWarmup

# Load environment variables
load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description="Pinterest Warmup & Scraper")
    parser.add_argument("prompt", type=str, help="Visual prompt for warm-up (e.g., 'boho minimalist bedroom')")
    parser.add_argument("num_images", type=int, nargs="?", default=10, help="Number of images to scrape (default: 10)")
    parser.add_argument("--username", type=str, help="Pinterest username (defaults to env variable)")
    parser.add_argument("--password", type=str, help="Pinterest password (defaults to env variable)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--output-name", type=str, help="Custom output folder name")
    parser.add_argument("--no-download", action="store_true", help="Don't download images, just return URLs")
    return parser.parse_args()

async def main_async():
    args = parse_args()
    
    # Create warmup session with prompt
    warmup = PinterestWarmup(
        prompt=args.prompt,
        username=args.username,
        password=args.password
    )
    
    try:
        # Initialize browser
        print("Initializing browser...")
        await warmup.initialize_browser(headless=args.headless)
        
        # Login
        print("Attempting login...")
        success = await warmup.login()
        
        if not success:
            print("Login failed")
            return
            
        print("Login successful")
        
        # Feed algorithm (warm-up) - click same number of pins as images to download
        print("\n=== WARM-UP PHASE ===")
        warmup_success = await warmup.feed_algorithm(num_clicks=args.num_images)
        
        if not warmup_success:
            print("Warm-up failed, but continuing with scraping...")
        
        # Scrape after warm-up
        print("\n=== SCRAPING PHASE ===")
        img_urls = await warmup.scrape_after_warmup(
            num_images=args.num_images,
            download=not args.no_download,
            output_name=args.output_name
        )
        
        print(f"\nCompleted! Found {len(img_urls)} images.")
        if not args.no_download:
            folder_name = args.output_name or f"warmup_{args.prompt.replace(' ', '_')}"
            print(f"Images saved to: downloaded_images/{folder_name}/")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Always close the session
        await warmup.close()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()