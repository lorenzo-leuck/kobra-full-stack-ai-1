from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel
from bson import ObjectId
import asyncio

from ..services.workflow.main import WorkflowOrchestrator
from ..database.prompts import PromptDB
from ..services.websocket import websocket_manager

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

@router.websocket("/ws/{prompt_id}")
async def websocket_endpoint(websocket: WebSocket, prompt_id: str):
    """
    WebSocket endpoint for real-time status updates for a specific prompt.
    """
    try:
        # Connect to WebSocket manager
        await websocket_manager.connect(websocket, prompt_id)
        
        print(f"📡 WebSocket connected for prompt {prompt_id}")
        
        # Keep connection alive and handle disconnection
        while True:
            try:
                # Wait for any message (ping/pong to keep alive)
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"📡 WebSocket error: {e}")
                break
                
    except Exception as e:
        print(f"📡 WebSocket connection error: {e}")
    finally:
        # Disconnect from WebSocket manager
        websocket_manager.disconnect(websocket, prompt_id)
        print(f"📡 WebSocket disconnected for prompt {prompt_id}")

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
        status_docs = StatusDB.get_status_by_prompt_id(prompt_id)
        
        # Map sessions to frontend expected format
        stages = []
        for session in sessions:
            stage_id = session['stage']
            stage_name = {
                'warmup': 'Pinterest Warm-up',
                'scraping': 'Image Collection', 
                'validation': 'AI Validation'
            }.get(stage_id, stage_id.title())
            
            stages.append({
                'id': stage_id,
                'name': stage_name,
                'status': session['status'],
                'logs': session.get('log', [])
            })
            
        # Calculate overall progress
        overall_progress = 0
        if status_docs:
            status_doc = status_docs[0]
            overall_progress = status_doc.get('progress', 0)
            
        return {
            'prompt_id': prompt_id,
            'status': prompt_doc['status'],
            'overall_progress': overall_progress,
            'stages': stages
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
            
        return {
            'prompt_id': prompt_id,
            'original_prompt': prompt_doc['text'],
            'pins': formatted_pins
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get prompt pins: {str(e)}"
        )