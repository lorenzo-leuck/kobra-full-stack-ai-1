#!/usr/bin/env python3

import argparse
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add app directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "app"))
from services.pinterest.session import PinterestSession

# Load environment variables
load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description="Pinterest Session Manager")
    parser.add_argument("--username", type=str, help="Pinterest username (defaults to env variable)")
    parser.add_argument("--password", type=str, help="Pinterest password (defaults to env variable)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("num_images", type=int, nargs="?", default=10, help="Number of images to scrape from feed (default: 10)")
    parser.add_argument("--output-name", type=str, default="feed", help="Output folder name (default: feed)")
    parser.add_argument("--no-download", action="store_true", help="Don't download images, just return URLs")
    return parser.parse_args()

async def main_async():
    args = parse_args()
    
    # Create session with provided credentials or from env variables
    session = PinterestSession(
        username=args.username,
        password=args.password
    )
    
    try:
        # Initialize browser
        print("Initializing browser...")
        await session.initialize_browser(headless=args.headless)
        
        # Login
        print("Attempting login...")
        success = await session.login()
        
        if success:
            print("Login successful")
            
            # Scrape feed
            print(f"Scraping {args.num_images} images from feed...")
            img_urls = await session.scrape_feed(
                num_images=args.num_images,
                download=not args.no_download,
                output_name=args.output_name
            )
            
            print(f"\nCompleted! Found {len(img_urls)} images.")
            if not args.no_download:
                print(f"Images saved to: downloaded_images/{args.output_name}/")
            
        else:
            print("Login failed")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Always close the session
        await session.close()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()