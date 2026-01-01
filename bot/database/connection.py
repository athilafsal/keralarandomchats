"""
Database connection and pool management
"""
import asyncpg
from typing import Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the database connection pool"""
    global _pool
    if _pool is None:
        if not settings.database_url:
            error_msg = (
                "❌ DATABASE_URL environment variable is not set!\n\n"
                "To fix this in Railway:\n"
                "1. Go to Railway dashboard → Your project\n"
                "2. Click 'New' → 'Database' → 'Add PostgreSQL'\n"
                "3. Railway will automatically provide DATABASE_URL\n"
                "4. Make sure the PostgreSQL service is in the same project as your bot\n"
                "5. Redeploy your service\n\n"
                "The DATABASE_URL is automatically set when you add a PostgreSQL addon."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        _pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=5,
            max_size=10,
            command_timeout=60
        )
        logger.info("Database connection pool created")
    return _pool


async def close_pool():
    """Close the database connection pool"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")


async def execute_query(query: str, *args):
    """Execute a query and return results"""
    pool = await get_pool()
    return await pool.execute(query, *args)


async def fetch_query(query: str, *args):
    """Fetch a single row"""
    pool = await get_pool()
    row = await pool.fetchrow(query, *args)
    # Convert asyncpg.Record to dict-like access (asyncpg already supports this, but ensure compatibility)
    return row


async def fetch_all(query: str, *args):
    """Fetch all rows"""
    pool = await get_pool()
    return await pool.fetch(query, *args)

