from datetime import datetime
from typing import List
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.prompt import PyObjectId

class PinBase(BaseModel):
    prompt_id: PyObjectId
    image_url: str
    pin_url: str
    title: str
    description: str
    match_score: float = 0.0
    status: str = "approved"  # "approved" | "disqualified"
    ai_explanation: str = ""

class PinCreate(PinBase):
    pass

class PinMetadata(BaseModel):
    collected_at: datetime = Field(default_factory=datetime.utcnow)

class Pin(PinBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    metadata: PinMetadata = Field(default_factory=PinMetadata)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "prompt_id": "507f1f77bcf86cd799439012",
                "image_url": "https://example.com/image.jpg",
                "pin_url": "https://pinterest.com/pin/123456",
                "title": "Industrial Home Office",
                "description": "Cozy industrial home office with exposed brick",
                "match_score": 0.85,
                "status": "approved",
                "ai_explanation": "This image matches the prompt well because it shows a cozy industrial home office setting.",
                "metadata": {
                    "collected_at": "2023-01-01T00:00:00"
                }
            }
        }
    }