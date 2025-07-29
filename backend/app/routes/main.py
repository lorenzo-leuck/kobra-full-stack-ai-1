from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from bson import ObjectId
import asyncio

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
        
        try:
            # Send initial status update
            await orchestrator.setStatus("running", "Starting Pinterest workflow", 5.0)
            
            pinterest_result = await orchestrator.run_pinterest_workflow(
                num_images=20,
                headless=True
            )
            print(f"📌 Pinterest workflow result: {pinterest_result}")
            
        except Exception as pinterest_error:
            print(f"💥 Pinterest workflow failed with exception: {type(pinterest_error).__name__}: {str(pinterest_error)}")
            import traceback
            print(f"📋 Pinterest workflow traceback:")
            traceback.print_exc()
            
            # Update status to show error
            await orchestrator.setStatus("failed", f"Pinterest workflow failed: {str(pinterest_error)}", 0.0)
            PromptDB.update_prompt_status(ObjectId(prompt_id), "error")
            return
        
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
async def create_prompt(prompt_request: PromptRequest, background_tasks: BackgroundTasks):
    """
    Submit a new prompt and start workflow in background.
    Returns immediately with prompt_id.
    """
    try:
        # Create prompt in database
        prompt_id = PromptDB.create_prompt(prompt_request.text)
        
        # Add workflow to background tasks
        background_tasks.add_task(
            run_complete_workflow_background,
            prompt_request.text,
            str(prompt_id)
        )
        
        return PromptResponse(
            prompt_id=str(prompt_id),
            status="pending",
            message="Workflow started in background"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create prompt: {str(e)}"
        )

# WebSocket endpoint removed - now using polling for status updates

@router.get("/prompts/{prompt_id}/status")
async def get_prompt_status(prompt_id: str):
    """
    Get current status of a prompt workflow.
    """
    try:
        from ..database.prompts import PromptDB
        from ..database.sessions import SessionDB
        from ..database.status import StatusDB
        
        # Get prompt
        prompt_doc = PromptDB.get_prompt_by_id(ObjectId(prompt_id))
        if not prompt_doc:
            raise HTTPException(status_code=404, detail="Prompt not found")
            
        # Get sessions
        sessions = SessionDB.get_sessions_by_prompt(ObjectId(prompt_id))
        
        # Get status
        status_data = StatusDB.get_workflow_progress(prompt_id)
        
        # Map sessions to frontend expected format
        sessions_formatted = []
        for session in sessions:
            stage_id = session['stage']
            
            sessions_formatted.append({
                '_id': str(session['_id']),
                'prompt_id': prompt_id,
                'stage': stage_id,
                'status': session['status'],
                'timestamp': session.get('timestamp', ''),
                'logs': session.get('log', [])
            })
            
        # Calculate overall progress
        overall_progress = status_data.get('progress', 0) if status_data else 0
            
        return {
            'prompt': {
                '_id': prompt_id,
                'text': prompt_doc['text'],
                'status': prompt_doc['status'],
                'created_at': prompt_doc.get('created_at', '')
            },
            'sessions': sessions_formatted,
            'overall_progress': overall_progress,
            'current_stage': status_data.get('overall_status', 'pending') if status_data else 'pending'
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get prompt status: {str(e)}"
        )

@router.get("/prompts/{prompt_id}/pins")
async def get_prompt_pins(prompt_id: str):
    """
    Get validated pins for a prompt.
    """
    try:
        from ..database.prompts import PromptDB
        from ..database.pins import PinDB
        
        # Get prompt
        prompt_doc = PromptDB.get_prompt_by_id(ObjectId(prompt_id))
        if not prompt_doc:
            raise HTTPException(status_code=404, detail="Prompt not found")
            
        # Get pins
        pins = PinDB.get_pins_by_prompt(ObjectId(prompt_id))
        
        # Format pins for frontend
        formatted_pins = []
        for pin in pins:
            formatted_pin = {
                '_id': str(pin['_id']),
                'image_url': pin.get('image_url'),
                'pin_url': pin.get('pin_url'),
                'title': pin.get('title', ''),
                'description': pin.get('description', ''),
                'match_score': pin.get('match_score', 0.0),
                'status': pin.get('status', 'pending'),
                'ai_explanation': pin.get('ai_explanation', ''),
                'metadata': pin.get('metadata', {})
            }
            formatted_pins.append(formatted_pin)
            
        # Calculate statistics
        total_count = len(formatted_pins)
        approved_count = len([p for p in formatted_pins if p['status'] == 'approved'])
        disqualified_count = len([p for p in formatted_pins if p['status'] == 'disqualified'])
        avg_score = sum(p['match_score'] for p in formatted_pins) / total_count if total_count > 0 else 0.0
        
        return {
            'pins': formatted_pins,
            'total_count': total_count,
            'approved_count': approved_count,
            'disqualified_count': disqualified_count,
            'avg_score': round(avg_score, 2)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get prompt pins: {str(e)}"
        )