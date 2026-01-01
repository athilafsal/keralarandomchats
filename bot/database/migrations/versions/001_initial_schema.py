"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.execute("""
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
    
    # Create pairs table
    op.execute("""
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
    
    # Create referrals table
    op.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id SERIAL PRIMARY KEY,
            referrer_id BIGINT REFERENCES users(id),
            referree_id BIGINT REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(referrer_id, referree_id)
        )
    """)
    
    # Create admin_logs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id SERIAL PRIMARY KEY,
            admin_id BIGINT REFERENCES users(id),
            action TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    # Create messages table
    op.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id BIGSERIAL PRIMARY KEY,
            pair_id UUID REFERENCES pairs(pair_id),
            from_id BIGINT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    # Create index on messages.created_at for cleanup
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)
    """)
    
    # Create reports table
    op.execute("""
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


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS reports")
    op.execute("DROP INDEX IF EXISTS idx_messages_created_at")
    op.execute("DROP TABLE IF EXISTS messages")
    op.execute("DROP TABLE IF EXISTS admin_logs")
    op.execute("DROP TABLE IF EXISTS referrals")
    op.execute("DROP TABLE IF EXISTS pairs")
    op.execute("DROP TABLE IF EXISTS users")

