"""
Configuration settings for the FILMPRO script analysis service.
"""
import os
from pydantic import BaseSettings, Field
from typing import Optional, Dict, Any, List


class Settings(BaseSettings):
    """Application settings that can be loaded from environment variables."""
    
    # General settings
    APP_NAME: str = "FILMPRO Script Analysis Service"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = Field(False, env="DEBUG")
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Security settings
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database settings
    MONGO_URI: str = Field(..., env="MONGO_URI")
    MONGO_DB_NAME: str = Field("filmpro_scripts", env="MONGO_DB_NAME")
    
    # Storage settings
    SCRIPT_UPLOAD_DIR: str = Field("/tmp/filmpro/scripts", env="SCRIPT_UPLOAD_DIR")
    MAX_SCRIPT_SIZE_MB: int = 10
    
    # NLP settings
    SPACY_MODEL: str = "en_core_web_md"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    def ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.SCRIPT_UPLOAD_DIR, exist_ok=True)


# Create global settings instance
settings = Settings()
settings.ensure_directories()