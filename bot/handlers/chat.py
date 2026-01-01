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
    
    # Check for pending admin actions
    from bot.services.redis_client import get_redis
    from bot.services.admin_service import check_admin_access, get_user_pair_info, force_pair_users, ban_user, unban_user, log_admin_action
    from bot.services.matchmaking import get_user_pair, end_pair
    from bot.utils.keyboards import get_admin_keyboard
    
    if await check_admin_access(user_id):
        redis_client = await get_redis()
        pending_action = await redis_client.get(f"admin_pending:{user_id}")
        if pending_action:
            # Clear pending action
            await redis_client.delete(f"admin_pending:{user_id}")
            
            try:
                if pending_action == "view_pair":
                    target_user_id = int(message_text.strip())
                    pair_info = await get_user_pair_info(target_user_id)
                    if pair_info:
                        message = f"🔍 Pair info for user {target_user_id}:\n\n"
                        message += f"Pair ID: {pair_info['pair_id']}\n"
                        message += f"User A: {pair_info['user_a']}\n"
                        message += f"User B: {pair_info['user_b']}\n"
                        message += f"Started: {pair_info['started_at']}\n"
                        message += f"Last message: {pair_info.get('last_message_at', 'N/A')}\n"
                        message += f"Active: {pair_info['is_active']}"
                    else:
                        message = f"User {target_user_id} is not in an active pair."
                    await update.message.reply_text(message, reply_markup=get_admin_keyboard())
                    await log_admin_action(user_id, "view_pair", {"target_user_id": target_user_id})
                    
                elif pending_action == "force_pair":
                    parts = message_text.strip().split()
                    if len(parts) >= 2:
                        user_a = int(parts[0])
                        user_b = int(parts[1])
                        pair_id = await force_pair_users(user_a, user_b)
                        if pair_id:
                            await update.message.reply_text(
                                f"✅ Created pair {pair_id} between users {user_a} and {user_b}",
                                reply_markup=get_admin_keyboard()
                            )
                            await log_admin_action(user_id, "force_pair", {"user_a": user_a, "user_b": user_b, "pair_id": pair_id})
                        else:
                            await update.message.reply_text("❌ Failed to create pair.", reply_markup=get_admin_keyboard())
                    else:
                        await update.message.reply_text("Please send two user_ids separated by space.", reply_markup=get_admin_keyboard())
                        
                elif pending_action == "ban":
                    target_user_id = int(message_text.strip())
                    success = await ban_user(target_user_id, user_id)
                    if success:
                        await update.message.reply_text(f"✅ User {target_user_id} has been banned.", reply_markup=get_admin_keyboard())
                    else:
                        await update.message.reply_text(f"❌ Failed to ban user {target_user_id}.", reply_markup=get_admin_keyboard())
                    await log_admin_action(user_id, "ban", {"target_user_id": target_user_id})
                    
                elif pending_action == "unban":
                    target_user_id = int(message_text.strip())
                    success = await unban_user(target_user_id, user_id)
                    if success:
                        await update.message.reply_text(f"✅ User {target_user_id} has been unbanned.", reply_markup=get_admin_keyboard())
                    else:
                        await update.message.reply_text(f"❌ Failed to unban user {target_user_id}.", reply_markup=get_admin_keyboard())
                    await log_admin_action(user_id, "unban", {"target_user_id": target_user_id})
                    
                elif pending_action == "disconnect":
                    target_user_id = int(message_text.strip())
                    pair_id = await get_user_pair(target_user_id)
                    if pair_id:
                        await end_pair(pair_id, target_user_id)
                        await update.message.reply_text(f"✅ Disconnected user {target_user_id} from chat.", reply_markup=get_admin_keyboard())
                        await log_admin_action(user_id, "disconnect", {"target_user_id": target_user_id, "pair_id": pair_id})
                    else:
                        await update.message.reply_text(f"User {target_user_id} is not in an active chat.", reply_markup=get_admin_keyboard())
            except ValueError:
                await update.message.reply_text("❌ Invalid input. Please send a valid user_id.", reply_markup=get_admin_keyboard())
            except Exception as e:
                logger.error(f"Error handling admin action: {e}")
                await update.message.reply_text(f"❌ Error: {str(e)}", reply_markup=get_admin_keyboard())
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

