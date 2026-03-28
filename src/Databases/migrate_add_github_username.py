"""
Migration: Add github_username column to users table
"""

from sqlalchemy import text
from src.Databases.database import db_manager

def migrate_add_github_username():
    with db_manager.engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        if 'github_username' not in columns:
            print("Adding github_username column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN github_username TEXT"))
        else:
            print("✓ github_username column already exists")

if __name__ == "__main__":
    migrate_add_github_username()
    print("Migration complete.")
