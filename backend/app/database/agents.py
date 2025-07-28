from datetime import datetime
from typing import Dict, Optional
from bson import ObjectId
from pydantic import BaseModel

from .base import BaseDB


class AgentMetadata(BaseModel):
    created_at: datetime
    updated_at: datetime
    version: str = "1.0"


class AgentSchema(BaseModel):
    title: str
    model: str
    system_prompt: str
    user_prompt_template: str
    temperature: float = 0.7  # Default temperature for AI responses
    metadata: AgentMetadata
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }


class AgentDB(BaseDB):
    collection_name = "agents"
    
    @classmethod
    def get_agent_by_title(cls, title: str) -> Optional[Dict]:
        """
        Get agent configuration by title
        
        Args:
            title (str): Agent title (e.g., "pin-evaluator")
            
        Returns:
            Optional[Dict]: Agent document or None if not found
        """
        return cls.get_collection().find_one({"title": title})
    
    @classmethod
    def create_or_update_agent(cls, title: str, model: str, system_prompt: str, 
                              user_prompt_template: str, temperature: float = 0.7) -> ObjectId:
        """
        Create or update an agent configuration
        
        Args:
            title (str): Agent title
            model (str): Model name (e.g., "gpt-4o")
            system_prompt (str): System prompt for the agent
            user_prompt_template (str): Template for user prompts
            temperature (float): Temperature for AI responses (0.0-2.0)
            
        Returns:
            ObjectId: Agent document ID
        """
        now = datetime.utcnow()
        
        # Check if agent exists
        existing_agent = cls.get_agent_by_title(title)
        
        if existing_agent:
            # Update existing agent
            update_data = {
                "model": model,
                "system_prompt": system_prompt,
                "user_prompt_template": user_prompt_template,
                "temperature": temperature,
                "metadata.updated_at": now
            }
            cls.get_collection().update_one(
                {"title": title},
                {"$set": update_data}
            )
            return existing_agent["_id"]
        else:
            # Create new agent
            agent_schema = AgentSchema(
                title=title,
                model=model,
                system_prompt=system_prompt,
                user_prompt_template=user_prompt_template,
                temperature=temperature,
                metadata=AgentMetadata(
                    created_at=now,
                    updated_at=now
                )
            )
            result = cls.get_collection().insert_one(agent_schema.dict())
            return result.inserted_id
    
    @classmethod
    def list_agents(cls) -> list:
        """
        List all agents
        
        Returns:
            list: List of agent documents
        """
        return list(cls.get_collection().find())
