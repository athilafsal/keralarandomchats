"""
Onboarding handler for new user registration
"""
from datetime import datetime
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.connection import execute_query, fetch_query
from bot.services.referrals import process_referral
from bot.services.redis_client import get_redis
from bot.utils.validators import validate_display_name, validate_age_range
from config.constants import (
    GENDER_UNKNOWN, GENDER_MALE, GENDER_FEMALE, GENDER_OTHER, GENDER_PREFER_NOT_SAY,
    LANGUAGE_MALAYALAM, LANGUAGE_ENGLISH, LANGUAGE_HINDI, LANGUAGE_ANY,
    REFERRAL_PAYLOAD_PREFIX, ADMIN_PAYLOAD_PREFIX, USER_STATE_ONBOARDING
)
import logging

logger = logging.getLogger(__name__)

# Onboarding state storage in Redis (temporary, expires after 1 hour)
ONBOARDING_STATE_PREFIX = "onboarding:"


async def get_onboarding_state(user_id: int) -> Optional[dict]:
    """Get user's onboarding state from Redis"""
    try:
        redis_client = await get_redis()
        state_json = await redis_client.get(f"{ONBOARDING_STATE_PREFIX}{user_id}")
        if state_json:
            import json
            return json.loads(state_json)
        return None
    except Exception as e:
        logger.error(f"Error getting onboarding state: {e}")
        return None


async def set_onboarding_state(user_id: int, state: dict):
    """Set user's onboarding state in Redis"""
    try:
        redis_client = await get_redis()
        import json
        await redis_client.setex(
            f"{ONBOARDING_STATE_PREFIX}{user_id}",
            3600,  # 1 hour TTL
            json.dumps(state)
        )
    except Exception as e:
        logger.error(f"Error setting onboarding state: {e}")


