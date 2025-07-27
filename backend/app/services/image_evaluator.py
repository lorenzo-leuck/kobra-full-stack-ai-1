import httpx
from app.config import settings


class ImageEvaluator:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY if hasattr(settings, "OPENAI_API_KEY") else None
        
    async def generate_explanation(self, prompt: str, image_url: str, match_score: float) -> str:
        """Generate an explanation for why an image matches or doesn't match a prompt."""
        explanation_prompt = f"""
        You are evaluating how well an image matches the visual prompt: "{prompt}"
        The image has been given a match score of {match_score:.2f} out of 1.0.
        
        Please provide a brief, 1-2 sentence explanation of why the image received this score.
        Focus on specific visual elements that either match or don't match the prompt.
        """
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant that evaluates image-prompt matches."},
                            {"role": "user", "content": explanation_prompt}
                        ],
                        "max_tokens": 100
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                explanation = result["choices"][0]["message"]["content"].strip()
                return explanation
        except httpx.HTTPStatusError as e:
            print(f"HTTP error generating explanation: {e.response.status_code} - {e.response.text}")
            return self._get_fallback_explanation(match_score)
        except httpx.RequestError as e:
            print(f"Request error generating explanation: {e}")
            return self._get_fallback_explanation(match_score)
        except (KeyError, IndexError, ValueError) as e:
            print(f"Error parsing API response: {e}")
            return self._get_fallback_explanation(match_score)
        except Exception as e:
            print(f"Unexpected error generating explanation: {e}")
            return self._get_fallback_explanation(match_score)
            
    def _get_fallback_explanation(self, match_score: float) -> str:
        """Get a fallback explanation based on the match score."""
        if match_score >= 0.7:
            return "The image appears to match the prompt well based on its visual elements."
        elif match_score >= 0.4:
            return "The image partially matches some aspects of the prompt."
        else:
            return "The image does not appear to match the key elements of the prompt."

    async def evaluate_image_match(self, prompt: str, image_url: str) -> float:
        if not self.api_key:
            return 0.5  # Default score if no API key is available
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4-vision-preview",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": image_url}}
                                ]
                            }
                        ],
                        "max_tokens": 300
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                score_text = result["choices"][0]["message"]["content"].strip()
                try:
                    score = float(score_text)
                    return min(max(score, 0.0), 1.0)  # Ensure score is between 0 and 1
                except ValueError as e:
                    print(f"Error parsing score: {e}")
                    return 0.5  # Default score if parsing fails
                    
        except httpx.HTTPStatusError as e:
            print(f"HTTP error evaluating image match: {e.response.status_code} - {e.response.text}")
            return 0.5  # Default score on HTTP error
        except httpx.RequestError as e:
            print(f"Request error evaluating image match: {e}")
            return 0.5  # Default score on request error
        except (KeyError, IndexError) as e:
            print(f"Error parsing API response: {e}")
            return 0.5  # Default score on parsing error
        except Exception as e:
            print(f"Unexpected error evaluating image match: {e}")
            return 0.5  # Default score on any other error