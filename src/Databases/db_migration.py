from sqlalchemy import text
import os
import sys

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')
)
sys.path.insert(0, PROJECT_ROOT)

from src.Databases.database import DatabaseManager


def migrate_add_file_hash():
    """Add file_hash column to files table if it doesn't exist"""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Check if column exists
        result = session.execute(text("PRAGMA table_info(files)"))
        columns = [row[1] for row in result]
        
        if 'file_hash' not in columns:
            print("Adding file_hash column to files table...")
            session.execute(text("ALTER TABLE files ADD COLUMN file_hash VARCHAR(64)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS ix_files_file_hash ON files(file_hash)"))
            session.commit()
            print("✓ Migration complete")
        else:
            print("✓ file_hash column already exists")
    except Exception as e:
        print(f"Migration error: {e}")
        session.rollback()
    finally:
        session.close()


def migrate_add_user_contribution_percent():
    """Add user_contribution_percent column to projects table if it doesn't exist"""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Check if column exists
        result = session.execute(text("PRAGMA table_info(projects)"))
        columns = [row[1] for row in result]
        
        if 'user_contribution_percent' not in columns:
            print("Adding user_contribution_percent column to projects table...")
            session.execute(text("ALTER TABLE projects ADD COLUMN user_contribution_percent FLOAT DEFAULT 0.0"))
            session.commit()
            print("✓ Migration complete: user_contribution_percent column added")
        else:
            print("✓ user_contribution_percent column already exists")
    except Exception as e:
        print(f"Migration error: {e}")
        session.rollback()
    finally:
        session.close()


def run_all_migrations():
    """Run all migration functions"""
    print("\n=== Running Database Migrations ===\n")
    migrate_add_file_hash()
    migrate_add_user_contribution_percent()
    print("\n=== All migrations complete ===\n")


if __name__ == "__main__":
    run_all_migrations()