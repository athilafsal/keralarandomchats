"""
Initialize database tables
Run this script to create all required tables
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bot.database.connection import get_pool, close_pool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database with all tables"""
    pool = await get_pool()
    
    try:
        async with pool.acquire() as conn:
            logger.info("Creating database tables...")
            
            # UUID type is built-in in PostgreSQL, no extension needed
            
            # Create users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    username TEXT,
                    display_name TEXT,
                    gender SMALLINT DEFAULT 0,
                    language_preference TEXT DEFAULT 'any',
                    age_range TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    last_active TIMESTAMPTZ DEFAULT NOW(),
                    is_banned BOOLEAN DEFAULT false,
                    is_admin BOOLEAN DEFAULT false,
                    admin_session_expiry TIMESTAMPTZ,
                    referral_by TEXT,
                    referrals_count INT DEFAULT 0,
                    unlocked_features JSONB DEFAULT '{}',
                    blocked_users JSONB DEFAULT '[]'
                )
            """)
            logger.info("Created users table")
            
            # Create pairs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pairs (
                    pair_id UUID PRIMARY KEY,
                    user_a BIGINT REFERENCES users(id),
                    user_b BIGINT REFERENCES users(id),
                    started_at TIMESTAMPTZ DEFAULT NOW(),
                    last_message_at TIMESTAMPTZ DEFAULT NOW(),
                    is_active BOOLEAN DEFAULT true,
                    language_used TEXT
                )
            """)
            logger.info("Created pairs table")
            
            # Create referrals table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id SERIAL PRIMARY KEY,
                    referrer_id BIGINT REFERENCES users(id),
                    referree_id BIGINT REFERENCES users(id),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(referrer_id, referree_id)
                )
            """)
            logger.info("Created referrals table")
            
            # Create admin_logs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_logs (
                    id SERIAL PRIMARY KEY,
                    admin_id BIGINT REFERENCES users(id),
                    action TEXT NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            logger.info("Created admin_logs table")
            
            # Create messages table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGSERIAL PRIMARY KEY,
                    pair_id UUID REFERENCES pairs(pair_id),
                    from_id BIGINT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            logger.info("Created messages table")
            
            # Create index on messages.created_at
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)
            """)
            logger.info("Created index on messages.created_at")
            
            # Create reports table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id SERIAL PRIMARY KEY,
                    pair_id UUID REFERENCES pairs(pair_id),
                    reported_by BIGINT REFERENCES users(id),
                    reported_user BIGINT REFERENCES users(id),
                    reason TEXT,
                    conversation_excerpt JSONB DEFAULT '[]',
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            logger.info("Created reports table")
            
            logger.info("✅ Database initialization complete!")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(init_database())

