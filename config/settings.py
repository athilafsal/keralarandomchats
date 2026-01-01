"""
Configuration settings loaded from environment variables
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # Telegram Bot Configuration
    bot_token: str = ""
    
    # Admin Configuration
    admin_secret: str = ""
    
    # Database (Railway auto-provides this)
    database_url: Optional[str] = None
    
    # Redis (Railway auto-provides this)
    redis_url: Optional[str] = None
    
    # Webhook URL (set in Railway dashboard)
    webhook_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings(
    bot_token=os.getenv("BOT_TOKEN", ""),
    admin_secret=os.getenv("ADMIN_SECRET", ""),
    database_url=os.getenv("DATABASE_URL"),
    redis_url=os.getenv("REDIS_URL"),
    webhook_url=os.getenv("WEBHOOK_URL")
)

