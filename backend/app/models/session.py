from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from app.models.prompt import PyObjectId

class SessionBase(BaseModel):
    prompt_id: PyObjectId
    stage: str  # "warmup" | "scraping" | "validation"
    status: str = "pending"  # "pending" | "completed" | "failed"
    log: List[str] = []

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "prompt_id": "507f1f77bcf86cd799439012",
                "stage": "warmup",
                "status": "pending",
                "timestamp": "2023-01-01T00:00:00",
                "log": ["Started warmup phase", "Completed warmup phase"]
            }
        }
    }
