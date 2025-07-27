from typing import Dict, Any, List
import httpx
from app.config import settings


class ImageEvaluator:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY if hasattr(settings, "OPENAI_API_KEY") else None
        
    async def evaluate_image_match(self, prompt: str, image_description: str) -> float:
        if not self.api_key:
            return 0.5  # Default score if no API key is available
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json={
                        "model": "gpt-4-vision-preview",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an AI that evaluates how well an image matches a given prompt. Provide a score between 0.0 and 1.0, where 1.0 is a perfect match."
                            },
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Evaluate how well this image description matches the prompt: '{prompt}'. The image description is: '{image_description}'. Return only a number between 0.0 and 1.0."
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 10
                    },
                    timeout=30.0
                )
                
                result = response.json()
                score_text = result["choices"][0]["message"]["content"].strip()
                try:
                    score = float(score_text)
                    return min(max(score, 0.0), 1.0)  # Ensure score is between 0 and 1
                except ValueError:
                    return 0.5  # Default score if parsing fails
                    
        except Exception as e:
            print(f"Error evaluating image match: {e}")
            return 0.5  # Default score on error
