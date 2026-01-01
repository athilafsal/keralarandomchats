"""
Callback query handlers for inline buttons
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.connection import fetch_query, execute_query
from bot.services.matchmaking import add_to_queue, try_match, remove_from_queue, get_user_pair, end_pair, create_pair
from bot.services.admin_service import check_admin_access
from bot.handlers.onboarding import get_onboarding_state, set_onboarding_state, complete_onboarding, clear_onboarding_state
from bot.handlers.callbacks_profile import handle_profile_edit, handle_partner_preference, handle_profile_edit_field
from bot.utils.keyboards import (
    get_gender_keyboard, get_language_keyboard, get_age_range_keyboard,
    get_main_menu_keyboard, get_chat_actions_keyboard, get_waiting_keyboard,
    get_admin_keyboard, get_settings_keyboard, get_skip_keyboard
)
from config.constants import (
    GENDER_UNKNOWN, GENDER_MALE, GENDER_FEMALE, GENDER_OTHER, GENDER_PREFER_NOT_SAY,
    LANGUAGE_MALAYALAM, LANGUAGE_ENGLISH, LANGUAGE_HINDI, LANGUAGE_ANY,
    USER_STATE_WAITING, GENDER_MAP
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
    elif data == "settings":
        await handle_settings(query, context)
    elif data.startswith("settings_"):
        await handle_settings_callback(query, context, data)
    
    # Handle main menu callbacks
    elif data == "my_stats":
        await handle_my_stats(query, context)
    elif data == "invite":
        await handle_invite_callback(query, context)
    elif data == "help":
        await handle_help(query, context)
    elif data.startswith("profile_edit_"):
        await handle_profile_edit_field(query, context, data)
    
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
    
    # Check if this is for partner preference
    from bot.services.redis_client import get_redis
    redis_client = await get_redis()
    is_partner_pref = await redis_client.get(f"editing_partner_pref:{user_id}")
    
    if is_partner_pref:
        # Update partner preference
        await redis_client.delete(f"editing_partner_pref:{user_id}")
        await execute_query(
            "UPDATE users SET gender_preference = $1 WHERE id = $2",
            gender, user_id
        )
        # Get updated settings keyboard
        user_data = await fetch_query("SELECT unlocked_features FROM users WHERE id = $1", user_id)
        has_partner_pref = False
        if user_data:
            unlocked = user_data.get('unlocked_features') or {}
            if isinstance(unlocked, str):
                import json
                unlocked = json.loads(unlocked) if unlocked else {}
            has_partner_pref = unlocked.get('partner_preference', False)
        await query.edit_message_text(
            f"✅ Partner preference updated to {GENDER_MAP.get(gender, 'Unknown')}!\n\n"
            "Choose an option:",
            reply_markup=get_settings_keyboard(has_partner_preference=has_partner_pref)
        )
        return
    
    # Check if this is for profile editing
    is_profile_edit = await redis_client.get(f"editing_profile_gender:{user_id}")
    if is_profile_edit:
        await redis_client.delete(f"editing_profile_gender:{user_id}")
        await execute_query(
            "UPDATE users SET gender = $1 WHERE id = $2",
            gender, user_id
        )
        await query.edit_message_text(
            f"✅ Gender updated to {GENDER_MAP.get(gender, 'Unknown')}!\n\n"
            "Choose an option:",
            reply_markup=get_settings_keyboard(has_partner_preference=False)
        )
        return
    
    # Otherwise, it's onboarding
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
    
    # Check if user is in onboarding
    state = await get_onboarding_state(user_id)
    if state:
        # Update onboarding state
        state["language_preference"] = language
        state["step"] = "age"
        await set_onboarding_state(user_id, state)
        
        await query.edit_message_text(
            "📅 What is your age range? (Optional)",
            reply_markup=get_age_range_keyboard()
        )
    else:
        # User is updating language from settings
        user_data = await fetch_query("SELECT id FROM users WHERE id = $1", user_id)
        if user_data:
            # Update user's language preference
            await execute_query(
                "UPDATE users SET language_preference = $1 WHERE id = $2",
                language, user_id
            )
            lang_names = {
                LANGUAGE_MALAYALAM: "Malayalam",
                LANGUAGE_ENGLISH: "English",
                LANGUAGE_HINDI: "Hindi",
                LANGUAGE_ANY: "Any"
            }
            await query.edit_message_text(
                f"✅ Language preference updated to {lang_names.get(language, 'Any')}!\n\n"
                "Choose an option:",
                reply_markup=get_settings_keyboard()
            )
        else:
            await query.edit_message_text("Please start with /start to register first.")


async def handle_age_callback(query, context, data):
    """Handle age range selection callback"""
    user_id = query.from_user.id
    
    # Check if this is for profile editing
    from bot.services.redis_client import get_redis
    redis_client = await get_redis()
    is_profile_edit = await redis_client.get(f"editing_profile_age:{user_id}")
    
    if is_profile_edit:
        await redis_client.delete(f"editing_profile_age:{user_id}")
        
        if data == "age_any":
            age_range = None
        else:
            age_range = data.replace("age_", "")
        
        await execute_query(
            "UPDATE users SET age_range = $1 WHERE id = $2",
            age_range, user_id
        )
        
        age_text = age_range if age_range else "Any"
        await query.edit_message_text(
            f"✅ Age range updated to: {age_text}!\n\n"
            "Choose an option:",
            reply_markup=get_settings_keyboard(has_partner_preference=False)
        )
        return
    
    # Otherwise, it's onboarding
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
    
    try:
        if not await check_admin_access(user_id):
            await query.answer("Admin access required.", show_alert=True)
            return
        
        # Handle different admin actions
        if data == "admin_list_online":
        from bot.services.admin_service import get_online_stats
        stats = await get_online_stats()
        
        message = "📊 Online Statistics:\n\n"
        message += f"⏳ Waiting users: {stats.get('waiting_users', 0)}\n"
        message += f"💬 Chatting users: {stats.get('chatting_users', 0)}\n"
        message += f"🔗 Active pairs: {stats.get('active_pairs', 0)}\n"
        
        queue_sizes = stats.get('queue_sizes', {})
        if queue_sizes:
            message += "\n📋 Queue sizes:\n"
            for queue, size in list(queue_sizes.items())[:5]:  # Show first 5
                message += f"• {queue}: {size}\n"
        
            try:
                await query.edit_message_text(
                    message,
                    reply_markup=get_admin_keyboard()
                )
            except Exception as e:
                logger.error(f"Error editing message for admin_list_online: {e}")
                await query.message.reply_text(
                    message,
                    reply_markup=get_admin_keyboard()
                )
        
        elif data == "admin_stats":
        from bot.database.connection import fetch_query
        
        # Get basic statistics
        total_users_row = await fetch_query("SELECT COUNT(*) as count FROM users")
        total_users_count = total_users_row['count'] if total_users_row else 0
        
        active_pairs_row = await fetch_query("SELECT COUNT(*) as count FROM pairs WHERE is_active = true")
        active_pairs_count = active_pairs_row['count'] if active_pairs_row else 0
        
        banned_users_row = await fetch_query("SELECT COUNT(*) as count FROM users WHERE is_banned = true")
        banned_users_count = banned_users_row['count'] if banned_users_row else 0
        
        pending_reports_row = await fetch_query("SELECT COUNT(*) as count FROM reports WHERE status = 'pending'")
        pending_reports_count = pending_reports_row['count'] if pending_reports_row else 0
        
        message = "📈 Statistics:\n\n"
        message += f"👥 Total users: {total_users_count}\n"
        message += f"🔗 Active pairs: {active_pairs_count}\n"
        message += f"🚫 Banned users: {banned_users_count}\n"
        message += f"⚠️ Pending reports: {pending_reports_count}\n"
        
            try:
                await query.edit_message_text(
                    message,
                    reply_markup=get_admin_keyboard()
                )
            except Exception as e:
                logger.error(f"Error editing message for admin_stats: {e}")
                await query.message.reply_text(
                    message,
                    reply_markup=get_admin_keyboard()
                )
        
        elif data == "admin_view_pair_menu":
        # Store pending action in Redis
        from bot.services.redis_client import get_redis
        redis_client = await get_redis()
        await redis_client.setex(f"admin_pending:{user_id}", 300, "view_pair")
        
            try:
                await query.edit_message_text(
                    "🔍 View Pair Info\n\n"
                    "Please send the user_id you want to view pair info for:",
                    reply_markup=get_admin_keyboard()
                )
            except Exception as e:
                logger.error(f"Error editing message for admin_view_pair_menu: {e}")
                await query.message.reply_text(
                    "🔍 View Pair Info\n\n"
                    "Please send the user_id you want to view pair info for:",
                    reply_markup=get_admin_keyboard()
                )
        
        elif data == "admin_force_pair_menu":
        # Store pending action
        from bot.services.redis_client import get_redis
        redis_client = await get_redis()
        await redis_client.setex(f"admin_pending:{user_id}", 300, "force_pair")
        
            try:
                await query.edit_message_text(
                    "🔗 Force Pair Users\n\n"
                    "Please send two user_ids separated by space:\n"
                    "Example: `123456789 987654321`",
                    reply_markup=get_admin_keyboard(),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Error editing message for admin_force_pair_menu: {e}")
                await query.message.reply_text(
                    "🔗 Force Pair Users\n\n"
                    "Please send two user_ids separated by space:\n"
                    "Example: `123456789 987654321`",
                    reply_markup=get_admin_keyboard(),
                    parse_mode='Markdown'
                )
        
        elif data == "admin_ban_menu":
        # Store pending action
        from bot.services.redis_client import get_redis
        redis_client = await get_redis()
        await redis_client.setex(f"admin_pending:{user_id}", 300, "ban")
        
            try:
                await query.edit_message_text(
                    "🚫 Ban User\n\n"
                    "Please send the user_id you want to ban:",
                    reply_markup=get_admin_keyboard()
                )
            except Exception as e:
                logger.error(f"Error editing message for admin_ban_menu: {e}")
                await query.message.reply_text(
                    "🚫 Ban User\n\n"
                    "Please send the user_id you want to ban:",
                    reply_markup=get_admin_keyboard()
                )
        
        elif data == "admin_unban_menu":
        # Store pending action
        from bot.services.redis_client import get_redis
        redis_client = await get_redis()
        await redis_client.setex(f"admin_pending:{user_id}", 300, "unban")
        
            try:
                await query.edit_message_text(
                    "✅ Unban User\n\n"
                    "Please send the user_id you want to unban:",
                    reply_markup=get_admin_keyboard()
                )
            except Exception as e:
                logger.error(f"Error editing message for admin_unban_menu: {e}")
                await query.message.reply_text(
                    "✅ Unban User\n\n"
                    "Please send the user_id you want to unban:",
                    reply_markup=get_admin_keyboard()
                )
        
        elif data == "admin_disconnect_menu":
        # Store pending action
        from bot.services.redis_client import get_redis
        redis_client = await get_redis()
        await redis_client.setex(f"admin_pending:{user_id}", 300, "disconnect")
        
            try:
                await query.edit_message_text(
                    "🔌 Disconnect User\n\n"
                    "Please send the user_id you want to disconnect from their chat:",
                    reply_markup=get_admin_keyboard()
                )
            except Exception as e:
                logger.error(f"Error editing message for admin_disconnect_menu: {e}")
                await query.message.reply_text(
                    "🔌 Disconnect User\n\n"
                    "Please send the user_id you want to disconnect from their chat:",
                    reply_markup=get_admin_keyboard()
                )
        
        else:
            try:
                await query.edit_message_text(
                    f"Admin feature coming soon!\n\n"
                    f"Received callback: {data}",
                    reply_markup=get_admin_keyboard()
                )
            except Exception as e:
                logger.error(f"Error editing message for unknown admin callback: {e}")
                await query.message.reply_text(
                    f"Admin feature coming soon!\n\n"
                    f"Received callback: {data}",
                    reply_markup=get_admin_keyboard()
                )
    except Exception as e:
        logger.error(f"Error in admin callback {data}: {e}", exc_info=True)
        try:
            await query.answer(f"Error: {str(e)}", show_alert=True)
        except:
            pass
        try:
            await query.message.reply_text(
                f"❌ Error: {str(e)}\n\n"
                "Please try again.",
                reply_markup=get_admin_keyboard()
            )
        except:
            pass


async def handle_settings(query, context):
    """Handle settings menu"""
    user_id = query.from_user.id
    
    # Check if user has partner preference unlocked
    user_data = await fetch_query(
        "SELECT unlocked_features FROM users WHERE id = $1",
        user_id
    )
    has_partner_preference = False
    if user_data:
        unlocked = user_data.get('unlocked_features') or {}
        if isinstance(unlocked, str):
            import json
            unlocked = json.loads(unlocked) if unlocked else {}
        has_partner_preference = unlocked.get('partner_preference', False)
    
    await query.edit_message_text(
        "⚙️ Settings\n\n"
        "Choose an option:",
        reply_markup=get_settings_keyboard(has_partner_preference=has_partner_preference)
    )


async def handle_settings_callback(query, context, data):
    """Handle settings callbacks"""
    user_id = query.from_user.id
    
    if data == "settings_language":
        await query.edit_message_text(
            "🌐 Select your preferred language:",
            reply_markup=get_language_keyboard()
        )
    elif data == "settings_profile":
        await handle_profile_edit(query, context)
    elif data == "settings_partner_preference":
        await handle_partner_preference(query, context)


async def handle_my_stats(query, context):
    """Handle my stats button"""
    user_id = query.from_user.id
    
    # Check if user exists
    user_data = await fetch_query("SELECT id FROM users WHERE id = $1", user_id)
    if not user_data:
        await query.edit_message_text("Please start with /start to register first.")
        return
    
    # Get stats
    from bot.services.stats import get_user_stats
    stats = await get_user_stats(user_id)
    
    if not stats:
        await query.edit_message_text("❌ Error loading stats. Please try again.")
        return
    
    # Format stats message
    message = "📊 Your Statistics\n\n"
    message += f"💬 Total Chats: {stats.get('total_chats', 0)}\n"
    message += f"💭 Messages Sent: {stats.get('messages_sent', 0)}\n"
    message += f"🔗 Referrals: {stats.get('referrals_count', 0)}/5\n"
    
    if stats.get('account_age_days', 0) > 0:
        message += f"📅 Account Age: {stats['account_age_days']} days\n"
    
    if stats.get('has_unlocked_features'):
        message += "\n✅ Premium Features Unlocked!"
        unlocked = stats.get('unlocked_features', {})
        if unlocked.get('see_gender'):
            message += "\n• See gender preference"
        if unlocked.get('search_by_age'):
            message += "\n• Search by age range"
    else:
        remaining = 5 - stats.get('referrals_count', 0)
        if remaining > 0:
            message += f"\n🔓 Unlock premium features in {remaining} more referral(s)!"
    
    await query.edit_message_text(
        message,
        reply_markup=get_main_menu_keyboard()
    )


async def handle_invite_callback(query, context):
    """Handle invite friends button"""
    user_id = query.from_user.id
    
    # Check if user exists
    user_data = await fetch_query("SELECT id FROM users WHERE id = $1", user_id)
    if not user_data:
        await query.edit_message_text("Please start with /start to register first.")
        return
    
    # Get bot username
    bot_info = await context.bot.get_me()
    bot_username = bot_info.username
    
    # Generate referral link
    from bot.services.referrals import generate_referral_link, get_referral_count, get_unlocked_features
    referral_link = generate_referral_link(bot_username, user_id)
    
    # Get referral count
    count = await get_referral_count(user_id)
    
    # Get unlocked features
    features = await get_unlocked_features(user_id)
    has_unlocked = features.get('see_gender', False) or features.get('search_by_age', False)
    
    message = (
        "🎁 Invite your friends!\n\n"
        f"Share this link:\n`{referral_link}`\n\n"
        f"Referrals: {count}/5\n\n"
    )
    
    if has_unlocked:
        message += "✅ You've unlocked premium features!\n\n"
    else:
        message += f"🔓 Unlock premium features after {5 - count} more referral(s)!\n\n"
    
    message += "Premium features:\n• See gender preference\n• Search by age range"
    
    await query.edit_message_text(
        message,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )


async def handle_help(query, context):
    """Handle help button"""
    help_text = (
        "ℹ️ Help & Commands\n\n"
        "📋 **Main Commands:**\n"
        "• `/start` - Start or restart the bot\n"
        "• `/next` - Find a new chat partner\n"
        "• `/stop` - End current chat\n"
        "• `/report` - Report a user\n"
        "• `/block` - Block a user\n"
        "• `/invite` - Get your referral link\n"
        "• `/language` - Change language preference\n"
        "• `/policy` - View privacy policy\n\n"
        "🎯 **How to Use:**\n"
        "1. Tap 'Find Chat' to start searching\n"
        "2. Wait for a match\n"
        "3. Start chatting!\n"
        "4. Use buttons to manage your chat\n\n"
        "💡 **Tips:**\n"
        "• All chats are anonymous\n"
        "• Be respectful to others\n"
        "• Report inappropriate behavior\n"
        "• Invite friends to unlock premium features"
    )
    
    await query.edit_message_text(
        help_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )

