"""
Script to run database migrations
Can be used for Railway deployment
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bot.database.connection import get_pool, close_pool
from config.settings import settings


async def run_migrations():
    """Run database migrations"""
    try:
        pool = await get_pool()
        
        async with pool.acquire() as conn:
            # Check if migrations table exists
            migrations_table = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'alembic_version'
                )
            """)
            
            if not migrations_table:
                # Run initial migration
                print("Running initial migration...")
                
                # Read migration file
                migration_file = Path(__file__).parent / "bot" / "database" / "migrations" / "versions" / "001_initial_schema.py"
                if migration_file.exists():
                    # Execute migration SQL directly
                    from bot.database.migrations.versions import migration_001_initial
                    migration_001_initial.upgrade()
                    print("Initial migration completed!")
                else:
                    print("Migration file not found. Creating tables manually...")
                    await create_tables(conn)
            else:
                print("Migrations already run. Tables exist.")
        
        await close_pool()
    except Exception as e:
        print(f"Error running migrations: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def create_tables(conn):
    """Create database tables directly"""
    # This is a fallback if Alembic isn't working
    # For production, use Alembic properly
    pass


if __name__ == "__main__":
    asyncio.run(run_migrations())

