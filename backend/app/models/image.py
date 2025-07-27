from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4


class ImageBase(BaseModel):
    prompt_id: UUID
    pin_id: str
    image_url: str
    source_url: Optional[str] = None
    description: Optional[str] = None


class ImageCreate(ImageBase):
    pass


class Image(ImageBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    match_score: Optional[float] = None
    approved: Optional[bool] = None
    
    class Config:
        populate_by_name = True
