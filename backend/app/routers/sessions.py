from fastapi import APIRouter, HTTPException, Depends
from typing import List

from bson import ObjectId
import pymongo

from app.models.prompt import PyObjectId
from app.models.session import Session
from app.database import get_database

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"]
)

@router.get("/prompt/{prompt_id}", response_model=List[Session])
def get_sessions_by_prompt(
    prompt_id: str,
    db = Depends(get_database)
):
    try:
        try:
            prompt_id = ObjectId(prompt_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid prompt ID format") from exc
        object_id = PyObjectId(prompt_id)
        sessions = list(db.sessions.find({"prompt_id": object_id}))
        return [Session(**session) for session in sessions]
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc

@router.get("/{session_id}", response_model=Session)
def get_session(
    session_id: str,
    db = Depends(get_database)
):
    try:
        try:
            session_id = ObjectId(session_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid session ID format") from exc
        object_id = PyObjectId(session_id)
        session = db.sessions.find_one({"_id": object_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return Session(**session)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc
