from fastapi import APIRouter, HTTPException, Depends
from typing import List
from bson import ObjectId
from app.models.prompt import PyObjectId
from app.models.image import Pin
from app.database import get_database

router = APIRouter(
    prefix="/pins",
    tags=["pins"]
)

@router.get("/prompt/{prompt_id}", response_model=List[Pin])
def get_pins_by_prompt(
    prompt_id: str,
    min_score: float = None,
    status: str = None,
    db = Depends(get_database)
):
    try:
        prompt_id = ObjectId(prompt_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid prompt ID format") from exc
        
    try:
        query = {"prompt_id": prompt_id}
        
        # Apply score filter if provided
        if min_score is not None:
            query["match_score"] = {"$gte": min_score}
            
        # Apply status filter if provided
        if status is not None:
            query["status"] = status
        
        pins = list(db.pins.find(query))
        return [Pin(**pin) for pin in pins]
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc

@router.put("/{pin_id}/status", response_model=Pin)
def update_pin_status(
    pin_id: str,
    status: str,
    db = Depends(get_database)
):
    try:
        pin_id = ObjectId(pin_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid pin ID format") from exc
        
    try:
        # Validate status value
        if status not in ["approved", "disqualified"]:
            raise HTTPException(status_code=400, detail="Status must be 'approved' or 'disqualified'")
        
        result = db.pins.update_one(
            {"_id": pin_id},
            {"$set": {"status": status}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Pin not found")
        
        updated_pin = db.pins.find_one({"_id": pin_id})
        return Pin(**updated_pin)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc
