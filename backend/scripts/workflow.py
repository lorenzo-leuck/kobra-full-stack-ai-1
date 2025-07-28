#!/usr/bin/env python3
"""
Main Pinterest Workflow Script
Runs the complete Pinterest + AI validation workflow + downloads results
"""

import asyncio
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from bson import ObjectId

# Add app directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from app.services.workflow.main import WorkflowOrchestrator
from app.database import PromptDB, PinDB
from app.config import settings
from download import export_pins_to_json, download_from_json

load_dotenv()

# Configuration
PINTEREST_PROMPT = "retro future bam bam"
NUM_IMAGES = 10

async def run_complete_workflow():
    """Run the complete Pinterest + AI validation workflow"""
    
    print(f"🚀 Running Complete Workflow: '{PINTEREST_PROMPT}'")
    print("=" * 60)
    
    # Check prerequisites
    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not configured")
        print("Set OPENAI_API_KEY in .env file")
        return
    
    # Create workflow orchestrator
    orchestrator = WorkflowOrchestrator(prompt=PINTEREST_PROMPT)
    print(f"Created workflow orchestrator for prompt: '{orchestrator.prompt}'")
    
    # Phase 1: Pinterest Workflow
    print("\n📌 PHASE 1: Pinterest Scraping & Enrichment")
    print("-" * 50)
    
    pinterest_result = await orchestrator.run_pinterest_workflow(
        num_images=NUM_IMAGES,
        headless=True
    )
    
    if not pinterest_result['success']:
        print(f"❌ Pinterest workflow failed: {pinterest_result.get('error', 'Unknown error')}")
        return
    
    prompt_id = ObjectId(pinterest_result['prompt_id'])
    pin_count = pinterest_result['pin_count']
    
    print(f"✅ Pinterest workflow completed!")
    print(f"   Scraped and enriched: {pin_count} pins")
    print(f"   Prompt ID: {prompt_id}")
    
    # Show sample scraped data
    ready_pins = PinDB.get_pins_by_status(prompt_id, "ready")
    if ready_pins:
        sample_pin = ready_pins[0]
        print(f"\n📋 Sample scraped pin:")
        print(f"   Title: {sample_pin.get('title', 'No title')}")
        print(f"   Description: {sample_pin.get('description', 'No description')[:60]}...")
        print(f"   Status: {sample_pin.get('status', 'unknown')}")
    
    # Phase 2: AI Validation
    print("\n🤖 PHASE 2: AI Validation")
    print("-" * 50)
    
    ai_result = await orchestrator.run_ai_validation_workflow(prompt_id)
    
    if ai_result['success']:
        print(f"✅ AI validation completed!")
        print(f"   Evaluated: {ai_result['evaluated_count']} pins")
        print(f"   Approved: {ai_result['approved_count']} pins (≥0.5 score)")
        print(f"   Disqualified: {ai_result['disqualified_count']} pins (<0.5 score)")
        
        # Show top approved results
        approved_pins = PinDB.get_pins_by_status(prompt_id, "approved")
        if approved_pins:
            print(f"\n🎯 Top approved pins:")
            approved_sorted = sorted(approved_pins, key=lambda x: x['match_score'], reverse=True)
            for i, pin in enumerate(approved_sorted[:2], 1):
                print(f"   {i}. {pin.get('title', 'No title')} (Score: {pin['match_score']:.2f})")
                print(f"      AI: {pin['ai_explanation'][:70]}...")
    else:
        print(f"❌ AI validation failed: {ai_result.get('error', 'Unknown error')}")
        return
    
    # Final Results Summary
    print("\n📊 FINAL RESULTS")
    print("-" * 50)
    
    # Get final prompt status
    prompt_doc = PromptDB.get_prompt_by_id(prompt_id)
    final_status = prompt_doc['status'] if prompt_doc else 'unknown'
    
    all_pins = PinDB.get_pins_by_prompt(prompt_id)
    approved_count = len([p for p in all_pins if p.get('status') == 'approved'])
    disqualified_count = len([p for p in all_pins if p.get('status') == 'disqualified'])
    ready_count = len([p for p in all_pins if p.get('status') == 'ready'])
    
    print(f"Prompt Status: {final_status}")
    print(f"Total Pins: {len(all_pins)}")
    print(f"  ✅ Approved: {approved_count}")
    print(f"  ❌ Disqualified: {disqualified_count}")
    
    # Save results
    results = {
        'prompt': PINTEREST_PROMPT,
        'prompt_id': str(prompt_id),
        'final_status': final_status,
        'total_pins': len(all_pins),
        'approved_pins': approved_count,
        'disqualified_pins': disqualified_count,
        'timestamp': str(prompt_doc['created_at']) if prompt_doc else None
    }
    
    with open('workflow_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Test results saved to workflow_test_results.json")
    
    # Phase 3: Download Results
    print("\n💾 PHASE 3: Download Results")
    print("-" * 50)
    
    await download_workflow_results(prompt_id, PINTEREST_PROMPT)
    
    print(f"🎉 Complete workflow finished successfully!")

async def download_workflow_results(prompt_id: ObjectId, prompt_text: str):
    """Download and export workflow results with pin IDs as filenames"""
    
    # Get all pins from database
    all_pins = PinDB.get_pins_by_prompt(prompt_id)
    if not all_pins:
        print("No pins found to download")
        return
    
    # Prepare pin data for export with pin IDs as identifiers
    export_data = []
    for pin in all_pins:
        pin_data = {
            'pin_id': str(pin['_id']),
            'image_url': pin['image_url'],
            'pin_url': pin['pin_url'],
            'title': pin.get('title', 'No title'),
            'description': pin.get('description', 'No description'),
            'status': pin.get('status', 'unknown'),
            'match_score': pin.get('match_score'),
            'ai_explanation': pin.get('ai_explanation'),
            'metadata': pin.get('metadata', {})
        }
        export_data.append(pin_data)
    
    # Export to JSON
    print(f"Exporting {len(export_data)} pins to JSON...")
    json_file = export_pins_to_json(export_data, prompt_text)
    print(f"✅ JSON exported: {json_file}")
    
    # Download images with pin IDs as filenames
    print(f"\nDownloading {len(export_data)} images with pin IDs as filenames...")
    await download_images_with_pin_ids(export_data, prompt_text)
    
    print(f"✅ Download phase completed!")
    print(f"📁 Check exports/{prompt_text.replace(' ', '_')}/ for results")

async def download_images_with_pin_ids(pin_data: list, prompt_text: str):
    """Download images using pin IDs as filenames"""
    import urllib.request
    from concurrent.futures import ThreadPoolExecutor
    
    # Create output directory
    safe_prompt = prompt_text.replace(' ', '_').replace('/', '_')
    output_dir = Path("exports") / safe_prompt
    output_dir.mkdir(parents=True, exist_ok=True)
    
    def download_pin_image(pin):
        """Download single pin image with pin ID as filename"""
        try:
            pin_id = pin['pin_id']
            image_url = pin['image_url']
            
            # Use pin ID as filename
            filename = f"{pin_id}.jpg"
            file_path = output_dir / filename
            
            urllib.request.urlretrieve(image_url, file_path)
            return f"Downloaded: {filename}"
        except Exception as e:
            return f"Failed to download {pin.get('pin_id', 'unknown')}: {e}"
    
    # Download images concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(download_pin_image, pin) for pin in pin_data]
        
        successful_downloads = 0
        for future in futures:
            try:
                result = future.result()
                if "Downloaded:" in result:
                    successful_downloads += 1
                print(result)
            except Exception as e:
                print(f"Download error: {e}")
    
    print(f"\n✅ Downloaded {successful_downloads}/{len(pin_data)} images to: {output_dir}/")

if __name__ == "__main__":
    # Run the complete Pinterest + AI validation workflow
    asyncio.run(run_complete_workflow())
