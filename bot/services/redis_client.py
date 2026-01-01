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
            raise ValueError("REDIS_URL not set. Please configure your Redis connection.")
        
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

