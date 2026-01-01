"""
Admin command handlers
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.admin_service import (
    grant_admin_access, check_admin_access, log_admin_action,
    get_online_stats, get_user_pair_info, force_pair_users,
    ban_user, unban_user
)
from bot.services.matchmaking import end_pair, get_user_pair
from bot.utils.security import verify_admin_secret
from bot.utils.keyboards import get_admin_keyboard
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - admin authentication and commands"""
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    
    if not context.args or len(context.args) == 0:
        # Check if already admin
        if await check_admin_access(user_id):
            await update.message.reply_text(
                "🔐 Admin Panel\n\n"
                "Select an option:",
                reply_markup=get_admin_keyboard()
            )
        else:
            await update.message.reply_text(
                "🔐 Admin Panel\n\n"
                "To access admin features, use:\n"
                "`/admin <your_secret>`\n\n"
                "Or use the buttons below if already authenticated:",
                reply_markup=get_admin_keyboard()
            )
        return
    
    command = context.args[0]
    
    # Handle authentication
    if command != "list_online" and command != "view_pair" and command != "force_pair" and \
       command != "disconnect" and command != "ban" and command != "unban" and command != "stats":
        # This is likely the secret code for authentication
        secret = " ".join(context.args)
        if verify_admin_secret(secret):
            await grant_admin_access(user_id)
            await log_admin_action(user_id, "admin_login", {})
            await update.message.reply_text(
                "✅ Admin access granted. Session expires in 2 hours.\n\n"
                "Select an option:",
                reply_markup=get_admin_keyboard()
            )
        else:
            await update.message.reply_text("❌ Invalid admin secret.")
        return
    
    # Check admin access for all other commands
    if not await check_admin_access(user_id):
        await update.message.reply_text("❌ Admin access required. Use /admin <secret> to authenticate.")
        return
    
    # Handle admin commands
    if command == "list_online":
        await handle_admin_list_online(update, context)
    elif command == "view_pair":
        await handle_admin_view_pair(update, context)
    elif command == "force_pair":
        await handle_admin_force_pair(update, context)
    elif command == "disconnect":
        await handle_admin_disconnect(update, context)
    elif command == "ban":
        await handle_admin_ban(update, context)
    elif command == "unban":
        await handle_admin_unban(update, context)
    elif command == "stats":
        await handle_admin_stats(update, context)


async def handle_admin_list_online(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin list_online"""
    user_id = update.effective_user.id
    stats = await get_online_stats()
    
    message = "📊 Online Statistics:\n\n"
    message += f"Waiting users: {stats.get('waiting_users', 0)}\n"
    message += f"Chatting users: {stats.get('chatting_users', 0)}\n"
    message += f"Active pairs: {stats.get('active_pairs', 0)}\n\n"
    
    queue_sizes = stats.get('queue_sizes', {})
    if queue_sizes:
        message += "Queue sizes:\n"
        for queue, size in queue_sizes.items():
            message += f"{queue}: {size}\n"
    
    await update.message.reply_text(message)
    await log_admin_action(user_id, "list_online", stats)


async def handle_admin_view_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin view_pair <user_id>"""
    user_id = update.effective_user.id
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /admin view_pair <user_id>")
        return
    
    try:
        target_user_id = int(context.args[1])
        pair_info = await get_user_pair_info(target_user_id)
        
        if pair_info:
            message = f"Pair info for user {target_user_id}:\n\n"
            message += f"Pair ID: {pair_info['pair_id']}\n"
            message += f"User A: {pair_info['user_a']}\n"
            message += f"User B: {pair_info['user_b']}\n"
            message += f"Started: {pair_info['started_at']}\n"
            message += f"Last message: {pair_info['last_message_at']}\n"
            message += f"Active: {pair_info['is_active']}"
        else:
            message = f"User {target_user_id} is not in an active pair."
        
        await update.message.reply_text(message)
        await log_admin_action(user_id, "view_pair", {"target_user_id": target_user_id})
    except ValueError:
        await update.message.reply_text("Invalid user ID.")


async def handle_admin_force_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin force_pair <user_a> <user_b>"""
    user_id = update.effective_user.id
    
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /admin force_pair <user_a> <user_b>")
        return
    
    try:
        user_a = int(context.args[1])
        user_b = int(context.args[2])
        
        pair_id = await force_pair_users(user_a, user_b)
        if pair_id:
            await update.message.reply_text(f"✅ Created pair {pair_id} between users {user_a} and {user_b}")
            await log_admin_action(user_id, "force_pair", {"user_a": user_a, "user_b": user_b, "pair_id": pair_id})
        else:
            await update.message.reply_text("❌ Failed to create pair.")
    except ValueError:
        await update.message.reply_text("Invalid user IDs.")


async def handle_admin_disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin disconnect <user_id>"""
    user_id = update.effective_user.id
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /admin disconnect <user_id>")
        return
    
    try:
        target_user_id = int(context.args[1])
        pair_id = await get_user_pair(target_user_id)
        
        if pair_id:
            await end_pair(pair_id, target_user_id)
            await update.message.reply_text(f"✅ Disconnected user {target_user_id} from chat.")
            await log_admin_action(user_id, "disconnect", {"target_user_id": target_user_id, "pair_id": pair_id})
        else:
            await update.message.reply_text(f"User {target_user_id} is not in an active chat.")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")


async def handle_admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin ban <user_id>"""
    user_id = update.effective_user.id
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /admin ban <user_id>")
        return
    
    try:
        target_user_id = int(context.args[1])
        success = await ban_user(target_user_id, user_id)
        
        if success:
            await update.message.reply_text(f"✅ User {target_user_id} has been banned.")
        else:
            await update.message.reply_text(f"❌ Failed to ban user {target_user_id}.")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")


async def handle_admin_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin unban <user_id>"""
    user_id = update.effective_user.id
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /admin unban <user_id>")
        return
    
    try:
        target_user_id = int(context.args[1])
        success = await unban_user(target_user_id, user_id)
        
        if success:
            await update.message.reply_text(f"✅ User {target_user_id} has been unbanned.")
        else:
            await update.message.reply_text(f"❌ Failed to unban user {target_user_id}.")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")


async def handle_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin stats"""
    user_id = update.effective_user.id
    
    from bot.database.connection import fetch_query, fetch_all
    
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
    message += f"Total users: {total_users_count}\n"
    message += f"Active pairs: {active_pairs_count}\n"
    message += f"Banned users: {banned_users_count}\n"
    message += f"Pending reports: {pending_reports_count}\n"
    
    await update.message.reply_text(message)
    await log_admin_action(user_id, "stats", {})

