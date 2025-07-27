from fastapi import APIRouter, HTTPException, Depends
from typing import List
from uuid import UUID
from app.models.image import Image
from app.database import get_database

router = APIRouter(
    prefix="/images",
    tags=["images"]
)

@router.get("/prompt/{prompt_id}", response_model=List[Image])
def get_images_by_prompt(
    prompt_id: UUID,
    min_score: float = None,
    db = Depends(get_database)
):
    query = {"prompt_id": str(prompt_id)}
    
    # Apply score filter if provided
    if min_score is not None:
        query["match_score"] = {"$gte": min_score}
    
    images = list(db.images.find(query))
    return [Image(**image) for image in images]

@router.put("/{image_id}/approve", response_model=Image)
def approve_image(
    image_id: UUID,
    approved: bool,
    db = Depends(get_database)
):
    result = db.images.update_one(
        {"id": str(image_id)},
        {"$set": {"approved": approved}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    
    updated_image = db.images.find_one({"id": str(image_id)})
    return Image(**updated_image)
