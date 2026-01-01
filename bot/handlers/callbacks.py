"""
Callback query handlers for inline buttons
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.connection import fetch_query, execute_query
from bot.services.matchmaking import add_to_queue, try_match, remove_from_queue, get_user_pair, end_pair
from bot.services.admin_service import check_admin_access
from bot.handlers.onboarding import get_onboarding_state, set_onboarding_state, complete_onboarding, clear_onboarding_state
from bot.utils.keyboards import (
    get_gender_keyboard, get_language_keyboard, get_age_range_keyboard,
    get_main_menu_keyboard, get_chat_actions_keyboard, get_waiting_keyboard,
    get_admin_keyboard, get_settings_keyboard, get_skip_keyboard
)
from config.constants import (
    GENDER_MALE, GENDER_FEMALE, GENDER_OTHER, GENDER_PREFER_NOT_SAY,
    LANGUAGE_MALAYALAM, LANGUAGE_ENGLISH, LANGUAGE_HINDI, LANGUAGE_ANY,
    USER_STATE_WAITING
)
import logging

logger = logging.getLogger(__name__)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries from inline buttons"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()  # Acknowledge the callback
    
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    data = query.data
    
    # Handle onboarding callbacks
    if data.startswith("gender_"):
        await handle_gender_callback(query, context, data)
    elif data.startswith("lang_"):
        await handle_language_callback(query, context, data)
    elif data.startswith("age_"):
        await handle_age_callback(query, context, data)
    elif data == "skip":
        await handle_skip_callback(query, context)
    
    # Handle main menu callbacks
    elif data == "find_chat":
        await handle_find_chat(query, context)
    elif data == "main_menu":
        await handle_main_menu(query, context)
    elif data == "stop_chat":
        await handle_stop_chat(query, context)
    elif data == "next_person":
        await handle_next_person(query, context)
    elif data == "cancel_search":
        await handle_cancel_search(query, context)
    elif data == "block_user":
        await handle_block_user(query, context)
    elif data == "report_user":
        await handle_report_user(query, context)
    
    # Handle admin callbacks
    elif data.startswith("admin_"):
        await handle_admin_callback(query, context, data)
    
    # Handle settings callbacks
    elif data.startswith("settings_"):
        await handle_settings_callback(query, context, data)
    
    else:
        await query.edit_message_text("❌ Unknown action. Please try again.")


async def handle_gender_callback(query, context, data):
    """Handle gender selection callback"""
    user_id = query.from_user.id
    gender_map = {
        "gender_1": GENDER_MALE,
        "gender_2": GENDER_FEMALE,
        "gender_3": GENDER_OTHER,
        "gender_4": GENDER_PREFER_NOT_SAY
    }
    
    gender = gender_map.get(data)
    if not gender:
        await query.edit_message_text("❌ Invalid selection. Please try again.")
        return
    
    state = await get_onboarding_state(user_id)
    if not state:
        await query.edit_message_text("❌ Onboarding session expired. Please use /start again.")
        return
    
    state["gender"] = gender
    state["step"] = "language"
    await set_onboarding_state(user_id, state)
    
    await query.edit_message_text(
        "🌐 What language would you prefer to chat in?",
        reply_markup=get_language_keyboard()
    )


async def handle_language_callback(query, context, data):
    """Handle language selection callback"""
    user_id = query.from_user.id
    lang_map = {
        "lang_malayalam": LANGUAGE_MALAYALAM,
        "lang_english": LANGUAGE_ENGLISH,
        "lang_hindi": LANGUAGE_HINDI,
        "lang_any": LANGUAGE_ANY
    }
    
    language = lang_map.get(data)
    if not language:
        await query.edit_message_text("❌ Invalid selection. Please try again.")
        return
    
    state = await get_onboarding_state(user_id)
    if not state:
        await query.edit_message_text("❌ Onboarding session expired. Please use /start again.")
        return
    
    state["language_preference"] = language
    state["step"] = "age"
    await set_onboarding_state(user_id, state)
    
    await query.edit_message_text(
        "📅 What is your age range? (Optional)",
        reply_markup=get_age_range_keyboard()
    )


async def handle_age_callback(query, context, data):
    """Handle age range selection callback"""
    user_id = query.from_user.id
    
    state = await get_onboarding_state(user_id)
    if not state:
        await query.edit_message_text("❌ Onboarding session expired. Please use /start again.")
        return
    
    if data == "age_any":
        state["age_range"] = None
    else:
        # Extract age range from callback data (e.g., "age_18-24" -> "18-24")
        state["age_range"] = data.replace("age_", "")
    
    # Complete onboarding
    from bot.handlers.onboarding import complete_onboarding
    await complete_onboarding_callback(query, context, state)


async def handle_skip_callback(query, context):
    """Handle skip button callback"""
    user_id = query.from_user.id
    state = await get_onboarding_state(user_id)
    
    if not state:
        await query.edit_message_text("❌ Onboarding session expired. Please use /start again.")
        return
    
    step = state.get("step")
    
    if step == "display_name":
        state["display_name"] = None
        state["step"] = "gender"
        await set_onboarding_state(user_id, state)
        await query.edit_message_text(
            "👤 What is your gender?",
            reply_markup=get_gender_keyboard()
        )
    elif step == "age":
        state["age_range"] = None
        await complete_onboarding_callback(query, context, state)


async def complete_onboarding_callback(query, context, state):
    """Complete onboarding from callback"""
    user_id = query.from_user.id
    
    try:
        from bot.database.connection import execute_query
        from bot.services.referrals import process_referral
        from config.constants import GENDER_UNKNOWN, LANGUAGE_ANY, REFERRAL_PAYLOAD_PREFIX
        
        # Create user in database
        await execute_query(
            """
            INSERT INTO users (
                id, username, display_name, gender, language_preference, age_range,
                created_at, last_active, referral_by
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW(), $7)
            """,
            user_id,
            query.from_user.username,
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
            except Exception as e:
                logger.error(f"Error processing referral: {e}")
        
        await clear_onboarding_state(user_id)
        
        # Set user state to idle
        from bot.services.redis_client import get_redis
        redis_client = await get_redis()
        await redis_client.setex(f"user_state:{user_id}", 300, "idle")
        
        await query.edit_message_text(
            "✅ Registration complete!\n\n"
            "You're all set! Tap the button below to start chatting:",
            reply_markup=get_main_menu_keyboard()
        )
        
        logger.info(f"User {user_id} completed onboarding")
    except Exception as e:
        logger.error(f"Error completing onboarding: {e}")
        await query.edit_message_text(
            "❌ An error occurred during registration. Please try /start again."
        )


async def handle_find_chat(query, context):
    """Handle find chat button"""
    user_id = query.from_user.id
    
    # Check if user exists
    user_data = await fetch_query("SELECT * FROM users WHERE id = $1", user_id)
    if not user_data:
        await query.edit_message_text("Please start with /start to register first.")
        return
    
    # Check if banned
    if user_data['is_banned']:
        await query.edit_message_text("❌ You have been banned from using this service.")
        return
    
    # Check if already in a chat
    pair_id = await get_user_pair(user_id)
    if pair_id:
        await query.edit_message_text(
            "You're already in a chat! Use the buttons below to manage it:",
            reply_markup=get_chat_actions_keyboard()
        )
        return
    
    # Add to queue
    gender_filter = user_data.get('gender', 0)
    language_preference = user_data.get('language_preference', 'any')
    
    success = await add_to_queue(user_id, gender_filter, language_preference)
    if not success:
        await query.edit_message_text("❌ Failed to join queue. Please try again.")
        return
    
    await query.edit_message_text(
        "🔍 Searching for a chat partner...\n\n"
        "Please wait while we find someone for you to chat with.",
        reply_markup=get_waiting_keyboard()
    )
    
    # Try to match immediately
    matched_id = await try_match(user_id, gender_filter, language_preference)
    if matched_id:
        # Create pair
        from bot.services.matchmaking import create_pair
        pair_id = await create_pair(user_id, matched_id, language_preference)
        if pair_id:
            await query.edit_message_text(
                "✅ Found someone! Start chatting now!\n\n"
                "Use the buttons below to manage your chat:",
                reply_markup=get_chat_actions_keyboard()
            )
        else:
            await query.edit_message_text(
                "✅ Found someone! Start chatting now!\n\n"
                "Use the buttons below to manage your chat:",
                reply_markup=get_chat_actions_keyboard()
            )


async def handle_main_menu(query, context):
    """Handle main menu button"""
    await query.edit_message_text(
        "👋 Welcome to Anonymous Chat!\n\n"
        "Choose an option:",
        reply_markup=get_main_menu_keyboard()
    )


async def handle_stop_chat(query, context):
    """Handle stop chat button"""
    user_id = query.from_user.id
    pair_id = await get_user_pair(user_id)
    
    if not pair_id:
        await query.answer("You're not in a chat.", show_alert=True)
        return
    
    await end_pair(pair_id)
    await query.edit_message_text(
        "⏹️ Chat ended.\n\n"
        "Tap below to find someone new:",
        reply_markup=get_main_menu_keyboard()
    )


async def handle_next_person(query, context):
    """Handle next person button"""
    user_id = query.from_user.id
    
    # End current chat
    pair_id = await get_user_pair(user_id)
    if pair_id:
        await end_pair(pair_id)
    
    # Start new search
    await handle_find_chat(query, context)


async def handle_cancel_search(query, context):
    """Handle cancel search button"""
    user_id = query.from_user.id
    await remove_from_queue(user_id)
    
    await query.edit_message_text(
        "❌ Search cancelled.\n\n"
        "Tap below to try again:",
        reply_markup=get_main_menu_keyboard()
    )


async def handle_block_user(query, context):
    """Handle block user button"""
    user_id = query.from_user.id
    pair_id = await get_user_pair(user_id)
    
    if not pair_id:
        await query.answer("You're not in a chat.", show_alert=True)
        return
    
    # Get partner ID
    pair_data = await fetch_query(
        "SELECT user_a, user_b FROM pairs WHERE pair_id = $1",
        pair_id
    )
    
    if not pair_data:
        await query.answer("Chat not found.", show_alert=True)
        return
    
    partner_id = pair_data['user_b'] if pair_data['user_a'] == user_id else pair_data['user_a']
    
    # Block user
    user_data = await fetch_query("SELECT blocked_users FROM users WHERE id = $1", user_id)
    blocked = user_data.get('blocked_users', []) if user_data else []
    
    if partner_id not in blocked:
        blocked.append(partner_id)
        await execute_query(
            "UPDATE users SET blocked_users = $1 WHERE id = $2",
            blocked, user_id
        )
    
    # End chat
    await end_pair(pair_id)
    
    await query.edit_message_text(
        "🚫 User blocked and chat ended.\n\n"
        "Tap below to find someone new:",
        reply_markup=get_main_menu_keyboard()
    )


async def handle_report_user(query, context):
    """Handle report user button"""
    await query.edit_message_text(
        "⚠️ To report a user, please use the /report command and provide details about the issue.\n\n"
        "Example: /report This user sent inappropriate messages"
    )


async def handle_admin_callback(query, context, data):
    """Handle admin panel callbacks"""
    user_id = query.from_user.id
    
    if not await check_admin_access(user_id):
        await query.answer("Admin access required.", show_alert=True)
        return
    
    # Handle different admin actions
    if data == "admin_list_online":
        from bot.handlers.admin import handle_admin_list_online
        # We need to create a mock update for this
        # For now, just show stats
        stats = await fetch_query("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN last_active > NOW() - INTERVAL '5 minutes' THEN 1 END) as online_users
            FROM users
        """)
        
        await query.edit_message_text(
            f"📊 Online Statistics:\n\n"
            f"👥 Total Users: {stats.get('total_users', 0) if stats else 0}\n"
            f"🟢 Online (last 5 min): {stats.get('online_users', 0) if stats else 0}",
            reply_markup=get_admin_keyboard()
        )
    elif data == "admin_stats":
        await query.edit_message_text(
            "📊 Statistics feature coming soon!",
            reply_markup=get_admin_keyboard()
        )
    else:
        await query.edit_message_text(
            "Admin feature coming soon!",
            reply_markup=get_admin_keyboard()
        )


async def handle_settings_callback(query, context, data):
    """Handle settings callbacks"""
    if data == "settings_language":
        await query.edit_message_text(
            "🌐 Select your preferred language:",
            reply_markup=get_language_keyboard()
        )
    elif data == "settings_profile":
        await query.edit_message_text(
            "👤 Profile settings coming soon!",
            reply_markup=get_settings_keyboard()
        )

