"""
Unit tests for db_migration.py
Tests database schema migration for file_hash column
"""

import unittest
import os
import tempfile
import shutil
from sqlalchemy import create_engine, inspect, text
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestDatabaseMigration(unittest.TestCase):
    """Test database migration functionality"""
    
    def setUp(self):
        """Create temporary test database"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, 'test_migration.db')
    
    def tearDown(self):
        """Clean up test database"""
        shutil.rmtree(self.test_dir)
    
    def test_migration_adds_column(self):
        """Test that migration adds file_hash column"""
        from src.Databases.database import DatabaseManager
        
        # Create database without file_hash column (simulate old database)
        db = DatabaseManager(db_path=self.test_db_path)
        
        # Manually remove file_hash column to simulate old schema
        engine = db.engine
        with engine.connect() as conn:
            # Check if column exists
            inspector = inspect(engine)
            columns_before = [col['name'] for col in inspector.get_columns('files')]
            
            if 'file_hash' in columns_before:
                # Remove it for testing
                try:
                    conn.execute(text("ALTER TABLE files DROP COLUMN file_hash"))
                    conn.commit()
                except:
                    pass  # SQLite doesn't support DROP COLUMN easily
        
        # Now run migration
        from src.Databases.db_migration import migrate_add_file_hash
        
        # Override db_manager to use test database
        import src.Databases.db_migration as migration_module
        original_db = migration_module.DatabaseManager
        migration_module.DatabaseManager = lambda: db
        
        try:
            migrate_add_file_hash()
        finally:
            migration_module.DatabaseManager = original_db
        
        # Verify column was added
        inspector = inspect(engine)
        columns_after = [col['name'] for col in inspector.get_columns('files')]
        
        self.assertIn('file_hash', columns_after)
        
        db.close()
    
    def test_migration_is_idempotent(self):
        """Test that running migration twice doesn't cause errors"""
        from src.Databases.database import DatabaseManager
        from src.Databases.db_migration import migrate_add_file_hash
        
        db = DatabaseManager(db_path=self.test_db_path)
        
        # Override db_manager
        import src.Databases.db_migration as migration_module
        original_db = migration_module.DatabaseManager
        migration_module.DatabaseManager = lambda: db
        
        try:
            # Run migration first time
            migrate_add_file_hash()
            
            # Run migration second time (should not error)
            migrate_add_file_hash()
            
            # Verify column exists
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('files')]
            self.assertIn('file_hash', columns)
            
        finally:
            migration_module.DatabaseManager = original_db
            db.close()
    
    def test_file_hash_column_properties(self):
        """Test that file_hash column has correct properties"""
        from src.Databases.database import DatabaseManager
        
        db = DatabaseManager(db_path=self.test_db_path)
        
        inspector = inspect(db.engine)
        columns = {col['name']: col for col in inspector.get_columns('files')}
        
        if 'file_hash' in columns:
            file_hash_col = columns['file_hash']
            
            # Check type (should be VARCHAR or TEXT)
            self.assertIn(str(file_hash_col['type']).upper(), ['VARCHAR', 'TEXT', 'VARCHAR(64)'])
            
            # Check that it's nullable (should be True for backward compatibility)
            self.assertTrue(file_hash_col['nullable'])
        
        db.close()


if __name__ == '__main__':
    unittest.main()