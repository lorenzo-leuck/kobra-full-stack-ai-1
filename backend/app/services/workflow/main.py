import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from bson import ObjectId

from ..pinterest.warmup import PinterestWarmup
from ..pinterest.pins import PinterestPins
from ..ai.evaluator import AIEvaluator


class WorkflowOrchestrator:
    """
    Main workflow orchestrator for the application.
    Manages different service workflows (Pinterest, AI agents, etc.).
    Uses MongoDB for persistence through database layer.
    """
    
    def __init__(self, prompt: str):
        self.prompt = prompt
        
        # Will be set when database is imported
        self.prompt_id = None
        
        # Current session tracking
        self.current_session_id = None
        
        # Status tracking
        self.current_status_id = None
    
    def _create_prompt_in_db(self):
        """Create prompt in database - called by specific workflow methods"""
        if not self.prompt_id:
            from ...database.prompts import PromptDB
            self.prompt_id = PromptDB.create_prompt(self.prompt)
        return self.prompt_id
    
    def _log(self, message: str) -> None:
        """Add log message to current session"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        if self.current_session_id:
            from ...database.sessions import SessionDB
            SessionDB.add_session_log(self.current_session_id, log_entry)
    
    async def setStatus(self, status: str, message: str = None, progress_percentage: float = None) -> None:
        """
        Update workflow status and send WebSocket update
        """
        if not self.prompt_id:
            return
        
        try:
            from ...database.status import StatusDB
            from ..websocket import websocket_manager
            
            # Update status in database
            StatusDB.update_step_status(
                prompt_id=str(self.prompt_id),
                status=status,
                message=message,
                progress=progress_percentage
            )
            
            self._log(f"Status updated: {status} - {message}")
            
            # Send WebSocket update
            status_data = {
                "status": status,
                "message": message,
                "progress_percentage": progress_percentage,
                "prompt_id": str(self.prompt_id)
            }
            
            await websocket_manager.send_status_update(
                prompt_id=str(self.prompt_id),
                status_data=status_data
            )
            
        except Exception as e:
            self._log(f"Failed to update status: {e}")
    
    def _initialize_workflow_status(self) -> str:
        """Initialize workflow status tracking"""
        try:
            from ...database.status import StatusDB
            
            self.current_status_id = StatusDB.create_workflow_status(
                prompt_id=str(self.prompt_id)
            )
            
            return self.current_status_id
            
        except Exception as e:
            self._log(f"Failed to initialize status tracking: {e}")
            return None
    
    async def run_pinterest_workflow(self, num_images: int = 20, headless: bool = True, 
                                   username: Optional[str] = None, password: Optional[str] = None) -> Dict:
        """
        Execute Pinterest-specific workflow: warmup -> scraping -> enrichment
        
        Args:
            num_images (int): Number of images to scrape
            headless (bool): Run browser in headless mode
            username (str): Pinterest username (optional, uses env if not provided)
            password (str): Pinterest password (optional, uses env if not provided)
            
        Returns:
            Dict: Complete workflow results with prompt_id and status
        """
        # Create prompt in database
        self._create_prompt_in_db()
        
        # Initialize workflow status tracking
        # Initialize status tracking
        self._initialize_workflow_status()
        
        # Initialize Pinterest-specific components
        pinterest_workflow = PinterestWorkflowHandler(
            prompt=self.prompt,
            prompt_id=self.prompt_id,
            username=username,
            password=password
        )
        
        # Set current session for logging
        self.current_session_id = pinterest_workflow.current_session_id
        
        # Pass status tracking to Pinterest workflow
        pinterest_workflow.orchestrator = self
        
        # Run Pinterest workflow
        return await pinterest_workflow.run_complete_workflow(num_images, headless)
    
    async def run_ai_validation_workflow(self, prompt_id: ObjectId) -> Dict:
        """
        Execute AI validation workflow for pins with status "ready"
        
        Args:
            prompt_id (ObjectId): Prompt ID to validate pins for
            
        Returns:
            Dict: AI validation results with counts and status
        """
        try:
            # Import database classes
            from ...database.prompts import PromptDB
            from ...database.sessions import SessionDB
            from ...database.pins import PinDB
            
            # Get prompt to validate it exists
            prompt_doc = PromptDB.get_prompt_by_id(prompt_id)
            if not prompt_doc:
                return {
                    "success": False,
                    "error": f"Prompt not found: {prompt_id}"
                }
            
            # Set prompt_id for status tracking (reuse existing status document)
            self.prompt_id = prompt_id
            
            # Find existing status document - don't create a new one
            from ...database.status import StatusDB
            existing_status = StatusDB.get_workflow_progress(str(prompt_id))
            if existing_status:
                # Reuse existing status tracking
                self.current_status_id = str(prompt_id)  # Use prompt_id as identifier
            else:
                # If no existing status, initialize one (shouldn't happen in normal flow)
                self.current_status_id = self._initialize_workflow_status()
            
            # Create AI validation session
            session_id = SessionDB.create_session(prompt_id, "validation")
            self.current_session_id = session_id
            
            # Step: Initialization
            self.setStatus("running", "Initializing AI validation system")
            self._log("=== AI VALIDATION PHASE ===")
            self._log(f"Starting AI validation for prompt: {prompt_doc['text']}")
            
            # Initialize AI evaluator
            evaluator = AIEvaluator()
            self.setStatus("completed", "AI validation system initialized", progress_percentage=100.0)
            
            # Step: Evaluation
            self.setStatus("running", "Evaluating pins with AI model")
            result = await evaluator.evaluate_pins_for_prompt(prompt_id)
            self.setStatus("completed", f"Evaluated {result.get('evaluated_count', 0)} pins", progress_percentage=100.0)
            
            # Step: Completion
            if result.get("success"):
                self.setStatus("running", "Finalizing validation results")
                self._log(f"AI validation completed successfully")
                self._log(f"Results: {result['approved_count']} approved, {result['disqualified_count']} disqualified")
                
                # Update prompt status to completed
                PromptDB.update_prompt_status(prompt_id, "completed")
                SessionDB.update_session_status(session_id, "completed")
                
                self.setStatus("completed", f"Validation completed: {result['approved_count']} approved, {result['disqualified_count']} disqualified", 
                             progress_percentage=100.0)
                
                self._log(f"AI validation completed: {result['evaluated_count']} pins evaluated")
                self._log(f"Results: {result['approved_count']} approved, {result['disqualified_count']} disqualified")
                
                return {
                    "success": True,
                    "prompt_id": str(prompt_id),
                    "message": result["message"],
                    "evaluated_count": result["evaluated_count"],
                    "approved_count": result["approved_count"],
                    "disqualified_count": result["disqualified_count"]
                }
            else:
                # Failed
                self.setStatus("failed", "AI validation failed")
                
                # Update session status to failed
                SessionDB.update_session_status(session_id, "failed")
                PromptDB.update_prompt_status(prompt_id, "error")
                
                return {
                    "success": False,
                    "error": result.get("message", "AI validation failed")
                }
                
        except Exception as e:
            self._log(f"AI validation error: {e}")
            
            if self.current_session_id:
                SessionDB.update_session_status(self.current_session_id, "failed")
            
            return {
                "success": False,
                "error": str(e)
            }


class PinterestWorkflowHandler:
    """
    Pinterest-specific workflow handler.
    Separated from main orchestrator for modularity.
    """
    
    def __init__(self, prompt: str, prompt_id: ObjectId, username: Optional[str] = None, password: Optional[str] = None):
        self.prompt = prompt
        self.prompt_id = prompt_id
        
        # Pinterest credentials
        import os
        self.username = username or os.getenv('PINTEREST_USERNAME')
        self.password = password or os.getenv('PINTEREST_PASSWORD')
        
        # Pinterest session components
        self.warmup_session = None
        self.pins_handler = None
        
        # Current session tracking
        self.current_session_id = None
        
        # Reference to orchestrator for status tracking
        self.orchestrator = None
    
    def _log(self, message: str) -> None:
        """Add log message to current session"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        if self.current_session_id:
            from ...database.sessions import SessionDB
            SessionDB.add_session_log(self.current_session_id, log_entry)
    
    async def initialize_session(self, headless: bool = True) -> bool:
        """
        Initialize Pinterest session and browser
        
        Args:
            headless (bool): Run browser in headless mode
            
        Returns:
            bool: True if initialization successful
        """
        try:
            self._log("Initializing Pinterest session...")
            
            self.warmup_session = PinterestWarmup(
                prompt=self.prompt,
                username=self.username,
                password=self.password
            )
            
            self._log("Starting browser...")
            await self.warmup_session.initialize_browser(headless=headless)
            
            self._log("Attempting Pinterest login...")
            login_success = await self.warmup_session.login()
            
            if not login_success:
                self._log("Pinterest login failed")
                from ...database.prompts import PromptDB
                PromptDB.update_prompt_status(self.prompt_id, "error")
                return False
            
            self._log("Pinterest login successful")
            
            # Initialize pins handler with the same page
            self.pins_handler = PinterestPins(self.warmup_session.page)
            
            return True
            
        except Exception as e:
            self._log(f"Session initialization failed: {e}")
            from ...database.prompts import PromptDB
            PromptDB.update_prompt_status(self.prompt_id, "error")
            return False
    
    async def run_warmup_phase(self) -> bool:
        """
        Execute Pinterest algorithm warmup phase with granular tracking
        
        Returns:
            bool: True if warmup successful
        """
        if not self.warmup_session:
            self._log("Session not initialized")
            return False
        
        # Create warmup session in database
        from ...database.sessions import SessionDB
        self.current_session_id = SessionDB.create_session(self.prompt_id, "warmup")
        
        try:
            # Update status to running
            if self.orchestrator:
                await self.orchestrator.setStatus("running", "Starting Pinterest algorithm warmup")
            
            self._log(f"Starting warmup phase for prompt: '{self.prompt}'")
            
            warmup_success = await self.warmup_session.feed_algorithm()
            
            if warmup_success:
                self._log("Warmup phase completed successfully")
                SessionDB.update_session_status(self.current_session_id, "ready")
                
                # Update status to completed
                if self.orchestrator:
                    await self.orchestrator.setStatus("completed", "Pinterest algorithm warmup completed successfully")
                
                return True
            else:
                self._log("Warmup phase failed - Pinterest algorithm warmup did not complete successfully")
                SessionDB.update_session_status(self.current_session_id, "failed")
                
                # Update status to failed
                if self.orchestrator:
                    await self.orchestrator.setStatus("failed", "Warmup phase failed")
                
                return False
                
        except Exception as e:
            self._log(f"Warmup phase error: {e}")
            SessionDB.update_session_status(self.current_session_id, "failed")
            
            # Update status to failed
            if self.orchestrator:
                await self.orchestrator.setStatus("failed", "Warmup phase error")
            
            return False
    
    async def run_scraping_phase(self, num_images: int = 20) -> List[ObjectId]:
        """
        Execute Pinterest feed scraping phase and save pins to database with granular tracking
        
        Args:
            num_images (int): Number of images to scrape
            
        Returns:
            List[ObjectId]: List of created pin IDs
        """
        if not self.warmup_session or not self.pins_handler:
            self._log("Session not properly initialized")
            return []
        
        # Create new scraping session (separate from warmup session)
        from ...database.sessions import SessionDB
        from ...database.pins import PinDB
        scraping_session_id = SessionDB.create_session(self.prompt_id, "scraping")
        
        # Keep track of scraping session separately
        self.scraping_session_id = scraping_session_id
        
        try:
            # Update status to running
            if self.orchestrator:
                await self.orchestrator.setStatus("running", f"Starting scraping phase - collecting {num_images} pins")
            
            self._log(f"Starting scraping phase - collecting {num_images} pins")
            
            # Navigate to Pinterest feed after warmup
            self._log("Refreshing Pinterest feed...")
            await self.warmup_session.page.goto("https://www.pinterest.com/", timeout=30000)
            await asyncio.sleep(3)
            
            # Scrape pins from feed
            pin_data = await self.pins_handler.scrape_feed(num_images=num_images)
            
            if pin_data:
                self._log(f"Scraping completed - found {len(pin_data)} pins")
                
                # Save pins to database
                pin_ids = PinDB.create_pins_from_scraped_data(self.prompt_id, pin_data)
                self._log(f"Saved {len(pin_ids)} pins to database")
                
                # Update status to completed
                if self.orchestrator:
                    await self.orchestrator.setStatus("completed", f"Scraping completed - found {len(pin_data)} pins", 
                                              progress_percentage=100.0)
                
                SessionDB.update_session_status(self.scraping_session_id, "completed")
                return pin_ids
            else:
                self._log("No pins found during scraping")
                SessionDB.update_session_status(self.scraping_session_id, "failed")
                
                # Update status to failed
                if self.orchestrator:
                    await self.orchestrator.setStatus("failed", "No pins found during scraping")
                
                return []
                
        except Exception as e:
            self._log(f"Scraping phase error: {e}")
            SessionDB.update_session_status(self.scraping_session_id, "failed")
            
            # Update status to failed
            if self.orchestrator:
                await self.orchestrator.setStatus("failed", "Scraping phase error")
            
            return []
    
    async def run_enrichment_phase(self) -> bool:
        """
        Execute title enrichment phase for pins in database with granular tracking
        
        Returns:
            bool: True if enrichment successful
        """
        # Use scraping session for enrichment (enrichment is part of scraping workflow)
        from ...database.sessions import SessionDB
        from ...database.pins import PinDB
        
        # Use scraping session ID if available, otherwise fall back to current session
        enrichment_session_id = getattr(self, 'scraping_session_id', self.current_session_id)
        
        # Get pins from database
        pins = PinDB.get_pins_by_prompt(self.prompt_id)
        if not pins:
            self._log("No pins found in database to enrich")
            
            # Update status to failed
            if self.orchestrator:
                await self.orchestrator.setStatus("failed", "No pins found in database to enrich")
            
            SessionDB.update_session_status(enrichment_session_id, "failed")
            return False
        
        if not self.pins_handler:
            self._log("Pins handler not initialized")
            
            # Update status to failed
            if self.orchestrator:
                await self.orchestrator.setStatus("failed", "Pins handler not initialized")
            
            SessionDB.update_session_status(enrichment_session_id, "failed")
            return False
        
        try:
            # Update status to running
            if self.orchestrator:
                await self.orchestrator.setStatus("running", f"Starting title enrichment for {len(pins)} pins")
            
            self._log(f"Starting title enrichment for {len(pins)} pins")
            
            # Convert database pins to format expected by enrichment
            pin_data_for_enrichment = []
            for pin in pins:
                pin_data = {
                    "image_url": pin["image_url"],
                    "pin_url": pin["pin_url"],
                    "title": pin.get("title"),
                    "description": pin.get("description"),
                    "metadata": pin["metadata"]
                }
                pin_data_for_enrichment.append((pin["_id"], pin_data))
            
            # Enrich titles with progress tracking
            enriched_data = await self.pins_handler.enrich_with_titles([data for _, data in pin_data_for_enrichment])
            
            # Update database with enriched titles
            from ...database.pins import PinDB
            titles_found = 0
            for i, (pin_id, _) in enumerate(pin_data_for_enrichment):
                if i < len(enriched_data) and enriched_data[i].get("title"):
                    # Update the pin in database with the new title
                    PinDB.update_pin_title(pin_id, enriched_data[i]["title"])
                    titles_found += 1
            
            self._log(f"Title enrichment completed - {len(enriched_data)} pins processed")
            
            # Update status to completed
            if self.orchestrator:
                await self.orchestrator.setStatus("completed", f"Title enrichment completed - {len(enriched_data)} pins processed, {titles_found} titles found", 
                                          progress_percentage=100.0)
            
            SessionDB.update_session_status(enrichment_session_id, "completed")
            
            return True
            
        except Exception as e:
            self._log(f"Enrichment phase error: {e}")
            
            # Update status to failed
            if self.orchestrator:
                await self.orchestrator.setStatus("failed", "Enrichment phase error")
            
            SessionDB.update_session_status(enrichment_session_id, "failed")
            return False
    
    async def run_complete_workflow(self, num_images: int = 20, headless: bool = True) -> Dict:
        """
        Execute the complete Pinterest workflow: warmup -> scraping -> enrichment
        
        Args:
            num_images (int): Number of images to scrape
            headless (bool): Run browser in headless mode
            
        Returns:
            Dict: Complete workflow results with prompt_id and status
        """
        from ...database.prompts import PromptDB
        from ...database.pins import PinDB
        
        workflow_result = {
            'success': False,
            'prompt_id': str(self.prompt_id),
            'pin_count': 0
        }
        
        try:
            # Phase 1: Initialize session
            if self.orchestrator:
                await self.orchestrator.setStatus("running", "Initializing Pinterest session and browser", 0.0)
            
            self._log("=== INITIALIZATION PHASE ===")
            init_success = await self.initialize_session(headless=headless)
            if not init_success:
                if self.orchestrator:
                    await self.orchestrator.setStatus("failed", "Session initialization failed")
                workflow_result['error'] = "Session initialization failed"
                return workflow_result
            
            if self.orchestrator:
                await self.orchestrator.setStatus("completed", "Pinterest session initialized successfully", 25.0)
            
            # Phase 2: Warmup (status handled by run_warmup_phase)
            self._log("=== WARMUP PHASE ===")
            warmup_success = await self.run_warmup_phase()
            
            # Phase 3: Scraping (status handled by run_scraping_phase)
            self._log("=== SCRAPING PHASE ===")
            pin_ids = await self.run_scraping_phase(num_images=num_images)
            if not pin_ids:
                workflow_result['error'] = "No pins scraped"
                PromptDB.update_prompt_status(self.prompt_id, "error")
                return workflow_result
            
            # Phase 4: Title enrichment (status handled by run_enrichment_phase)
            self._log("=== ENRICHMENT PHASE ===")
            enrichment_success = await self.run_enrichment_phase()
            
            if enrichment_success:
                # Mark prompt as ready for AI validation
                PromptDB.update_prompt_status(self.prompt_id, "ready")
                
                # Get final pin count
                pin_count = PinDB.count_pins_by_prompt(self.prompt_id)
                
                workflow_result.update({
                    'success': True,
                    'pin_count': pin_count
                })
                
                self._log(f"=== WORKFLOW COMPLETED - {pin_count} pins ready for AI validation ===")
            else:
                PromptDB.update_prompt_status(self.prompt_id, "error")
                workflow_result['error'] = "Title enrichment failed"
            
            return workflow_result
            
        except Exception as e:
            self._log(f"Workflow error: {e}")
            PromptDB.update_prompt_status(self.prompt_id, "error")
            workflow_result['error'] = str(e)
            return workflow_result
            
        finally:
            # Always cleanup
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up browser session and resources"""
        try:
            if self.warmup_session:
                self._log("Cleaning up browser session...")
                await self.warmup_session.close()
        except Exception as e:
            self._log(f"Cleanup error: {e}")
    
    def get_status(self) -> Dict:
        """Get current workflow status and progress from database"""
        from ...database.prompts import PromptDB
        from ...database.sessions import SessionDB
        from ...database.pins import PinDB
        
        prompt_doc = PromptDB.get_prompt_by_id(self.prompt_id)
        sessions = SessionDB.get_sessions_by_prompt(self.prompt_id)
        pin_count = PinDB.count_pins_by_prompt(self.prompt_id)
        
        return {
            'prompt_id': str(self.prompt_id),
            'prompt_text': self.prompt,
            'prompt_status': prompt_doc['status'] if prompt_doc else 'unknown',
            'created_at': prompt_doc['created_at'].isoformat() if prompt_doc else None,
            'sessions': [{
                'session_id': str(session['_id']),
                'stage': session['stage'],
                'status': session['status'],
                'timestamp': session['timestamp'].isoformat(),
                'recent_logs': session.get('log', [])[-3:]
            } for session in sessions],
            'pin_count': pin_count
        }
