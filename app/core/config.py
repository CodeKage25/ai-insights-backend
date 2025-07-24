from functools import lru_cache
from typing import Set
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application settings
    app_name: str = "AI Insights Platform"
    debug: bool = False
    
    # File upload settings
    upload_dir: str = "./tmp/uploads"
    allowed_extensions: Set[str] = {".csv", ".xls", ".xlsx"}
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_preview_rows: int = 5
    
    # Database settings
    database_url: str = "sqlite:///./ai_insights.db"
    
    # Processing settings
    max_insights: int = 5
    min_confidence_score: float = 0.1
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
