"""
Admin service for admin operations
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bot.database.connection import execute_query, fetch_query, fetch_all
from bot.services.redis_client import get_redis
from bot.services.matchmaking import get_queue_size, create_pair
from config.constants import (
    ADMIN_SESSION_DURATION_HOURS, GENDER_UNKNOWN, LANGUAGE_ANY,
    USER_STATE_WAITING, USER_STATE_CHATTING, USER_STATE_IDLE
)
import logging

logger = logging.getLogger(__name__)


async def grant_admin_access(user_id: int) -> bool:
    """Grant admin access to a user (2 hour session)"""
    try:
        expiry = datetime.utcnow() + timedelta(hours=ADMIN_SESSION_DURATION_HOURS)
        await execute_query(
            """
            UPDATE users
            SET is_admin = true, admin_session_expiry = $1
            WHERE id = $2
            """,
            expiry, user_id
        )
        logger.info(f"Granted admin access to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error granting admin access: {e}")
        return False


async def check_admin_access(user_id: int) -> bool:
    """Check if user has valid admin access"""
    try:
        user_data = await fetch_query(
            "SELECT is_admin, admin_session_expiry FROM users WHERE id = $1",
            user_id
        )
        
        if not user_data or not user_data['is_admin']:
            return False
        
        # Check if session expired
        if user_data['admin_session_expiry']:
            expiry = user_data['admin_session_expiry']
            if datetime.utcnow() > expiry:
                # Revoke admin access
                await execute_query(
                    "UPDATE users SET is_admin = false, admin_session_expiry = NULL WHERE id = $1",
                    user_id
                )
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error checking admin access: {e}")
        return False


async def log_admin_action(admin_id: int, action: str, metadata: Dict = None):
    """Log an admin action"""
    try:
        import json
        meta_json = json.dumps(metadata or {})
        await execute_query(
            """
            INSERT INTO admin_logs (admin_id, action, metadata, created_at)
            VALUES ($1, $2, $3::jsonb, NOW())
            """,
            admin_id, action, meta_json
        )
    except Exception as e:
        logger.error(f"Error logging admin action: {e}")


async def get_online_stats() -> Dict:
    """Get online user statistics"""
    try:
        redis_client = await get_redis()
        
        # Count users in different states
        waiting_keys = await redis_client.keys("user_state:*")
        waiting_count = 0
        chatting_count = 0
        
        for key in waiting_keys:
            state = await redis_client.get(key)
            if state == USER_STATE_WAITING:
                waiting_count += 1
            elif state == USER_STATE_CHATTING:
                chatting_count += 1
        
        # Get queue sizes
        queue_sizes = {}
        try:
            for gender in [GENDER_UNKNOWN, 1, 2, 3]:
                for lang in ['any', 'malayalam', 'english', 'hindi']:
                    size = await get_queue_size(gender, lang)
                    if size > 0:
                        queue_sizes[f"gender_{gender}_lang_{lang}"] = size
        except Exception as e:
            logger.error(f"Error getting queue sizes: {e}")
        
        # Get total active pairs
        from bot.database.connection import fetch_query
        pairs_data = await fetch_query(
            "SELECT COUNT(*) as count FROM pairs WHERE is_active = true"
        )
        active_pairs = pairs_data['count'] if pairs_data else 0
        
        return {
            "waiting_users": waiting_count,
            "chatting_users": chatting_count,
            "active_pairs": active_pairs,
            "queue_sizes": queue_sizes
        }
    except Exception as e:
        logger.error(f"Error getting online stats: {e}")
        return {}


async def get_user_pair_info(user_id: int) -> Optional[Dict]:
    """Get pair information for a user (for admin)"""
    try:
        pair_data = await fetch_query(
            """
            SELECT pair_id, user_a, user_b, started_at, last_message_at, is_active
            FROM pairs
            WHERE (user_a = $1 OR user_b = $1) AND is_active = true
            ORDER BY started_at DESC LIMIT 1
            """,
            user_id
        )
        
        if pair_data:
            return {
                "pair_id": pair_data['pair_id'],
                "user_a": pair_data['user_a'],
                "user_b": pair_data['user_b'],
                "started_at": pair_data['started_at'].isoformat() if pair_data['started_at'] else None,
                "last_message_at": pair_data['last_message_at'].isoformat() if pair_data['last_message_at'] else None,
                "is_active": pair_data['is_active']
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user pair info: {e}")
        return None


async def force_pair_users(user_a: int, user_b: int, language: str = LANGUAGE_ANY) -> Optional[str]:
    """Force pair two users (admin only)"""
    try:
        pair_id = await create_pair(user_a, user_b, language)
        if pair_id:
            await log_admin_action(
                user_a,  # Assuming admin_id is user_a for logging
                "force_pair",
                {"user_a": user_a, "user_b": user_b, "pair_id": pair_id}
            )
        return pair_id
    except Exception as e:
        logger.error(f"Error forcing pair: {e}")
        return None


async def ban_user(user_id: int, admin_id: int) -> bool:
    """Ban a user"""
    try:
        await execute_query(
            "UPDATE users SET is_banned = true WHERE id = $1",
            user_id
        )
        await log_admin_action(admin_id, "ban", {"user_id": user_id})
        logger.info(f"User {user_id} banned by admin {admin_id}")
        return True
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        return False


async def unban_user(user_id: int, admin_id: int) -> bool:
    """Unban a user"""
    try:
        await execute_query(
            "UPDATE users SET is_banned = false WHERE id = $1",
            user_id
        )
        await log_admin_action(admin_id, "unban", {"user_id": user_id})
        logger.info(f"User {user_id} unbanned by admin {admin_id}")
        return True
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        return False

