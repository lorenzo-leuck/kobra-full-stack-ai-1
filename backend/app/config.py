from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # MongoDB settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "pinterest_scraper"
    
    # API settings
    API_PREFIX: str = "/api/v1"
    
    # Pinterest settings
    PINTEREST_BASE_URL: str = "https://www.pinterest.com"
    PINTEREST_USERNAME: Optional[str] = None
    PINTEREST_PASSWORD: Optional[str] = None
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
