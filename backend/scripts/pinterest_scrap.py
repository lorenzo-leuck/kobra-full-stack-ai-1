#!/usr/bin/env python3

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "app"))
from services.pinterest.scrapper import scrape_pinterest_images

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
    
    await scrape_pinterest_images(
        search_query=args.search_query,
        num_images=args.num_images,
        headless=args.headless,
        download=True,
        output_name=args.output_name
    )

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
