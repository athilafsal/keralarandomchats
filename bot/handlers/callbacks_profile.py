"""
Profile editing handlers for callbacks
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.database.connection import fetch_query, execute_query
from bot.utils.keyboards import get_gender_keyboard, get_age_range_keyboard, get_settings_keyboard
from config.constants import GENDER_MAP
import logging

logger = logging.getLogger(__name__)


async def handle_profile_edit(query, context):
    """Handle profile editing menu"""
    user_id = query.from_user.id
    
    # Get current profile
    user_data = await fetch_query(
        """
        SELECT display_name, gender, age_range 
        FROM users WHERE id = $1
        """,
        user_id
    )
    
    if not user_data:
        await query.edit_message_text("Please start with /start to register first.")
        return
    
    display_name = user_data.get('display_name') or "Not set"
    gender = user_data.get('gender', 0)
    age_range = user_data.get('age_range') or "Not set"
    
    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit Display Name", callback_data="profile_edit_name"),
            InlineKeyboardButton("👤 Edit Gender", callback_data="profile_edit_gender"),
        ],
        [
            InlineKeyboardButton("📅 Edit Age Range", callback_data="profile_edit_age"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Settings", callback_data="settings"),
        ]
    ]
    
    profile_text = (
        "👤 Your Profile\n\n"
        f"Display Name: {display_name}\n"
        f"Gender: {GENDER_MAP.get(gender, 'Unknown')}\n"
        f"Age Range: {age_range}\n\n"
        "Select what you want to edit:"
    )
    
    await query.edit_message_text(
        profile_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_partner_preference(query, context):
    """Handle partner preference selection"""
    user_id = query.from_user.id
    
    # Check if unlocked
    user_data = await fetch_query(
        "SELECT unlocked_features FROM users WHERE id = $1",
        user_id
    )
    
    if not user_data:
        await query.edit_message_text("Please start with /start to register first.")
        return
    
    unlocked = user_data.get('unlocked_features') or {}
    if isinstance(unlocked, str):
        import json
        unlocked = json.loads(unlocked) if unlocked else {}
    
    if not unlocked.get('partner_preference', False):
        await query.edit_message_text(
            "🔒 Partner Preference is locked!\n\n"
            "Unlock this feature by referring 3 users.\n"
            "Use /invite to get your referral link.",
            reply_markup=get_settings_keyboard(has_partner_preference=False)
        )
        return
    
    # Get current preference
    user_pref_data = await fetch_query(
        "SELECT gender_preference FROM users WHERE id = $1",
        user_id
    )
    current_pref = user_pref_data.get('gender_preference', 0) if user_pref_data else 0
    
    current_text = GENDER_MAP.get(current_pref, "Any")
    
    await query.edit_message_text(
        f"💑 Partner Preference\n\n"
        f"Current preference: {current_text}\n\n"
        "Select your preferred partner gender:",
        reply_markup=get_gender_keyboard()
    )
    
    # Store that this is for partner preference
    from bot.services.redis_client import get_redis
    redis_client = await get_redis()
    await redis_client.setex(f"editing_partner_pref:{user_id}", 300, "1")


async def handle_profile_edit_field(query, context, data):
    """Handle profile field editing"""
    user_id = query.from_user.id
    
    if data == "profile_edit_name":
        # Store editing state
        from bot.services.redis_client import get_redis
        redis_client = await get_redis()
        await redis_client.setex(f"editing_profile_name:{user_id}", 300, "1")
        
        await query.edit_message_text(
            "✏️ Edit Display Name\n\n"
            "Please send your new display name (max 32 characters):\n"
            "Or send /cancel to cancel."
        )
    elif data == "profile_edit_gender":
        # Store editing state
        from bot.services.redis_client import get_redis
        redis_client = await get_redis()
        await redis_client.setex(f"editing_profile_gender:{user_id}", 300, "1")
        
        await query.edit_message_text(
            "👤 Edit Gender\n\n"
            "Select your gender:",
            reply_markup=get_gender_keyboard()
        )
    elif data == "profile_edit_age":
        # Store editing state
        from bot.services.redis_client import get_redis
        redis_client = await get_redis()
        await redis_client.setex(f"editing_profile_age:{user_id}", 300, "1")
        
        await query.edit_message_text(
            "📅 Edit Age Range\n\n"
            "Select your age range:",
            reply_markup=get_age_range_keyboard()
        )

