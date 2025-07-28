from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from .base import BaseDB


class SessionSchema(BaseModel):
    """Pydantic schema for session documents"""
    prompt_id: ObjectId
    stage: str  # "warmup" | "scraping" | "validation"
    status: str = "pending"  # "pending" | "completed" | "failed"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    log: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }


class SessionDB(BaseDB):
    """Database operations for sessions collection"""
    
    collection_name = "sessions"
    
    @classmethod
    def create_session(cls, prompt_id: ObjectId, stage: str) -> ObjectId:
        """
        Create a new session document
        
        Args:
            prompt_id (ObjectId): Associated prompt ID
            stage (str): Initial stage ("warmup" | "scraping" | "validation")
            
        Returns:
            ObjectId: The created session ID
        """
        session_schema = SessionSchema(prompt_id=prompt_id, stage=stage)
        session_doc = session_schema.dict()
        return cls.create_one(session_doc)
    
    @classmethod
    def update_session_stage(cls, session_id: ObjectId, stage: str) -> bool:
        """
        Update session stage
        
        Args:
            session_id (ObjectId): Session ID
            stage (str): New stage ("warmup" | "scraping" | "validation")
            
        Returns:
            bool: True if updated successfully
        """
        return cls.update_by_id(
            session_id,
            {
                "$set": {
                    "stage": stage,
                    "timestamp": datetime.utcnow()
                }
            }
        )
    
    @classmethod
    def update_session_status(cls, session_id: ObjectId, status: str) -> bool:
        """
        Update session status
        
        Args:
            session_id (ObjectId): Session ID
            status (str): New status ("pending" | "completed" | "failed")
            
        Returns:
            bool: True if updated successfully
        """
        return cls.update_by_id(
            session_id,
            {
                "$set": {
                    "status": status,
                    "timestamp": datetime.utcnow()
                }
            }
        )
    
    @classmethod
    def add_session_log(cls, session_id: ObjectId, log_message: str) -> bool:
        """
        Add log message to session
        
        Args:
            session_id (ObjectId): Session ID
            log_message (str): Log message to add
            
        Returns:
            bool: True if added successfully
        """
        return cls.update_by_id(
            session_id,
            {
                "$push": {"log": log_message},
                "$set": {"timestamp": datetime.utcnow()}
            }
        )
    
    @classmethod
    def get_session(cls, session_id: ObjectId) -> Optional[dict]:
        """
        Get session by ID
        
        Args:
            session_id (ObjectId): Session ID
            
        Returns:
            Optional[dict]: Session document or None
        """
        return cls.get_by_id(session_id)
    
    @classmethod
    def get_sessions_by_prompt(cls, prompt_id: ObjectId) -> List[dict]:
        """
        Get all sessions for a prompt
        
        Args:
            prompt_id (ObjectId): Prompt ID
            
        Returns:
            List[dict]: List of session documents
        """
        return cls.get_many({"prompt_id": prompt_id}, sort_by="timestamp", sort_order=1)
