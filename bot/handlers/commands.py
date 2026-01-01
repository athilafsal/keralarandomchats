"""
Command handlers for bot commands
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.connection import fetch_query, fetch_all, execute_query
from bot.services.matchmaking import add_to_queue, try_match, create_pair, remove_from_queue, get_user_pair, end_pair
from bot.services.redis_client import get_redis
from bot.services.referrals import generate_referral_link, get_referral_count, get_unlocked_features
from bot.services.rate_limiter import check_rate_limit
from bot.handlers.onboarding import get_onboarding_state, handle_onboarding_message
from bot.utils.keyboards import get_main_menu_keyboard, get_chat_actions_keyboard, get_waiting_keyboard
from config.constants import (
    USER_STATE_WAITING, USER_STATE_CHATTING, USER_STATE_IDLE, GENDER_UNKNOWN,
    LANGUAGE_ANY, REPORT_CONVERSATION_EXCERPT_SIZE
)
import logging

logger = logging.getLogger(__name__)


async def handle_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /next command - find a new chat partner"""
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    
    # Check if user is in onboarding
    state = await get_onboarding_state(user_id)
    if state:
        await handle_onboarding_message(update, context)
        return
    
    # Check if user exists
    user_data = await fetch_query("SELECT * FROM users WHERE id = $1", user_id)
    if not user_data:
        await update.message.reply_text("Please start with /start to register first.")
        return
    
    # Check if banned
    if user_data['is_banned']:
        await update.message.reply_text("❌ You have been banned from using this service.")
        return
    
    # Check if already in a chat
    pair_id = await get_user_pair(user_id)
    if pair_id:
        await update.message.reply_text(
            "You're already in a chat! Use /stop to end the current chat first."
        )
        return
    
    # Remove from any existing queue
    await remove_from_queue(user_id)
    
    # Get user preferences
    gender_filter = user_data.get('gender', GENDER_UNKNOWN)
    language_preference = user_data.get('language_preference', LANGUAGE_ANY)
    
    # Add to queue
    await add_to_queue(user_id, gender_filter, language_preference)
    
    # Try immediate match
    matched_id = await try_match(user_id, gender_filter, language_preference)
    
    if matched_id:
        # Create pair
        pair_id = await create_pair(user_id, matched_id, language_preference)
        if pair_id:
            # Get matched user's display name if available
            matched_user = await fetch_query("SELECT display_name FROM users WHERE id = $1", matched_id)
            matched_name = matched_user.get('display_name') if matched_user and matched_user.get('display_name') else "Anonymous"
            
            await update.message.reply_text(
                f"✅ You've been paired! You're now chatting with {matched_name}.\n\n"
                "Type /stop to end the chat."
            )
            
            # Notify the matched user
            try:
                from telegram import Bot
                bot = Bot(token=context.bot.token)
                current_name = user_data.get('display_name') or "Anonymous"
                await bot.send_message(
                    chat_id=matched_id,
                    text=f"✅ You've been paired! You're now chatting with {current_name}.\n\nType /stop to end the chat."
                )
            except Exception as e:
                logger.error(f"Error notifying matched user: {e}")
        else:
            await update.message.reply_text("❌ Error creating pair. Please try /next again.")
    else:
        await update.message.reply_text(
            "🔍 Looking for a chat partner... You'll be notified when someone is available.\n\n"
            "Type /stop to cancel."
        )


async def handle_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command - end current chat"""
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    
    # Get current pair
    pair_id = await get_user_pair(user_id)
    
    if not pair_id:
        # Remove from queue if waiting
        removed = await remove_from_queue(user_id)
        if removed:
            await update.message.reply_text("✅ Removed from waiting queue.")
        else:
            await update.message.reply_text("You're not in a chat or waiting queue.")
        return
    
    # End the pair
    await end_pair(pair_id, user_id)
    
    # Get partner ID
    pair_data = await fetch_query(
        "SELECT user_a, user_b FROM pairs WHERE pair_id = $1",
        pair_id
    )
    
    if pair_data:
        partner_id = pair_data['user_b'] if pair_data['user_a'] == user_id else pair_data['user_a']
        
        # Notify partner
        try:
            from telegram import Bot
            bot = Bot(token=context.bot.token)
            await bot.send_message(
                chat_id=partner_id,
                text="Your chat partner has ended the conversation. Use /next to find someone new."
            )
        except Exception as e:
            logger.error(f"Error notifying partner: {e}")
    
    await update.message.reply_text(
        "✅ Chat ended. Use /next to find a new chat partner."
    )


async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command - report a user"""
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    
    # Get current pair
    pair_id = await get_user_pair(user_id)
    if not pair_id:
        await update.message.reply_text("You're not currently in a chat to report.")
        return
    
    # Get partner
    pair_data = await fetch_query(
        "SELECT user_a, user_b FROM pairs WHERE pair_id = $1",
        pair_id
    )
    if not pair_data:
        await update.message.reply_text("Error: Pair not found.")
        return
    
    reported_user_id = pair_data['user_b'] if pair_data['user_a'] == user_id else pair_data['user_a']
    
    # Get conversation excerpt (last N messages)
    import json
    messages = await fetch_all(
        f"""
        SELECT from_id, content, created_at
        FROM messages
        WHERE pair_id = $1
        ORDER BY created_at DESC
        LIMIT {REPORT_CONVERSATION_EXCERPT_SIZE}
        """,
        pair_id
    )
    
    # Convert to JSON-serializable format
    excerpt = []
    for msg in messages:
        excerpt.append({
            "from_id": msg['from_id'],
            "content": msg['content'],
            "created_at": msg['created_at'].isoformat() if hasattr(msg['created_at'], 'isoformat') else str(msg['created_at'])
        })
    
    # Create report
    await execute_query(
        """
        INSERT INTO reports (pair_id, reported_by, reported_user, conversation_excerpt, status, created_at)
        VALUES ($1, $2, $3, $4::jsonb, 'pending', NOW())
        """,
        pair_id, user_id, reported_user_id, json.dumps(excerpt)
    )
    
    # End the pair
    await end_pair(pair_id, user_id)
    
    await update.message.reply_text(
        "✅ Thank you for reporting. We've reviewed your report and taken action.\n\n"
        "The chat has been ended. Use /next to find someone new."
    )
    
    logger.info(f"User {user_id} reported user {reported_user_id}")


