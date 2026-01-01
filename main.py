"""
Main FastAPI application for Telegram Anonymous Chat Bot
"""
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config.settings import settings
from bot.database.connection import get_pool, close_pool, execute_query
from bot.services.redis_client import get_redis, close_redis
from bot.handlers.commands import (
    handle_next, handle_stop, handle_report, handle_block,
    handle_invite, handle_language, handle_policy
)
from bot.handlers.onboarding import handle_start
from bot.handlers.chat import handle_message
from bot.handlers.admin import handle_admin
from config.constants import MESSAGE_RETENTION_DAYS

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global Telegram application
telegram_app: Application = None


async def cleanup_old_messages():
    """Background task to clean up old messages"""
    try:
        await execute_query(
            f"""
            DELETE FROM messages
            WHERE created_at < NOW() - INTERVAL '{MESSAGE_RETENTION_DAYS} days'
            """
        )
        logger.info("Cleaned up old messages")
    except Exception as e:
        logger.error(f"Error cleaning up messages: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global telegram_app
    
    # Startup
    logger.info("Starting application...")
    
    # Initialize database pool
    try:
        await get_pool()
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Initialize Redis
    try:
        await get_redis()
        logger.info("Redis connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise
    
    # Initialize database tables if they don't exist
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Check if users table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                )
            """)
            if not table_exists:
                logger.warning("Database tables not found. Please run 'python init_db.py' to initialize the database.")
            else:
                logger.info("Database ready")
    except Exception as e:
        logger.warning(f"Database check failed: {e}")
    
    # Initialize Telegram bot
    try:
        telegram_app = Application.builder().token(settings.bot_token).build()
        
        # Register handlers
        telegram_app.add_handler(CommandHandler("start", handle_start))
        telegram_app.add_handler(CommandHandler("next", handle_next))
        telegram_app.add_handler(CommandHandler("stop", handle_stop))
        telegram_app.add_handler(CommandHandler("report", handle_report))
        telegram_app.add_handler(CommandHandler("block", handle_block))
        telegram_app.add_handler(CommandHandler("invite", handle_invite))
        telegram_app.add_handler(CommandHandler("referrals", handle_invite))  # Alias
        telegram_app.add_handler(CommandHandler("language", handle_language))
        telegram_app.add_handler(CommandHandler("policy", handle_policy))
        telegram_app.add_handler(CommandHandler("admin", handle_admin))
        telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Initialize bot
        await telegram_app.initialize()
        logger.info("Telegram bot initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Telegram bot: {e}")
        raise
    
    # Start background task for cleanup
    async def periodic_cleanup():
        while True:
            await asyncio.sleep(86400)  # Run once per day
            await cleanup_old_messages()
    
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    cleanup_task.cancel()
    
    if telegram_app:
        await telegram_app.shutdown()
        await telegram_app.stop()
    
    await close_redis()
    await close_pool()
    logger.info("Application shut down")


# Create FastAPI app
app = FastAPI(
    title="Telegram Anonymous Chat Bot",
    description="Anonymous one-to-one chat service for Telegram",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "ok", "service": "telegram-anonymous-chat-bot"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Check Redis
        redis_client = await get_redis()
        await redis_client.ping()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "healthy", "database": "ok", "redis": "ok"}
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/webhook")
async def webhook(request: Request):
    """Telegram webhook endpoint"""
    global telegram_app
    
    if not telegram_app:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "Bot not initialized"}
        )
    
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

