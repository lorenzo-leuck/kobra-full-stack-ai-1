from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from .base import BaseDB


class PromptSchema(BaseModel):
    """Pydantic schema for prompt documents"""
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # "pending" | "completed" | "error"
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }


class PromptDB(BaseDB):
    """Database operations for prompts collection"""
    
    collection_name = "prompts"
    
    @classmethod
    def create_prompt(cls, text: str) -> ObjectId:
        """
        Create a new prompt document
        
        Args:
            text (str): The prompt text
            
        Returns:
            ObjectId: The created prompt ID
        """
        prompt_schema = PromptSchema(text=text)
        prompt_doc = prompt_schema.dict()
        return cls.create_one(prompt_doc)
    
    @classmethod
    def update_prompt_status(cls, prompt_id: ObjectId, status: str) -> bool:
        """
        Update prompt status
        
        Args:
            prompt_id (ObjectId): Prompt ID
            status (str): New status ("pending" | "completed" | "error")
            
        Returns:
            bool: True if updated successfully
        """
        return cls.update_by_id(prompt_id, {"$set": {"status": status}})
    
    @classmethod
    def get_prompt(cls, prompt_id: ObjectId) -> Optional[dict]:
        """
        Get prompt by ID
        
        Args:
            prompt_id (ObjectId): Prompt ID
            
        Returns:
            Optional[dict]: Prompt document or None
        """
        return cls.get_by_id(prompt_id)
    
    @classmethod
    def get_prompts_by_status(cls, status: str) -> List[dict]:
        """
        Get prompts by status
        
        Args:
            status (str): Status to filter by
            
        Returns:
            List[dict]: List of prompt documents
        """
        return cls.get_many({"status": status}, sort_by="created_at", sort_order=-1)
