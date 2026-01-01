"""
Referral system service
"""
import json
from datetime import datetime
from typing import Optional
from bot.database.connection import execute_query, fetch_query
from config.constants import (
    REFERRAL_PAYLOAD_PREFIX, REFERRAL_UNLOCK_THRESHOLD,
    PARTNER_PREFERENCE_UNLOCK_THRESHOLD
)
import logging

logger = logging.getLogger(__name__)


def generate_referral_link(bot_username: str, user_id: int) -> str:
    """Generate referral link for a user"""
    payload = f"{REFERRAL_PAYLOAD_PREFIX}{user_id}"
    return f"https://t.me/{bot_username}?start={payload}"


async def process_referral(referrer_id: int, referree_id: int) -> bool:
    """
    Process a referral (when new user signs up via referral link)
    Returns True if successfully processed
    """
    try:
        # Check for self-referral
        if referrer_id == referree_id:
            logger.warning(f"Self-referral attempted by user {referrer_id}")
            return False
        
        # Check if referral already exists
        existing = await fetch_query(
            "SELECT id FROM referrals WHERE referrer_id = $1 AND referree_id = $2",
            referrer_id, referree_id
        )
        if existing:
            logger.info(f"Referral already exists: {referrer_id} -> {referree_id}")
            return False
        
        # Create referral record
        await execute_query(
            """
            INSERT INTO referrals (referrer_id, referree_id, created_at)
            VALUES ($1, $2, NOW())
            """,
            referrer_id, referree_id
        )
        
        # Increment referral count
        await execute_query(
            """
            UPDATE users
            SET referrals_count = referrals_count + 1
            WHERE id = $1
            """,
            referrer_id
        )
        
        # Check if unlock thresholds reached
        user_data = await fetch_query(
            "SELECT referrals_count, unlocked_features FROM users WHERE id = $1",
            referrer_id
        )
        
        if user_data:
            referrals_count = user_data['referrals_count'] or 0
            current_unlocked = user_data.get('unlocked_features') or {}
            if isinstance(current_unlocked, str):
                import json
                current_unlocked = json.loads(current_unlocked) if current_unlocked else {}
            
            unlocked = dict(current_unlocked)
            updated = False
            
            # Unlock partner preference at 3 referrals
            if referrals_count >= PARTNER_PREFERENCE_UNLOCK_THRESHOLD:
                if not unlocked.get('partner_preference', False):
                    unlocked['partner_preference'] = True
                    updated = True
                    logger.info(f"Unlocked partner preference for user {referrer_id}")
            
            # Unlock other features at 5 referrals
            if referrals_count >= REFERRAL_UNLOCK_THRESHOLD:
                if not unlocked.get('see_gender', False):
                    unlocked['see_gender'] = True
                    unlocked['search_by_age'] = True
                    updated = True
                    logger.info(f"Unlocked premium features for user {referrer_id}")
            
            if updated:
                await execute_query(
                    """
                    UPDATE users
                    SET unlocked_features = $1::jsonb
                    WHERE id = $2
                    """,
                    json.dumps(unlocked), referrer_id
                )
        
        logger.info(f"Processed referral: {referrer_id} -> {referree_id}")
        return True
    except Exception as e:
        logger.error(f"Error processing referral: {e}")
        return False


async def get_referral_count(user_id: int) -> int:
    """Get referral count for a user"""
    user_data = await fetch_query(
        "SELECT referrals_count FROM users WHERE id = $1",
        user_id
    )
    if user_data:
        return user_data['referrals_count'] or 0
    return 0


async def get_unlocked_features(user_id: int) -> dict:
    """Get unlocked features for a user"""
    user_data = await fetch_query(
        "SELECT unlocked_features FROM users WHERE id = $1",
        user_id
    )
    if user_data and user_data['unlocked_features']:
        return user_data['unlocked_features']
    return {}

