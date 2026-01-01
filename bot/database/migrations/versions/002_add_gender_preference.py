"""Add gender_preference column to users table

Revision ID: 002_add_gender_preference
Revises: 001_initial_schema
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_gender_preference'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add gender_preference column to users table
    op.execute("""
        ALTER TABLE users ADD COLUMN IF NOT EXISTS gender_preference SMALLINT DEFAULT 0
    """)


def downgrade() -> None:
    # Remove gender_preference column
    op.execute("""
        ALTER TABLE users DROP COLUMN IF EXISTS gender_preference
    """)