async def clear_onboarding_state(user_id: int):
    """Clear user's onboarding state"""
    try:
        redis_client = await get_redis()
        await redis_client.delete(f"{ONBOARDING_STATE_PREFIX}{user_id}")
    except Exception as e:
        logger.error(f"Error clearing onboarding state: {e}")


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with deep link payload"""
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    username = user.username
    first_name = user.first_name or ""
    
    # Parse deep link payload
    payload = None
    if context.args and len(context.args) > 0:
        payload = context.args[0]
    
    # Check if user already exists
    existing_user = await fetch_query(
        "SELECT id FROM users WHERE id = $1",
        user_id
    )
    
    if existing_user:
        # User already registered
        await update.message.reply_text(
            "Welcome back! Use /next to find a chat partner.\n"
            "Commands: /next, /stop, /report, /block, /invite"
        )
        return
    
    # Process referral if present
    referral_by = None
    if payload and payload.startswith(REFERRAL_PAYLOAD_PREFIX):
        try:
            referrer_id = int(payload[len(REFERRAL_PAYLOAD_PREFIX):])
            referral_by = payload
            # Will process referral after user completes onboarding
        except ValueError:
            logger.warning(f"Invalid referral payload: {payload}")
    
    # Start onboarding
    await start_onboarding(update, context, referral_by)


async def start_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE, referral_by: Optional[str] = None):
    """Start the onboarding process"""
    user = update.effective_user
    user_id = user.id
    
    # Initialize onboarding state
    state = {
        "step": "welcome",
        "referral_by": referral_by,
        "display_name": None,
        "gender": None,
        "language_preference": None,
        "age_range": None
    }
    await set_onboarding_state(user_id, state)
    
    welcome_text = (
        "👋 Welcome to Anonymous Chat!\n\n"
        "This is an anonymous chat service. You'll be paired with random users for one-on-one conversations.\n\n"
        "📋 Privacy Policy: We respect your privacy. All chats are anonymous. Use /policy to view our privacy policy.\n\n"
        "Let's get you started! What would you like to be called? (You can skip by typing /skip - max 32 characters)"
    )
    
    await update.message.reply_text(welcome_text)


async def handle_onboarding_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages during onboarding"""
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    text = update.message.text.strip() if update.message.text else ""
    
    state = await get_onboarding_state(user_id)
    if not state:
        # Not in onboarding, ignore
        return
    
    step = state.get("step")
    
    if step == "welcome" or step == "display_name":
        # Collect display name
        if text.lower() == "/skip":
            state["display_name"] = None
        else:
            is_valid, error = validate_display_name(text)
            if not is_valid:
                await update.message.reply_text(f"❌ {error}\nPlease try again or type /skip:")
                return
            state["display_name"] = text if text else None
        
        state["step"] = "gender"
        await set_onboarding_state(user_id, state)
        
        await update.message.reply_text(
            "What is your gender?\n\n"
            "1. Male\n"
            "2. Female\n"
            "3. Other\n"
            "4. Prefer not to say\n\n"
            "Reply with the number (1-4):"
        )
        return
    
    if step == "gender":
        # Collect gender
        gender_map = {"1": GENDER_MALE, "2": GENDER_FEMALE, "3": GENDER_OTHER, "4": GENDER_PREFER_NOT_SAY}
        if text in gender_map:
            state["gender"] = gender_map[text]
            state["step"] = "language"
            await set_onboarding_state(user_id, state)
            
            await update.message.reply_text(
                "What language would you prefer to chat in?\n\n"
                "1. Malayalam\n"
                "2. English\n"
                "3. Hindi\n"
                "4. Any\n\n"
                "Reply with the number (1-4):"
            )
        else:
            await update.message.reply_text("Please reply with 1, 2, 3, or 4:")
        return
    
    if step == "language":
        # Collect language preference
        lang_map = {"1": LANGUAGE_MALAYALAM, "2": LANGUAGE_ENGLISH, "3": LANGUAGE_HINDI, "4": LANGUAGE_ANY}
        if text in lang_map:
            state["language_preference"] = lang_map[text]
            state["step"] = "age"
            await set_onboarding_state(user_id, state)
            
            await update.message.reply_text(
                "What is your age range? (Optional - type /skip to skip)\n\n"
                "Format: 18-25, 26-35, etc."
            )
        else:
            await update.message.reply_text("Please reply with 1, 2, 3, or 4:")
        return
    
    if step == "age":
        # Collect age range (optional)
        if text.lower() == "/skip":
            state["age_range"] = None
        else:
            is_valid, error = validate_age_range(text)
            if not is_valid:
                await update.message.reply_text(f"❌ {error}\nPlease try again or type /skip:")
                return
            state["age_range"] = text
        
        # Complete onboarding
        await complete_onboarding(update, context, state)


async def complete_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
    """Complete onboarding and create user account"""
    user = update.effective_user
    user_id = user.id
    username = user.username
    
    try:
        # Create user in database
        await execute_query(
            """
            INSERT INTO users (
                id, username, display_name, gender, language_preference, age_range,
                created_at, last_active, referral_by
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW(), $7)
            """,
            user_id,
            username,
            state.get("display_name"),
            state.get("gender", GENDER_UNKNOWN),
            state.get("language_preference", LANGUAGE_ANY),
            state.get("age_range"),
            state.get("referral_by")
        )
        
        # Process referral if present
        if state.get("referral_by"):
            try:
                referrer_id = int(state["referral_by"][len(REFERRAL_PAYLOAD_PREFIX):])
                await process_referral(referrer_id, user_id)
            except (ValueError, Exception) as e:
                logger.error(f"Error processing referral: {e}")
        
        # Clear onboarding state
        await clear_onboarding_state(user_id)
        
        # Set user state to idle
        redis_client = await get_redis()
        await redis_client.setex(f"user_state:{user_id}", 300, "idle")
        
        await update.message.reply_text(
            "✅ Registration complete!\n\n"
            "Use /next to find a chat partner.\n"
            "Other commands:\n"
            "/stop - End current chat\n"
            "/report - Report a user\n"
            "/block - Block a user\n"
            "/invite - Get your referral link\n"
            "/language - Change language preference"
        )
        
        logger.info(f"User {user_id} completed onboarding")
    except Exception as e:
        logger.error(f"Error completing onboarding: {e}")
        await update.message.reply_text(
            "❌ An error occurred during registration. Please try /start again."
        )

