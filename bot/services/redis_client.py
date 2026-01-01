"""
Redis connection and utilities
"""
import redis.asyncio as redis
from typing import Optional
import json
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Global Redis client
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        if not settings.redis_url:
            error_msg = (
                "❌ REDIS_URL environment variable is not set!\n\n"
                "To fix this in Railway:\n"
                "1. Go to Railway dashboard → Your project\n"
                "2. Click 'New' → 'Database' → 'Add Redis'\n"
                "3. Railway will automatically provide REDIS_URL\n"
                "4. Make sure the Redis service is in the same project as your bot\n"
                "5. Redeploy your service\n\n"
                "The REDIS_URL is automatically set when you add a Redis addon."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True
        )
        logger.info("Redis client created")
    return _redis_client


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")

