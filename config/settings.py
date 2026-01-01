"""
Configuration settings loaded from environment variables
"""
import os
import re
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()


def validate_bot_token(token: str) -> bool:
    """Validate Telegram bot token format"""
    if not token or not token.strip():
        return False
    # Telegram bot tokens follow format: {bot_id}:{token_string}
    # bot_id is numeric, token_string is alphanumeric with hyphens/underscores
    pattern = r'^\d+:[A-Za-z0-9_-]+$'
    return bool(re.match(pattern, token.strip()))


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
_bot_token = os.getenv("BOT_TOKEN", "").strip()
_admin_secret = os.getenv("ADMIN_SECRET", "").strip()

# Validate bot token format
if _bot_token and not validate_bot_token(_bot_token):
    raise ValueError(
        "Invalid BOT_TOKEN format. "
        "Telegram bot tokens should be in format: '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'. "
        "Get a valid token from @BotFather on Telegram."
    )

if not _bot_token:
    raise ValueError(
        "BOT_TOKEN environment variable is required but not set. "
        "Please set BOT_TOKEN in your Railway environment variables. "
        "Get a token from @BotFather on Telegram: https://t.me/BotFather"
    )

settings = Settings(
    bot_token=_bot_token,
    admin_secret=_admin_secret,
    database_url=os.getenv("DATABASE_URL"),
    redis_url=os.getenv("REDIS_URL"),
    webhook_url=os.getenv("WEBHOOK_URL")
)

