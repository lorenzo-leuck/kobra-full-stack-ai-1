from datetime import datetime
from typing import List, Optional, Dict
from bson import ObjectId
from pydantic import BaseModel, Field
from .base import BaseDB


class PinMetadata(BaseModel):
    """Metadata for pin documents"""
    collected_at: datetime
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PinSchema(BaseModel):
    """Pydantic schema for pin documents"""
    prompt_id: ObjectId
    image_url: str
    pin_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    match_score: Optional[float] = None  # 0.0-1.0, set by AI validation
    status: Optional[str] = None  # "approved" | "disqualified", set by AI validation
    ai_explanation: Optional[str] = None  # Set by AI validation
    metadata: PinMetadata
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }


class PinDB(BaseDB):
    """Database operations for pins collection"""
    
    collection_name = "pins"
    
    @classmethod
    def create_pins_from_scraped_data(cls, prompt_id: ObjectId, scraped_pins: List[Dict]) -> List[ObjectId]:
        """
        Create pin documents from scraped Pinterest data
        
        Args:
            prompt_id (ObjectId): Associated prompt ID
            scraped_pins (List[Dict]): List of scraped pin data
            
        Returns:
            List[ObjectId]: List of created pin IDs
        """
        if not scraped_pins:
            return []
        
        pin_docs = []
        for pin_data in scraped_pins:
            # Parse collected_at timestamp
            collected_at_str = pin_data["metadata"]["collected_at"]
            if isinstance(collected_at_str, str):
                # Handle ISO format string
                collected_at = datetime.fromisoformat(collected_at_str.replace('Z', '+00:00'))
            else:
                collected_at = collected_at_str
            
            pin_schema = PinSchema(
                prompt_id=prompt_id,
                image_url=pin_data["image_url"],
                pin_url=pin_data["pin_url"],
                title=pin_data.get("title"),
                description=pin_data.get("description"),
                status="ready",  # Set initial status as ready for AI validation
                metadata=PinMetadata(collected_at=collected_at)
            )
            pin_docs.append(pin_schema.dict())
        
        return cls.create_many(pin_docs)
    
    @classmethod
    def update_pin_ai_validation(cls, pin_id: ObjectId, match_score: float, status: str, ai_explanation: str) -> bool:
        """
        Update pin with AI validation results
        
        Args:
            pin_id (ObjectId): Pin ID
            match_score (float): AI match score (0.0-1.0)
            status (str): AI status ("approved" | "disqualified")
            ai_explanation (str): AI explanation
            
        Returns:
            bool: True if updated successfully
        """
        return cls.update_by_id(
            pin_id,
            {
                "$set": {
                    "match_score": match_score,
                    "status": status,
                    "ai_explanation": ai_explanation
                }
            }
        )
    
    @classmethod
    def update_pin_title(cls, pin_id: ObjectId, title: str) -> bool:
        """
        Update pin title (used during enrichment)
        
        Args:
            pin_id (ObjectId): Pin ID
            title (str): Pin title
            
        Returns:
            bool: True if updated successfully
        """
        return cls.update_by_id(pin_id, {"$set": {"title": title}})
    
    @classmethod
    def get_pins_by_prompt(cls, prompt_id: ObjectId) -> List[Dict]:
        """
        Get all pins for a prompt
        
        Args:
            prompt_id (ObjectId): Prompt ID
            
        Returns:
            List[Dict]: List of pin documents
        """
        return cls.get_many({"prompt_id": prompt_id})
    
    @classmethod
    def get_pins_by_status(cls, prompt_id: ObjectId, status: str) -> List[Dict]:
        """
        Get pins by status for a specific prompt
        
        Args:
            prompt_id (ObjectId): Prompt ID
            status (str): Pin status ("approved" | "disqualified")
            
        Returns:
            List[Dict]: List of pin documents
        """
        return cls.get_many({"prompt_id": prompt_id, "status": status})
    
    @classmethod
    def get_pin(cls, pin_id: ObjectId) -> Optional[Dict]:
        """
        Get pin by ID
        
        Args:
            pin_id (ObjectId): Pin ID
            
        Returns:
            Optional[Dict]: Pin document or None
        """
        return cls.get_by_id(pin_id)
    
    @classmethod
    def count_pins_by_prompt(cls, prompt_id: ObjectId) -> int:
        """
        Count total pins for a prompt
        
        Args:
            prompt_id (ObjectId): Prompt ID
            
        Returns:
            int: Number of pins
        """
        return cls.count({"prompt_id": prompt_id})
