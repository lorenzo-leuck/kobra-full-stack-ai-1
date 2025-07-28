from fastapi import APIRouter, HTTPException
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
    print(f"🚀 Starting workflow for prompt: '{prompt_text}' (ID: {prompt_id})")
    
    try:
        # Create workflow orchestrator
        print(f"📋 Creating WorkflowOrchestrator...")
        orchestrator = WorkflowOrchestrator(prompt=prompt_text)
        orchestrator.prompt_id = ObjectId(prompt_id)
        print(f"✅ WorkflowOrchestrator created successfully")
        
        # Phase 1: Pinterest workflow
        print(f"📌 Starting Pinterest workflow phase...")
        pinterest_result = await orchestrator.run_pinterest_workflow(
            num_images=20,
            headless=True
        )
        print(f"📌 Pinterest workflow result: {pinterest_result}")
        
        if not pinterest_result.get('success'):
            print(f"❌ Pinterest workflow failed: {pinterest_result.get('error', 'Unknown error')}")
            PromptDB.update_prompt_status(ObjectId(prompt_id), "error")
            return
        
        print(f"✅ Pinterest workflow completed successfully")
        
        # Phase 2: AI validation workflow
        print(f"🤖 Starting AI validation workflow phase...")
        ai_result = await orchestrator.run_ai_validation_workflow(ObjectId(prompt_id))
        print(f"🤖 AI validation result: {ai_result}")
        
        if ai_result.get('success'):
            print(f"✅ Complete workflow finished successfully")
            PromptDB.update_prompt_status(ObjectId(prompt_id), "completed")
        else:
            print(f"❌ AI validation failed: {ai_result.get('error', 'Unknown error')}")
            PromptDB.update_prompt_status(ObjectId(prompt_id), "error")
            
    except Exception as e:
        print(f"💥 Workflow exception: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"📋 Full traceback:")
        traceback.print_exc()
        PromptDB.update_prompt_status(ObjectId(prompt_id), "error")

@router.post("/prompts", response_model=PromptResponse)
async def create_prompt(prompt_request: PromptRequest):
    """
    Submit a new prompt and run the complete workflow.
    Returns after workflow completion.
    """
    try:
        # Create prompt in database
        prompt_id = PromptDB.create_prompt(prompt_request.text)
        
        # Run workflow directly (not in background)
        await run_complete_workflow_background(
            prompt_request.text,
            str(prompt_id)
        )
        
        return PromptResponse(
            prompt_id=str(prompt_id),
            status="completed",
            message="Workflow completed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create prompt: {str(e)}"
        )