#!/usr/bin/env python3
"""
Download images from Pinterest URLs stored in JSON metadata files.
This is for testing purposes only - the main app uses URLs directly.
"""

import json
import argparse
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path to import services
sys.path.append(str(Path(__file__).parent.parent))
from app.services.pinterest.scrapper import download_image

def export_pins_to_json(pin_data, prompt_name, output_dir=None):
    """
    Export pin data to JSON file in exports/ directory
    
    Args:
        pin_data (list): List of pin dictionaries with image_url, pin_url, metadata
        prompt_name (str): Name of the prompt for folder/file naming
        output_dir (str): Optional custom output directory
    
    Returns:
        str: Path to the created JSON file
    """
    # Create exports directory structure
    safe_prompt = prompt_name.replace(' ', '_').replace('/', '_')
    if output_dir:
        export_dir = Path(output_dir) / safe_prompt
    else:
        export_dir = Path("exports") / safe_prompt
    
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate JSON file
    json_file = export_dir / f"{safe_prompt}_metadata.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(pin_data, f, indent=2, ensure_ascii=False)
    
    print(f"Exported metadata for {len(pin_data)} pins to: {json_file}")
    return str(json_file)

def download_from_json(json_file_path, output_folder=None):
    """
    Download images from a JSON metadata file containing Pinterest URLs
    
    Args:
        json_file_path (str): Path to the JSON metadata file
        output_folder (str): Optional custom output folder name
    """
    json_path = Path(json_file_path)
    
    if not json_path.exists():
        print(f"Error: JSON file not found: {json_file_path}")
        return
    
    # Load JSON data
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            pin_data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return
    
    if not pin_data:
        print("No pin data found in JSON file")
        return
    
    # Determine output directory
    if output_folder:
        output_dir = Path("downloaded_images") / output_folder
    else:
        # Use the same name as the JSON file
        output_dir = Path("downloaded_images") / json_path.stem.replace("_metadata", "")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading {len(pin_data)} images to: {output_dir}/")
    
    # Download images using ThreadPoolExecutor for speed
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        
        for index, pin in enumerate(pin_data):
            try:
                image_url = pin.get('image_url')
                if not image_url:
                    print(f"Skipping pin {index+1}: no image_url found")
                    continue
                
                # Generate filename
                safe_name = output_dir.name
                file_name = output_dir / f"{safe_name}_{index+1}.jpg"
                
                # Submit download task
                future = executor.submit(download_image, image_url, file_name)
                futures.append((future, index+1, file_name.name))
                
            except Exception as e:
                print(f"Error preparing download for pin {index+1}: {e}")
                continue
        
        # Wait for all downloads to complete
        successful_downloads = 0
        for future, pin_num, filename in futures:
            try:
                future.result()  # Wait for completion
                print(f"Downloaded: {filename}")
                successful_downloads += 1
            except Exception as e:
                print(f"Failed to download pin {pin_num}: {e}")
    
    print(f"\nDownload completed! {successful_downloads}/{len(pin_data)} images downloaded to: {output_dir}/")

def main():
    parser = argparse.ArgumentParser(
        description="Download images from Pinterest URLs in JSON metadata files"
    )
    parser.add_argument(
        "json_file", 
        help="Path to JSON metadata file (e.g., exports/prompt_name/prompt_name_metadata.json)"
    )
    parser.add_argument(
        "-o", "--output", 
        help="Custom output folder name (default: derived from JSON filename)"
    )
    
    args = parser.parse_args()
    
    download_from_json(args.json_file, args.output)

if __name__ == "__main__":
    main()