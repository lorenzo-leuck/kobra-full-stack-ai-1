from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4


class PromptBase(BaseModel):
    visual_prompt: str


class PromptCreate(PromptBase):
    pass


class Prompt(PromptBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, in_progress, completed, failed
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "visual_prompt": "cozy industrial home office",
                "created_at": "2023-01-01T00:00:00",
                "status": "pending"
            }
        }
