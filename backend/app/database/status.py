from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field
try:
    from bson import ObjectId
except ImportError:
    # Fallback for environments without pymongo
    ObjectId = str
from .base import BaseDB


class StatusSchema(BaseModel):
    """Schema for workflow status tracking"""
    prompt_id: str  # Will be converted to ObjectId in database
    overall_status: str = "pending"  # pending, running, completed, failed
    current_step: int = 0
    total_steps: int = 0
    progress: float = 0.0  # 0.0 to 100.0
    messages: List[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class StatusDB(BaseDB):
    """Database operations for workflow status tracking"""
    
    collection_name = "status"
    

    
    @classmethod
    def create_workflow_status(cls, prompt_id: str) -> str:
        """Create a new workflow status document (only if one doesn't exist)"""
        prompt_id_obj = ObjectId(prompt_id)
        
        # Check if status document already exists
        existing = cls.get_one({"prompt_id": prompt_id_obj})
        if existing:
            return str(existing["_id"])
        
        # Clean up any duplicate status documents for this prompt_id
        cls.collection.delete_many({"prompt_id": prompt_id_obj})
        
        status_data = {
            "prompt_id": prompt_id_obj,
            "overall_status": "pending",
            "current_step": 0,
            "total_steps": 0,  # Will be updated as messages are added
            "progress": 0.0,
            "messages": [],
            "started_at": datetime.now(),
            "completed_at": None
        }
        
        result = cls.create_one(status_data)
        return str(result)
    
    @classmethod
    def update_step_status(cls, prompt_id: str, status: str, message: str = None, progress: float = None) -> bool:
        """Update workflow status"""
        # First, get current document to calculate proper step counts
        current_doc = cls.get_one({"prompt_id": ObjectId(prompt_id)})
        if not current_doc:
            return False
        
        update_data = {
            "overall_status": status
        }
        
        if message:
            # Add message and increment current step
            current_messages = current_doc.get("messages", [])
            current_step = current_doc.get("current_step", 0)
            total_steps = current_doc.get("total_steps", 0)
            
            update_data["$push"] = {"messages": message}
            
            # Increment current step
            new_current_step = current_step + 1
            update_data["current_step"] = new_current_step
            
            # Only update total_steps if it's less than current_step (to handle dynamic workflows)
            if total_steps < new_current_step:
                update_data["total_steps"] = new_current_step
        
        if progress is not None:
            update_data["progress"] = progress
        
        if status == "completed":
            update_data["completed_at"] = datetime.now()
        
        # Build the update query
        if "$push" in update_data:
            result = cls.update_one(
                {"prompt_id": ObjectId(prompt_id)},
                {
                    "$set": {k: v for k, v in update_data.items() if k != "$push"},
                    "$push": update_data["$push"]
                }
            )
        else:
            result = cls.update_one(
                {"prompt_id": ObjectId(prompt_id)},
                {"$set": update_data}
            )
        
        return result  # cls.update_one already returns boolean
    
    @classmethod
    def get_workflow_progress(cls, prompt_id: str) -> Dict:
        """Get workflow progress"""
        status_doc = cls.get_one({"prompt_id": ObjectId(prompt_id)})
        if not status_doc:
            return {}
        
        return {
            "overall_status": status_doc["overall_status"],
            "current_step": status_doc["current_step"],
            "total_steps": status_doc["total_steps"],
            "progress": status_doc["progress"],
            "messages": status_doc["messages"],
            "started_at": status_doc["started_at"],
            "completed_at": status_doc.get("completed_at")
        }
    
    @classmethod
    def cleanup_duplicate_status_documents(cls, prompt_id: str) -> int:
        """Remove duplicate status documents for a prompt, keeping the most complete one"""
        # Find all status documents for this prompt
        collection = cls.get_collection()
        all_docs = list(collection.find({"prompt_id": ObjectId(prompt_id)}))
        
        if len(all_docs) <= 1:
            return 0  # No duplicates
        
        # Sort by number of messages (most complete first), then by started_at (newest first)
        all_docs.sort(key=lambda x: (len(x.get("messages", [])), x.get("started_at", datetime.min)), reverse=True)
        
        # Keep the first one (most complete), delete the rest
        keep_doc_id = all_docs[0]["_id"]
        delete_ids = [doc["_id"] for doc in all_docs[1:]]
        
        if delete_ids:
            collection = cls.get_collection()
            result = collection.delete_many({"_id": {"$in": delete_ids}})
            print(f"Kept status document {keep_doc_id}, deleted {result.deleted_count} duplicates")
            return result.deleted_count
        
        return 0
