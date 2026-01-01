"""
Matchmaking service for pairing users
"""
import uuid
from datetime import datetime
from typing import Optional, Tuple
from bot.services.redis_client import get_redis
from bot.database.connection import execute_query, fetch_query, fetch_all
from config.constants import (
    REDIS_QUEUE_PREFIX, MATCH_TIMEOUT_SECONDS, GENDER_UNKNOWN,
    USER_STATE_WAITING, USER_STATE_CHATTING, LANGUAGE_ANY
)
import logging

logger = logging.getLogger(__name__)


def get_queue_key(gender: int, language: str) -> str:
    """Generate Redis queue key for gender and language combination"""
    return f"{REDIS_QUEUE_PREFIX}:gender:{gender}:lang:{language}"


async def add_to_queue(user_id: int, gender_filter: int, language_preference: str, use_gender_preference: bool = False) -> bool:
    """
    Add user to matchmaking queue
    Returns True if added successfully
    
    Args:
        user_id: User ID to add to queue
        gender_filter: Gender filter to use (can be overridden by gender_preference)
        language_preference: Language preference
        use_gender_preference: If True, use user's gender_preference instead of gender_filter
    """
    try:
        redis_client = await get_redis()
        
        # If use_gender_preference is True, get user's gender_preference
        if use_gender_preference:
            from bot.database.connection import fetch_query
            user_data = await fetch_query(
                "SELECT gender_preference, unlocked_features FROM users WHERE id = $1",
                user_id
            )
            if user_data:
                unlocked = user_data.get('unlocked_features') or {}
                if isinstance(unlocked, str):
                    import json
                    unlocked = json.loads(unlocked) if unlocked else {}
                
                if unlocked.get('partner_preference', False):
                    gender_pref = user_data.get('gender_preference', 0) or 0
                    if gender_pref > 0:  # Only use if set (not 0/any)
                        gender_filter = gender_pref
        
        queue_key = get_queue_key(gender_filter, language_preference)
        
        # Check if user is already in any queue
        existing_queues = await redis_client.keys(f"{REDIS_QUEUE_PREFIX}:*")
        for queue in existing_queues:
            if await redis_client.lrem(queue, 0, str(user_id)) > 0:
                logger.info(f"Removed user {user_id} from existing queue {queue}")
        
        # Add to new queue
        await redis_client.lpush(queue_key, str(user_id))
        await redis_client.setex(f"user_state:{user_id}", 300, USER_STATE_WAITING)  # 5 min TTL
        logger.info(f"Added user {user_id} to queue {queue_key}")
        return True
    except Exception as e:
        logger.error(f"Error adding user to queue: {e}")
        return False


async def remove_from_queue(user_id: int) -> bool:
    """Remove user from all queues"""
    try:
        redis_client = await get_redis()
        queues = await redis_client.keys(f"{REDIS_QUEUE_PREFIX}:*")
        removed = False
        for queue in queues:
            if await redis_client.lrem(queue, 0, str(user_id)) > 0:
                removed = True
                logger.info(f"Removed user {user_id} from queue {queue}")
        return removed
    except Exception as e:
        logger.error(f"Error removing user from queue: {e}")
        return False


async def try_match(user_id: int, gender_filter: int, language_preference: str) -> Optional[int]:
    """
    Try to find a match for the user
    Returns matched user_id if found, None otherwise
    """
    redis_client = await get_redis()
    
    # Primary queue (exact match)
    primary_key = get_queue_key(gender_filter, language_preference)
    matched_id = await try_match_from_queue(redis_client, primary_key, user_id)
    if matched_id:
        return matched_id
    
    # Fallback: try 'any' language with same gender
    if language_preference != LANGUAGE_ANY:
        fallback_key = get_queue_key(gender_filter, LANGUAGE_ANY)
        matched_id = await try_match_from_queue(redis_client, fallback_key, user_id)
        if matched_id:
            return matched_id
    
    # Fallback: try 'any' gender with same language
    if gender_filter != GENDER_UNKNOWN:
        fallback_key = get_queue_key(GENDER_UNKNOWN, language_preference)
        matched_id = await try_match_from_queue(redis_client, fallback_key, user_id)
        if matched_id:
            return matched_id
    
    # Final fallback: any gender, any language
    if gender_filter != GENDER_UNKNOWN or language_preference != LANGUAGE_ANY:
        fallback_key = get_queue_key(GENDER_UNKNOWN, LANGUAGE_ANY)
        matched_id = await try_match_from_queue(redis_client, fallback_key, user_id)
        if matched_id:
            return matched_id
    
    return None


