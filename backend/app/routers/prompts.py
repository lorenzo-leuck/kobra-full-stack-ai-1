from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
from uuid import UUID
from app.models.prompt import Prompt, PromptCreate
from app.database import get_database
from app.services.pinterest_scraper import PinterestScraper
from app.services.image_evaluator import ImageEvaluator
import asyncio
import threading

router = APIRouter(
    prefix="/prompts",
    tags=["prompts"]
)

def process_prompt_background(prompt_id: UUID, prompt_text: str, db):
    # Run in a separate thread to handle the async operations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Update status to in_progress
        db.prompts.update_one(
            {"id": str(prompt_id)},
            {"$set": {"status": "in_progress"}}
        )
        
        # Initialize scraper and run in the event loop
        scraper = PinterestScraper()
        loop.run_until_complete(scraper.initialize())
        
        # Simulate Pinterest activity and scrape pins
        loop.run_until_complete(scraper.simulate_pinterest_activity(prompt_text))
        pins = loop.run_until_complete(scraper.scrape_pins(max_pins=30))
        
        # Close scraper
        loop.run_until_complete(scraper.close())
        
        # Evaluate images
        evaluator = ImageEvaluator()
        for pin in pins:
            match_score = loop.run_until_complete(
                evaluator.evaluate_image_match(prompt_text, pin.get("description", ""))
            )
            
            # Save image to database
            db.images.insert_one({
                "prompt_id": str(prompt_id),
                "pin_id": pin.get("pin_id"),
                "image_url": pin.get("image_url"),
                "source_url": pin.get("source_url"),
                "description": pin.get("description"),
                "match_score": match_score,
                "approved": None
            })
        
        # Update status to completed
        db.prompts.update_one(
            {"id": str(prompt_id)},
            {"$set": {"status": "completed"}}
        )
    except Exception as e:
        # Update status to failed
        db.prompts.update_one(
            {"id": str(prompt_id)},
            {"$set": {"status": "failed", "error": str(e)}}
        )
    finally:
        loop.close()

@router.post("/", response_model=Prompt)
def create_prompt(
    prompt: PromptCreate,
    background_tasks: BackgroundTasks,
    db = Depends(get_database)
):
    prompt_dict = prompt.model_dump()
    new_prompt = Prompt(**prompt_dict)
    
    # Insert prompt into database
    db.prompts.insert_one(new_prompt.model_dump())
    
    # Process prompt in background
    thread = threading.Thread(
        target=process_prompt_background,
        args=(new_prompt.id, new_prompt.visual_prompt, db)
    )
    thread.daemon = True
    thread.start()
    
    return new_prompt

@router.get("/", response_model=List[Prompt])
def get_prompts(db = Depends(get_database)):
    prompts = list(db.prompts.find())
    return [Prompt(**prompt) for prompt in prompts]

@router.get("/{prompt_id}", response_model=Prompt)
def get_prompt(prompt_id: UUID, db = Depends(get_database)):
    prompt = db.prompts.find_one({"id": str(prompt_id)})
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return Prompt(**prompt)
