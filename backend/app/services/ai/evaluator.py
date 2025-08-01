from typing import List
from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ImageUrl
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

from app.config import settings
from app.database import PromptDB, PinDB, AgentDB


class PinValidation(BaseModel):
    match_score: float = Field(ge=0.0, le=1.0, description="Match score between 0.0 and 1.0")
    status: str = Field(pattern="^(approved|disqualified)$", description="approved if ≥0.5, disqualified if <0.5")
    explanation: str = Field(description="2-3 sentences explaining the match quality")


class AIEvaluator:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for AI evaluation")
        
        # Load agent configuration from database
        agent_config = AgentDB.get_agent_by_title("pin-evaluator")
        if not agent_config:
            raise ValueError("Agent configuration 'pin-evaluator' not found in database. Please run database setup.")
        
        # Create OpenAI provider with API key
        provider = OpenAIProvider(api_key=settings.OPENAI_API_KEY)
        self.model = OpenAIModel(agent_config["model"], provider=provider)
        
        # Store user prompt template for later use
        self.user_prompt_template = agent_config["user_prompt_template"]
        
        # Configure model settings with temperature from database
        model_settings = ModelSettings(
            temperature=agent_config.get("temperature", 0.7)  # Default to 0.7 if not set
        )
        
        self.agent = Agent(
            model=self.model,
            result_type=PinValidation,
            system_prompt=agent_config["system_prompt"],
            model_settings=model_settings
        )
    
    async def evaluate_pin(self, prompt_text: str, image_url: str, title: str = None, description: str = None) -> PinValidation:
        # Build comprehensive evaluation prompt including textual metadata
        textual_context = ""
        if title:
            textual_context += f"\nPin Title: {title}"
        if description:
            textual_context += f"\nPin Description: {description}"
        
        # Use the user prompt template from database configuration
        evaluation_prompt = self.user_prompt_template.format(
            prompt_text=prompt_text,
            textual_context=textual_context
        )
        
        # Send both the image and text for proper multimodal analysis
        messages = [
            evaluation_prompt,
            ImageUrl(url=image_url)  # This sends the actual image for visual analysis
        ]
        
        result = await self.agent.run(messages)
        return result.data
    
    async def evaluate_pins_for_prompt(self, prompt_id: ObjectId) -> dict:
        prompt_doc = PromptDB.get_prompt_by_id(prompt_id)
        if not prompt_doc:
            raise ValueError(f"Prompt not found: {prompt_id}")
        
        prompt_text = prompt_doc["text"]
        
        ready_pins = PinDB.get_pins_by_status(prompt_id, "ready")
        if not ready_pins:
            return {
                "success": True,
                "message": "No pins with 'ready' status found",
                "evaluated_count": 0,
                "approved_count": 0,
                "disqualified_count": 0
            }
        
        evaluated_count = 0
        approved_count = 0
        disqualified_count = 0
        
        for pin in ready_pins:
            try:
                pin_id = pin["_id"]
                image_url = pin["image_url"]
                title = pin.get("title")
                description = pin.get("description")
                
                validation = await self.evaluate_pin(
                    prompt_text=prompt_text, 
                    image_url=image_url,
                    title=title,
                    description=description
                )
                
                success = PinDB.update_pin_ai_validation(
                    pin_id=pin_id,
                    match_score=validation.match_score,
                    status=validation.status,
                    ai_explanation=validation.explanation
                )
                
                if success:
                    evaluated_count += 1
                    if validation.status == "approved":
                        approved_count += 1
                    else:
                        disqualified_count += 1
                
            except Exception as e:
                print(f"Error evaluating pin {pin.get('_id')}: {e}")
                continue
        
        return {
            "success": True,
            "message": f"Evaluated {evaluated_count} pins",
            "evaluated_count": evaluated_count,
            "approved_count": approved_count,
            "disqualified_count": disqualified_count
        }
