from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from typing import Any

class PyObjectId(str):
    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        return {"type": "string"}
        
    def __repr__(self):
        return str(self)
        
    def __str__(self):
        return str(self)
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.to_string_ser_schema(),
        )
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return str(ObjectId(v))
            raise ValueError("Invalid ObjectId format")
        raise ValueError("Invalid ObjectId type")

# Use field_serializer instead of ENCODERS_BY_TYPE for Pydantic v2 compatibility

class PromptBase(BaseModel):
    text: str

class PromptCreate(PromptBase):
    pass

class Prompt(PromptBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, completed, error
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "text": "cozy industrial home office",
                "created_at": "2023-01-01T00:00:00",
                "status": "pending"
            }
        }
    }
