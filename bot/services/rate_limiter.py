"""
Rate limiting service using Redis
"""
from bot.services.redis_client import get_redis
from config.constants import REDIS_RATE_LIMIT_PREFIX, MAX_MESSAGES_PER_MINUTE
import logging

logger = logging.getLogger(__name__)


async def check_rate_limit(user_id: int, limit: int = MAX_MESSAGES_PER_MINUTE, window_seconds: int = 60) -> bool:
    """
    Check if user has exceeded rate limit
    Returns True if allowed, False if rate limited
    """
    try:
        redis_client = await get_redis()
        key = f"{REDIS_RATE_LIMIT_PREFIX}:{user_id}"
        
        # Get current count
        current = await redis_client.get(key)
        if current is None:
            # First request in window
            await redis_client.setex(key, window_seconds, 1)
            return True
        
        current_count = int(current)
        if current_count >= limit:
            return False  # Rate limited
        
        # Increment count
        await redis_client.incr(key)
        return True
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        return True  # Allow on error (fail open)

