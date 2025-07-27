from fastapi import APIRouter, HTTPException, Depends
from typing import List
from bson import ObjectId
import pymongo
from app.models.prompt import Prompt, PromptCreate, PyObjectId
from app.models.session import Session, SessionCreate
from app.models.image import Pin, PinCreate
from app.database import get_database
from app.services.pinterest_scraper import PinterestScraper
from app.services.image_evaluator import ImageEvaluator
import asyncio
import threading

router = APIRouter(
    prefix="/prompts",
    tags=["prompts"]
)

def process_prompt_background(prompt_id: ObjectId, prompt_text: str, db):
    # Run in a separate thread to handle the async operations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Create session for warmup stage
        warmup_session = SessionCreate(
            prompt_id=prompt_id,
            stage="warmup",
            status="pending",
            log=["Starting Pinterest warmup phase"]
        )
        session_dict = warmup_session.model_dump()
        db.sessions.insert_one(session_dict)
        
        # Initialize scraper and run in the event loop
        scraper = PinterestScraper()
        loop.run_until_complete(scraper.initialize())
        
        # Update session status to completed
        db.sessions.update_one(
            {"prompt_id": prompt_id, "stage": "warmup"},
            {"$set": {"status": "completed"}, "$push": {"log": "Completed warmup phase"}}
        )
        
        # Create session for scraping stage
        scraping_session = SessionCreate(
            prompt_id=prompt_id,
            stage="scraping",
            status="pending",
            log=["Starting Pinterest scraping phase"]
        )
        session_dict = scraping_session.model_dump()
        db.sessions.insert_one(session_dict)
        
        # Simulate Pinterest activity and scrape pins
        loop.run_until_complete(scraper.simulate_pinterest_activity(prompt_text))
        pins = loop.run_until_complete(scraper.scrape_pins(max_pins=30))
        
        # Close scraper
        loop.run_until_complete(scraper.close())
        
        # Update session status to completed
        db.sessions.update_one(
            {"prompt_id": prompt_id, "stage": "scraping"},
            {"$set": {"status": "completed"}, "$push": {"log": f"Scraped {len(pins)} pins"}}
        )
        
        # Create session for validation stage
        validation_session = SessionCreate(
            prompt_id=prompt_id,
            stage="validation",
            status="pending",
            log=["Starting image validation phase"]
        )
        session_dict = validation_session.model_dump()
        db.sessions.insert_one(session_dict)
        
        # Evaluate images
        evaluator = ImageEvaluator()
        for pin in pins:
            match_score = loop.run_until_complete(
                evaluator.evaluate_image_match(prompt_text, pin.get("description", ""))
            )
            
            ai_explanation = loop.run_until_complete(
                evaluator.generate_explanation(prompt_text, pin.get("description", ""), match_score)
            )
            
            # Save pin to database
            pin_data = {
                "prompt_id": prompt_id,
                "image_url": pin.get("image_url"),
                "pin_url": pin.get("source_url", ""),  # Using source_url as pin_url
                "title": pin.get("title", ""),
                "description": pin.get("description", ""),
                "match_score": match_score,
                "status": "approved" if match_score >= 0.7 else "disqualified",
                "ai_explanation": ai_explanation,
                "metadata": {"collected_at": pin.get("collected_at", None)}
            }
            db.pins.insert_one(pin_data)
        
        # Update session status to completed
        db.sessions.update_one(
            {"prompt_id": prompt_id, "stage": "validation"},
            {"$set": {"status": "completed"}, "$push": {"log": "Completed validation phase"}}
        )
        
        # Update prompt status to completed
        db.prompts.update_one(
            {"_id": prompt_id},
            {"$set": {"status": "completed"}}
        )
    except pymongo.errors.PyMongoError as e:
        # Update current session to failed
        db.sessions.update_one(
            {"prompt_id": prompt_id, "status": "pending"},
            {"$set": {"status": "failed"}, "$push": {"log": f"Database error: {str(e)}"}}
        )
        
        # Update prompt status to error
        db.prompts.update_one(
            {"_id": prompt_id},
            {"$set": {"status": "error"}}
        )
        print(f"Database error: {str(e)}")
    except ValueError as e:
        # Update current session to failed
        db.sessions.update_one(
            {"prompt_id": prompt_id, "status": "pending"},
            {"$set": {"status": "failed"}, "$push": {"log": f"Value error: {str(e)}"}}
        )
        
        # Update prompt status to error
        db.prompts.update_one(
            {"_id": prompt_id},
            {"$set": {"status": "error"}}
        )
        print(f"Value error: {str(e)}")
    except Exception as e:
        # Update current session to failed
        db.sessions.update_one(
            {"prompt_id": prompt_id, "status": "pending"},
            {"$set": {"status": "failed"}, "$push": {"log": f"Unexpected error: {str(e)}"}}
        )
        
        # Update prompt status to error
        db.prompts.update_one(
            {"_id": prompt_id},
            {"$set": {"status": "error"}}
        )
        print(f"Unexpected error: {str(e)}")
    finally:
        loop.close()

@router.post("/", response_model=Prompt)
def create_prompt(
    prompt: PromptCreate,
    db = Depends(get_database)
):
    try:
        prompt_dict = prompt.model_dump()
        new_prompt = Prompt(**prompt_dict)
        
        # Insert prompt into database
        result = db.prompts.insert_one(new_prompt.model_dump(by_alias=True))
        prompt_id = result.inserted_id
        
        # Process prompt in background
        thread = threading.Thread(
            target=process_prompt_background,
            args=(prompt_id, new_prompt.text, db)
        )
        thread.daemon = True
        thread.start()
        
        # Retrieve the inserted prompt
        created_prompt = db.prompts.find_one({"_id": prompt_id})
        return Prompt(**created_prompt)
    except pymongo.errors.PyMongoError as e:
        # Update prompt status to error if ID exists
        if "prompt_dict" in locals() and "_id" in prompt_dict:
            db.prompts.update_one(
                {"_id": prompt_dict["_id"]},
                {"$set": {"status": "error"}}
            )
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e
    except ValueError as e:
        # Update prompt status to error if ID exists
        if "prompt_dict" in locals() and "_id" in prompt_dict:
            db.prompts.update_one(
                {"_id": prompt_dict["_id"]},
                {"$set": {"status": "error"}}
            )
        raise HTTPException(status_code=400, detail=f"Value error: {str(e)}") from e
    except Exception as e:
        # Update prompt status to error if ID exists
        if "prompt_dict" in locals() and "_id" in prompt_dict:
            db.prompts.update_one(
                {"_id": prompt_dict["_id"]},
                {"$set": {"status": "error"}}
            )
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") from e

@router.get("/", response_model=List[Prompt])
def get_prompts(db = Depends(get_database)):
    try:
        prompts = list(db.prompts.find())
        return [Prompt(**prompt) for prompt in prompts]
    except pymongo.errors.PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") from e

@router.get("/{prompt_id}", response_model=Prompt)
def get_prompt(prompt_id: str, db = Depends(get_database)):
    try:
        prompt_id = ObjectId(prompt_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid prompt ID format") from exc
    
    try:
        prompt = db.prompts.find_one({"_id": prompt_id})
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        return Prompt(**prompt)
    except pymongo.errors.PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") from e