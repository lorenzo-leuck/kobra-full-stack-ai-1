#!/usr/bin/env python3

import asyncio
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add app directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from app.services.workflow.main import WorkflowOrchestrator
from app.database import PromptDB, SessionDB, PinDB

load_dotenv()

async def example_workflow():
    """Example usage of the WorkflowOrchestrator class"""
    
    # Create workflow orchestrator instance
    workflow = WorkflowOrchestrator(
        prompt="cozy industrial home office"
    )
    
    print(f"Created workflow orchestrator for prompt: '{workflow.prompt}'")
    
    # Run Pinterest workflow
    print("Starting Pinterest workflow...")
    result = await workflow.run_pinterest_workflow(
        num_images=10,  # Scrape 10 images
        headless=True   # Run in headless mode
        # username and password will be loaded from environment variables
    )
    
    # Print results
    if result['success']:
        print(f"\n✅ Workflow completed successfully!")
        print(f"📌 Scraped {result['pin_count']} pins")
        print(f"🆔 Prompt ID: {result['prompt_id']}")
        
        # Get pins from database
        pins = PinDB.get_pins_by_prompt(workflow.prompt_id)
        if pins:
            sample_pin = pins[0]
            print(f"\nSample pin from database:")
            print(f"  Title: {sample_pin.get('title', 'No title')}")
            print(f"  Description: {sample_pin.get('description', 'No description')[:100]}...")
            print(f"  Image URL: {sample_pin['image_url']}")
            print(f"  Pin URL: {sample_pin['pin_url']}")
        
        # Save results to JSON
        workflow_data = {
            'prompt_id': result['prompt_id'],
            'pin_count': result['pin_count'],
            'status': workflow.get_status(),
            'pins': pins
        }
        with open('workflow_results.json', 'w') as f:
            json.dump(workflow_data, f, indent=2, default=str)
        print(f"\n💾 Results saved to workflow_results.json")
        
    else:
        print(f"\n❌ Workflow failed: {result.get('error', 'Unknown error')}")
        print(f"📝 Check database for session logs")
    
    # Print workflow status
    status = workflow.get_status()
    print(f"\n📊 Workflow Status:")
    print(f"  Prompt Status: {status['prompt_status']}")
    print(f"  Pin Count: {status['pin_count']}")
    print(f"  Sessions: {len(status['sessions'])}")

async def example_step_by_step():
    """Example of running workflow step by step with status monitoring"""
    
    workflow = WorkflowOrchestrator(prompt="minimalist bedroom decor")
    print(f"Created workflow orchestrator for prompt: '{workflow.prompt}'")
    
    # Run Pinterest workflow with monitoring
    print("🔧 Starting Pinterest workflow...")
    result = await workflow.run_pinterest_workflow(
        num_images=5,  # Scrape 5 images for testing
        headless=True
    )
    
    if result['success']:
        print(f"✅ Workflow completed successfully!")
        print(f"📌 Scraped {result['pin_count']} pins")
        print(f"🆔 Prompt ID: {result['prompt_id']}")
        
        # Show pins from database
        if workflow.prompt_id:
            pins = PinDB.get_pins_by_prompt(workflow.prompt_id)
            print(f"\n📝 Pins with titles:")
            for i, pin in enumerate(pins[:3]):
                title = pin.get('title', 'No title')
                print(f"  Pin {i+1}: {title}")
    else:
        print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
    
    # Show final status
    if workflow.prompt_id:
        status = workflow.get_status()
        print(f"\n📊 Final status: {status['prompt_status']}")
        print(f"Sessions completed: {len([s for s in status['sessions'] if s['status'] == 'completed'])}")

if __name__ == "__main__":
    print("Pinterest Workflow Examples")
    print("=" * 40)
    
    # Choose which example to run
    print("1. Complete workflow")
    print("2. Step-by-step workflow")
    
    choice = input("Choose example (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(example_workflow())
    elif choice == "2":
        asyncio.run(example_step_by_step())
    else:
        print("Invalid choice")
