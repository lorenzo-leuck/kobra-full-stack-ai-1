from pymongo import MongoClient
from app.config import settings
from functools import lru_cache
from datetime import datetime
from typing import List, Dict, Optional, Any
from bson import ObjectId

@lru_cache()
def get_mongodb_client():
    return MongoClient(settings.MONGODB_URL)

def get_database():
    client = get_mongodb_client()
    return client[settings.MONGODB_DB_NAME]


class BaseDB:
    """Base database operations class with common CRUD methods"""
    
    collection_name: str = None
    
    @classmethod
    def get_collection(cls):
        """Get the MongoDB collection for this class"""
        if not cls.collection_name:
            raise NotImplementedError("collection_name must be defined")
        db = get_database()
        return db[cls.collection_name]
    
    @classmethod
    def create_one(cls, document: Dict) -> ObjectId:
        """
        Create a single document
        
        Args:
            document (Dict): Document to create
            
        Returns:
            ObjectId: The created document ID
        """
        collection = cls.get_collection()
        result = collection.insert_one(document)
        return result.inserted_id
    
    @classmethod
    def create_many(cls, documents: List[Dict]) -> List[ObjectId]:
        """
        Create multiple documents
        
        Args:
            documents (List[Dict]): Documents to create
            
        Returns:
            List[ObjectId]: List of created document IDs
        """
        if not documents:
            return []
        collection = cls.get_collection()
        result = collection.insert_many(documents)
        return result.inserted_ids
    
    @classmethod
    def get_one(cls, filter_dict: Dict) -> Optional[Dict]:
        """
        Get a single document by filter
        
        Args:
            filter_dict (Dict): MongoDB filter
            
        Returns:
            Optional[Dict]: Document or None
        """
        collection = cls.get_collection()
        return collection.find_one(filter_dict)
    
    @classmethod
    def get_by_id(cls, doc_id: ObjectId) -> Optional[Dict]:
        """
        Get document by ID
        
        Args:
            doc_id (ObjectId): Document ID
            
        Returns:
            Optional[Dict]: Document or None
        """
        return cls.get_one({"_id": doc_id})
    
    @classmethod
    def get_many(cls, filter_dict: Dict = None, sort_by: str = None, sort_order: int = 1, limit: int = None) -> List[Dict]:
        """
        Get multiple documents
        
        Args:
            filter_dict (Dict): MongoDB filter (default: {})
            sort_by (str): Field to sort by
            sort_order (int): 1 for ascending, -1 for descending
            limit (int): Maximum number of documents to return
            
        Returns:
            List[Dict]: List of documents
        """
        collection = cls.get_collection()
        cursor = collection.find(filter_dict or {})
        
        if sort_by:
            cursor = cursor.sort(sort_by, sort_order)
        
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    @classmethod
    def update_one(cls, filter_dict: Dict, update_dict: Dict) -> bool:
        """
        Update a single document
        
        Args:
            filter_dict (Dict): MongoDB filter
            update_dict (Dict): Update operations
            
        Returns:
            bool: True if document was modified
        """
        collection = cls.get_collection()
        result = collection.update_one(filter_dict, update_dict)
        return result.modified_count > 0
    
    @classmethod
    def update_by_id(cls, doc_id: ObjectId, update_dict: Dict) -> bool:
        """
        Update document by ID
        
        Args:
            doc_id (ObjectId): Document ID
            update_dict (Dict): Update operations
            
        Returns:
            bool: True if document was modified
        """
        return cls.update_one({"_id": doc_id}, update_dict)
    
    @classmethod
    def delete_one(cls, filter_dict: Dict) -> bool:
        """
        Delete a single document
        
        Args:
            filter_dict (Dict): MongoDB filter
            
        Returns:
            bool: True if document was deleted
        """
        collection = cls.get_collection()
        result = collection.delete_one(filter_dict)
        return result.deleted_count > 0
    
    @classmethod
    def delete_by_id(cls, doc_id: ObjectId) -> bool:
        """
        Delete document by ID
        
        Args:
            doc_id (ObjectId): Document ID
            
        Returns:
            bool: True if document was deleted
        """
        return cls.delete_one({"_id": doc_id})
    
    @classmethod
    def count(cls, filter_dict: Dict = None) -> int:
        """
        Count documents
        
        Args:
            filter_dict (Dict): MongoDB filter (default: {})
            
        Returns:
            int: Number of documents
        """
        collection = cls.get_collection()
        return collection.count_documents(filter_dict or {})
