"""
User statistics service
"""
from typing import Dict
from bot.database.connection import fetch_query, fetch_all
import logging

logger = logging.getLogger(__name__)


async def get_user_stats(user_id: int) -> Dict:
    """Get comprehensive user statistics"""
    try:
        # Get user data
        user_data = await fetch_query(
            """
            SELECT 
                id, username, display_name, created_at, last_active,
                referrals_count, unlocked_features, is_banned
            FROM users WHERE id = $1
            """,
            user_id
        )
        
        if not user_data:
            return {}
        
        # Count total pairs/chats
        pairs_data = await fetch_query(
            """
            SELECT COUNT(*) as count 
            FROM pairs 
            WHERE user_a = $1 OR user_b = $1
            """,
            user_id
        )
        total_chats = pairs_data['count'] if pairs_data else 0
        
        # Count active pairs
        active_pairs_data = await fetch_query(
            """
            SELECT COUNT(*) as count 
            FROM pairs 
            WHERE (user_a = $1 OR user_b = $1) AND is_active = true
            """,
            user_id
        )
        active_chats = active_pairs_data['count'] if active_pairs_data else 0
        
        # Count messages sent
        messages_data = await fetch_query(
            """
            SELECT COUNT(*) as count 
            FROM messages 
            WHERE from_id = $1
            """,
            user_id
        )
        messages_sent = messages_data['count'] if messages_data else 0
        
        # Get account age
        from datetime import datetime
        created_at = user_data.get('created_at')
        account_age_days = 0
        if created_at:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            account_age_days = (datetime.now(created_at.tzinfo) - created_at).days if hasattr(created_at, 'tzinfo') else (datetime.now() - created_at).days
        
        # Get unlocked features
        unlocked = user_data.get('unlocked_features', {}) or {}
        has_unlocked = unlocked.get('see_gender', False) or unlocked.get('search_by_age', False)
        
        return {
            "user_id": user_id,
            "username": user_data.get('username'),
            "display_name": user_data.get('display_name'),
            "created_at": created_at,
            "last_active": user_data.get('last_active'),
            "referrals_count": user_data.get('referrals_count', 0) or 0,
            "total_chats": total_chats,
            "active_chats": active_chats,
            "messages_sent": messages_sent,
            "account_age_days": account_age_days,
            "has_unlocked_features": has_unlocked,
            "unlocked_features": unlocked,
            "is_banned": user_data.get('is_banned', False)
        }
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return {}


async def get_user_chat_count(user_id: int) -> int:
    """Count total pairs/chats for a user"""
    try:
        pairs_data = await fetch_query(
            """
            SELECT COUNT(*) as count 
            FROM pairs 
            WHERE user_a = $1 OR user_b = $1
            """,
            user_id
        )
        return pairs_data['count'] if pairs_data else 0
    except Exception as e:
        logger.error(f"Error getting chat count: {e}")
        return 0


async def get_user_message_count(user_id: int) -> int:
    """Count messages sent by a user"""
    try:
        messages_data = await fetch_query(
            """
            SELECT COUNT(*) as count 
            FROM messages 
            WHERE from_id = $1
            """,
            user_id
        )
        return messages_data['count'] if messages_data else 0
    except Exception as e:
        logger.error(f"Error getting message count: {e}")
        return 0