async def try_match_from_queue(redis_client, queue_key: str, user_id: int) -> Optional[int]:
    """Try to pop a user from the queue (excluding self)"""
    try:
        # Get queue length
        queue_len = await redis_client.llen(queue_key)
        if queue_len == 0:
            return None
        
        # Pop and check users until we find a valid match
        for _ in range(min(queue_len, 10)):  # Check max 10 users
            candidate_id_str = await redis_client.rpop(queue_key)
            if not candidate_id_str:
                break
            
            candidate_id = int(candidate_id_str)
            
            # Skip self
            if candidate_id == user_id:
                await redis_client.lpush(queue_key, candidate_id_str)  # Put back
                continue
            
            # Check if user is banned or blocked
            user_data = await fetch_query(
                "SELECT is_banned, blocked_users FROM users WHERE id = $1",
                candidate_id
            )
            
            if not user_data or user_data.get('is_banned'):
                continue
            
            # Check if current user blocked this candidate
            current_user_data = await fetch_query(
                "SELECT blocked_users FROM users WHERE id = $1",
                user_id
            )
            if current_user_data:
                blocked = current_user_data.get('blocked_users') or []
                # Handle both list and JSONB format
                if isinstance(blocked, list) and candidate_id in blocked:
                    continue
                elif isinstance(blocked, dict) and candidate_id in blocked.values():
                    continue
            
            # Valid match found
            return candidate_id
        
        # No valid match found, put back the popped users
        return None
    except Exception as e:
        logger.error(f"Error trying match from queue {queue_key}: {e}")
        return None


async def create_pair(user_a: int, user_b: int, language_used: str) -> Optional[str]:
    """
    Create a pair record in database
    Returns pair_id if successful
    """
    try:
        import uuid
        pair_id = str(uuid.uuid4())
        await execute_query(
            """
            INSERT INTO pairs (pair_id, user_a, user_b, language_used, started_at, last_message_at)
            VALUES ($1::uuid, $2, $3, $4, NOW(), NOW())
            """,
            pair_id, user_a, user_b, language_used
        )
        
        # Update user states in Redis
        redis_client = await get_redis()
        await redis_client.setex(f"user_state:{user_a}", 3600, USER_STATE_CHATTING)
        await redis_client.setex(f"user_state:{user_b}", 3600, USER_STATE_CHATTING)
        await redis_client.set(f"user_pair:{user_a}", pair_id, ex=3600)
        await redis_client.set(f"user_pair:{user_b}", pair_id, ex=3600)
        
        logger.info(f"Created pair {pair_id} between users {user_a} and {user_b}")
        return pair_id
    except Exception as e:
        logger.error(f"Error creating pair: {e}")
        return None


async def get_user_pair(user_id: int) -> Optional[str]:
    """Get the active pair_id for a user"""
    try:
        redis_client = await get_redis()
        pair_id = await redis_client.get(f"user_pair:{user_id}")
        if pair_id:
            return pair_id
        
        # Fallback to database
        pair_data = await fetch_query(
            """
            SELECT pair_id FROM pairs
            WHERE (user_a = $1 OR user_b = $1) AND is_active = true
            ORDER BY started_at DESC LIMIT 1
            """,
            user_id
        )
        if pair_data:
            return pair_data['pair_id']
        return None
    except Exception as e:
        logger.error(f"Error getting user pair: {e}")
        return None


async def end_pair(pair_id: str, user_id: Optional[int] = None):
    """End a pair (mark as inactive)"""
    try:
        await execute_query(
            "UPDATE pairs SET is_active = false WHERE pair_id = $1",
            pair_id
        )
        
        # Clear Redis state for both users
        redis_client = await get_redis()
        pair_data = await fetch_query(
            "SELECT user_a, user_b FROM pairs WHERE pair_id = $1",
            pair_id
        )
        
        if pair_data:
            await redis_client.delete(f"user_pair:{pair_data['user_a']}")
            await redis_client.delete(f"user_pair:{pair_data['user_b']}")
            await redis_client.delete(f"user_state:{pair_data['user_a']}")
            await redis_client.delete(f"user_state:{pair_data['user_b']}")
        
        logger.info(f"Ended pair {pair_id}")
    except Exception as e:
        logger.error(f"Error ending pair: {e}")


async def get_queue_size(gender: int, language: str) -> int:
    """Get the size of a specific queue"""
    try:
        redis_client = await get_redis()
        queue_key = get_queue_key(gender, language)
        return await redis_client.llen(queue_key)
    except:
        return 0

