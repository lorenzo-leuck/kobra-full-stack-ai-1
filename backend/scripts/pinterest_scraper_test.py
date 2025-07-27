#!/usr/bin/env python3

import argparse
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright
import time
import random

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

def get_image_urls(url, num_images=10, scroll_attempts_limit=250, headless=True):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(url, timeout=0)
            page.wait_for_selector("img", timeout=60000)
        except Exception as e:
            print(f"Error Loading Page: {e}")
            browser.close()
            return []

        img_urls = set()
        scroll_attempts = 0

        while len(img_urls) < num_images and scroll_attempts < scroll_attempts_limit:
            page.wait_for_selector("img", timeout=60000)
            img_elements = page.query_selector_all("img")
            for img in img_elements:
                src = img.get_attribute("src")
                if src and src.startswith("http"):
                    img_urls.add(src)
                if len(img_urls) >= num_images:
                    break
            
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            print(f"Scrolling: {scroll_attempts}", end="\r")
            t = random.randint(4, 8)
            time.sleep(t)
            scroll_attempts += 1

        browser.close()
        return list(img_urls)[:num_images]

def parse_args():
    parser = argparse.ArgumentParser(description="Pinterest Image Scraper")
    parser.add_argument("username", type=str, help="Pinterest username or page")
    parser.add_argument("tag", type=str, help="Board tag or name")
    parser.add_argument("num_images", type=int, help="Number of images to download")
    parser.add_argument("--headless", action="store_true", help="Run headless (without GUI)")
    return parser.parse_args()

def main():
    args = parse_args()
    pinterest_url = f"https://www.pinterest.com/{args.username}/{args.tag}/"
    print(f"Getting started with URL: {pinterest_url}")

    img_urls = get_image_urls(pinterest_url, num_images=args.num_images, headless=args.headless)
    if not img_urls:
        print("Image not found. Please try again.")
        return

    print(f"Number of images found: {len(img_urls)}")
    download_images(img_urls, args.username)
    print("\nThe image download has finished.")

if __name__ == "__main__":
    main()