async def handle_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /block command - block a user"""
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    
    # Get current pair
    pair_id = await get_user_pair(user_id)
    if not pair_id:
        await update.message.reply_text("You're not currently in a chat to block someone.")
        return
    
    # Get partner
    pair_data = await fetch_query(
        "SELECT user_a, user_b FROM pairs WHERE pair_id = $1",
        pair_id
    )
    if not pair_data:
        await update.message.reply_text("Error: Pair not found.")
        return
    
    blocked_user_id = pair_data['user_b'] if pair_data['user_a'] == user_id else pair_data['user_a']
    
    # Get current blocked users
    user_data = await fetch_query("SELECT blocked_users FROM users WHERE id = $1", user_id)
    blocked_users = user_data.get('blocked_users') if user_data else None
    
    # Handle JSONB format (can be list or dict)
    if blocked_users is None:
        blocked_users = []
    elif isinstance(blocked_users, dict):
        blocked_users = list(blocked_users.values()) if blocked_users else []
    elif not isinstance(blocked_users, list):
        blocked_users = []
    
    if blocked_user_id not in blocked_users:
        blocked_users.append(blocked_user_id)
        
        # Update blocked users
        import json
        await execute_query(
            "UPDATE users SET blocked_users = $1::jsonb WHERE id = $2",
            json.dumps(blocked_users), user_id
        )
    
    # End the pair
    await end_pair(pair_id, user_id)
    
    await update.message.reply_text(
        "✅ User blocked. You won't be matched with them again.\n\n"
        "Use /next to find someone new."
    )
    
    logger.info(f"User {user_id} blocked user {blocked_user_id}")


async def handle_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /invite command - show referral link"""
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    
    # Check if user exists
    user_data = await fetch_query("SELECT id FROM users WHERE id = $1", user_id)
    if not user_data:
        await update.message.reply_text("Please start with /start to register first.")
        return
    
    # Get bot username
    bot_info = await context.bot.get_me()
    bot_username = bot_info.username
    
    # Generate referral link
    referral_link = generate_referral_link(bot_username, user_id)
    
    # Get referral count
    count = await get_referral_count(user_id)
    
    # Get unlocked features
    features = await get_unlocked_features(user_id)
    has_unlocked = features.get('see_gender', False) or features.get('search_by_age', False)
    
    message = (
        "🎁 Invite your friends!\n\n"
        f"Share this link:\n{referral_link}\n\n"
        f"Referrals: {count}/5\n\n"
    )
    
    if has_unlocked:
        message += "✅ You've unlocked premium features!\n"
    else:
        message += f"Unlock premium features after {5 - count} more referrals!\n"
    
    message += "\nPremium features:\n• See gender preference\n• Search by age range"
    
    await update.message.reply_text(message)


async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /language command - change language preference"""
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    
    # Check if user exists
    user_data = await fetch_query("SELECT id FROM users WHERE id = $1", user_id)
    if not user_data:
        await update.message.reply_text("Please start with /start to register first.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "What language would you prefer to chat in?\n\n"
            "1. Malayalam\n"
            "2. English\n"
            "3. Hindi\n"
            "4. Any\n\n"
            "Usage: /language 1 (or 2, 3, 4)"
        )
        return
    
    lang_map = {"1": "malayalam", "2": "english", "3": "hindi", "4": "any"}
    choice = context.args[0]
    
    if choice in lang_map:
        new_lang = lang_map[choice]
        await execute_query(
            "UPDATE users SET language_preference = $1 WHERE id = $2",
            new_lang, user_id
        )
        await update.message.reply_text(f"✅ Language preference updated to {new_lang.capitalize()}.")
    else:
        await update.message.reply_text("Please choose 1, 2, 3, or 4.")


async def handle_policy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /policy command - show privacy policy"""
    policy_text = (
        "🔒 Privacy Policy\n\n"
        "• All chats are anonymous - we don't share your personal information\n"
        "• Messages are stored for moderation purposes (7 days retention)\n"
        "• Admins can view basic metadata and recent messages for moderation\n"
        "• Use /report to flag inappropriate behavior\n"
        "• Use /block to prevent matching with specific users\n"
        "• We respect your privacy and comply with data protection regulations\n\n"
        "By using this service, you agree to our privacy policy."
    )
    await update.message.reply_text(policy_text)

