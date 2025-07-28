from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from bson import ObjectId

from ..services.workflow.main import WorkflowOrchestrator
from ..database.prompts import PromptDB

router = APIRouter(
    prefix="/api",
    tags=["prompts"]
)

class PromptRequest(BaseModel):
    text: str

class PromptResponse(BaseModel):
    prompt_id: str
    status: str
    message: str

async def run_complete_workflow_background(prompt_text: str, prompt_id: str):
    """
    Run the complete workflow in background:
    1. Pinterest scraping + enrichment
    2. AI validation
    """
    try:
        # Create workflow orchestrator
        orchestrator = WorkflowOrchestrator(prompt=prompt_text)
        orchestrator.prompt_id = ObjectId(prompt_id)
        
        # Phase 1: Pinterest workflow
        pinterest_result = await orchestrator.run_pinterest_workflow(
            num_images=20,
            headless=True
        )
        
        if not pinterest_result.get('success'):
            # Update prompt status to error
            PromptDB.update_prompt_status(ObjectId(prompt_id), "error")
            return
        
        # Phase 2: AI validation workflow
        ai_result = await orchestrator.run_ai_validation_workflow(ObjectId(prompt_id))
        
        if ai_result.get('success'):
            # Update prompt status to completed
            PromptDB.update_prompt_status(ObjectId(prompt_id), "completed")
        else:
            # Update prompt status to error
            PromptDB.update_prompt_status(ObjectId(prompt_id), "error")
            
    except Exception as e:
        print(f"Workflow error: {e}")
        # Update prompt status to error
        PromptDB.update_prompt_status(ObjectId(prompt_id), "error")

@router.post("/prompts", response_model=PromptResponse)
async def create_prompt(prompt_request: PromptRequest, background_tasks: BackgroundTasks):
    """
    Submit a new prompt and start the complete workflow in background.
    Returns immediately with prompt_id for status tracking.
    """
    try:
        # Create prompt in database
        prompt_id = PromptDB.create_prompt(prompt_request.text)
        
        # Add background task to run complete workflow
        background_tasks.add_task(
            run_complete_workflow_background,
            prompt_request.text,
            str(prompt_id)
        )
        
        return PromptResponse(
            prompt_id=str(prompt_id),
            status="pending",
            message="Workflow started successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create prompt: {str(e)}"
        )