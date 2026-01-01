"""
Chat handler for message forwarding during active chats
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.connection import fetch_query, execute_query
from bot.services.matchmaking import get_user_pair
from bot.services.moderation import sanitize_message
from bot.services.rate_limiter import check_rate_limit
from bot.handlers.onboarding import get_onboarding_state, handle_onboarding_message
import logging

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages (during active chat)"""
    user = update.effective_user
    if not user or not update.message or not update.message.text:
        return
    
    user_id = user.id
    message_text = update.message.text
    
    # Check if user is in onboarding
    state = await get_onboarding_state(user_id)
    if state:
        await handle_onboarding_message(update, context)
        return
    
    # Check rate limit
    if not await check_rate_limit(user_id):
        await update.message.reply_text(
            "⏱️ You're sending messages too fast. Please wait a moment."
        )
        return
    
    # Get current pair
    pair_id = await get_user_pair(user_id)
    if not pair_id:
        # Not in a chat, show main menu
        from bot.utils.keyboards import get_main_menu_keyboard
        await update.message.reply_text(
            "💬 You're not in a chat right now.\n\n"
            "Tap below to find someone to chat with:",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Sanitize and validate message
    sanitized, is_valid, warning = sanitize_message(message_text)
    if not is_valid:
        await update.message.reply_text(f"❌ {warning}")
        return
    
    # Get pair info
    pair_data = await fetch_query(
        "SELECT user_a, user_b, is_active FROM pairs WHERE pair_id = $1",
        pair_id
    )
    
    if not pair_data or not pair_data['is_active']:
        from bot.utils.keyboards import get_main_menu_keyboard
        await update.message.reply_text(
            "💬 This chat has ended.\n\n"
            "Tap below to find someone new:",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Get partner ID
    partner_id = pair_data['user_b'] if pair_data['user_a'] == user_id else pair_data['user_a']
    
    # Store message in database
    try:
        await execute_query(
            """
            INSERT INTO messages (pair_id, from_id, content, created_at)
            VALUES ($1, $2, $3, NOW())
            """,
            pair_id, user_id, sanitized
        )
        
        # Update last_message_at
        await execute_query(
            "UPDATE pairs SET last_message_at = NOW() WHERE pair_id = $1",
            pair_id
        )
    except Exception as e:
        logger.error(f"Error storing message: {e}")
    
    # Forward message to partner
    try:
        from telegram import Bot
        bot = Bot(token=context.bot.token)
        await bot.send_message(
            chat_id=partner_id,
            text=sanitized
        )
    except Exception as e:
        logger.error(f"Error forwarding message to partner: {e}")
        await update.message.reply_text(
            "❌ Error sending message. Your partner may have left the chat."
        )

