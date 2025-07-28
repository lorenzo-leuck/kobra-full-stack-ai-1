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
        
        # Initialize Pinterest-specific components
        pinterest_workflow = PinterestWorkflowHandler(
            prompt=self.prompt,
            prompt_id=self.prompt_id,
            username=username,
            password=password
        )
        
        # Set current session for logging
        self.current_session_id = pinterest_workflow.current_session_id
        
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
            
            # Get prompt to validate it exists
            prompt_doc = PromptDB.get_prompt_by_id(prompt_id)
            if not prompt_doc:
                return {
                    "success": False,
                    "error": f"Prompt not found: {prompt_id}"
                }
            
            # Create AI validation session
            session_id = SessionDB.create_session(prompt_id, "validation")
            self.current_session_id = session_id
            
            self._log("=== AI VALIDATION PHASE ===")
            self._log(f"Starting AI validation for prompt: {prompt_doc['text']}")
            
            # Initialize AI evaluator
            evaluator = AIEvaluator()
            
            # Run AI validation
            result = await evaluator.evaluate_pins_for_prompt(prompt_id)
            
            if result["success"]:
                # Update session status
                SessionDB.update_session_status(session_id, "completed")
                
                # Update prompt status to completed
                PromptDB.update_prompt_status(prompt_id, "completed")
                
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
        Execute Pinterest algorithm warmup phase
        
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
            self._log(f"Starting warmup phase for prompt: '{self.prompt}'")
            
            warmup_success = await self.warmup_session.feed_algorithm()
            
            if warmup_success:
                self._log("Warmup phase completed successfully")
                SessionDB.update_session_status(self.current_session_id, "ready")
                return True
            else:
                self._log("Warmup phase failed, but continuing...")
                SessionDB.update_session_status(self.current_session_id, "failed")
                return False
                
        except Exception as e:
            self._log(f"Warmup phase error: {e}")
            SessionDB.update_session_status(self.current_session_id, "failed")
            return False
    
    async def run_scraping_phase(self, num_images: int = 20) -> List[ObjectId]:
        """
        Execute Pinterest feed scraping phase and save pins to database
        
        Args:
            num_images (int): Number of images to scrape
            
        Returns:
            List[ObjectId]: List of created pin IDs
        """
        if not self.warmup_session or not self.pins_handler:
            self._log("Session not properly initialized")
            return []
        
        # Update session to scraping stage
        from ...database.sessions import SessionDB
        from ...database.pins import PinDB
        SessionDB.update_session_stage(self.current_session_id, "scraping")
        
        try:
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
                
                SessionDB.update_session_status(self.current_session_id, "ready")
                return pin_ids
            else:
                self._log("No pins found during scraping")
                SessionDB.update_session_status(self.current_session_id, "failed")
                return []
            
        except Exception as e:
            self._log(f"Scraping phase error: {e}")
            SessionDB.update_session_status(self.current_session_id, "failed")
            return []
    
    async def run_enrichment_phase(self) -> bool:
        """
        Execute title enrichment phase for pins in database
        
        Returns:
            bool: True if enrichment successful
        """
        # Update session to validation stage
        from ...database.sessions import SessionDB
        from ...database.pins import PinDB
        SessionDB.update_session_stage(self.current_session_id, "validation")
        
        # Get pins from database
        pins = PinDB.get_pins_by_prompt(self.prompt_id)
        if not pins:
            self._log("No pins found in database to enrich")
            SessionDB.update_session_status(self.current_session_id, "failed")
            return False
        
        if not self.pins_handler:
            self._log("Pins handler not initialized")
            SessionDB.update_session_status(self.current_session_id, "failed")
            return False
        
        try:
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
            
            # Enrich titles
            enriched_data = await self.pins_handler.enrich_with_titles([data for _, data in pin_data_for_enrichment])
            
            # Update database with enriched titles
            from ...database.pins import PinDB
            for i, (pin_id, _) in enumerate(pin_data_for_enrichment):
                if i < len(enriched_data) and enriched_data[i].get("title"):
                    # Update the pin in database with the new title
                    PinDB.update_pin_title(pin_id, enriched_data[i]["title"])
            
            self._log(f"Title enrichment completed - {len(enriched_data)} pins processed")
            SessionDB.update_session_status(self.current_session_id, "ready")
            
            return True
            
        except Exception as e:
            self._log(f"Enrichment phase error: {e}")
            SessionDB.update_session_status(self.current_session_id, "failed")
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
            self._log("=== INITIALIZATION PHASE ===")
            init_success = await self.initialize_session(headless=headless)
            if not init_success:
                workflow_result['error'] = "Session initialization failed"
                return workflow_result
            
            # Phase 2: Warmup
            self._log("=== WARMUP PHASE ===")
            warmup_success = await self.run_warmup_phase()
            # Continue even if warmup fails
            
            # Phase 3: Scraping
            self._log("=== SCRAPING PHASE ===")
            pin_ids = await self.run_scraping_phase(num_images=num_images)
            if not pin_ids:
                workflow_result['error'] = "No pins scraped"
                PromptDB.update_prompt_status(self.prompt_id, "error")
                return workflow_result
            
            # Phase 4: Title enrichment
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
