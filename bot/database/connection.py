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
            raise ValueError("DATABASE_URL not set. Please configure your database connection.")
        
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

