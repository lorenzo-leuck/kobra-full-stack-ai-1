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
    return parser.parse_args()

async def main_async():
    args = parse_args()
    
    # Create session with provided credentials or from env variables
    session = PinterestSession(
        username=args.username,
        password=args.password
    )
    
    # Initialize and login
    await session.initialize()
    success = await session.login()
    
    if success:
        print("Login successful")
    else:
        print("Login failed")
    
    # Close the session
    await session.close()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()