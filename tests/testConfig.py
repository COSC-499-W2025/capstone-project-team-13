"""
Test file for consent system
Tests that consent is properly stored and retrieved from database
"""

import os
import sys
import shutil
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Databases.database import db_manager
from src.Databases.user_config import ConfigManager
from src.UserPrompts.config_integration import (
    has_basic_consent,
    has_ai_consent,
    get_ai_config,
    config_manager
)


def print_test(test_name):
    """Print test section header"""
    print("\n" + "=" * 70)
    print(f"TEST: {test_name}")
    print("=" * 70)


def test_database_setup():
    """Test 1: Verify database and tables are created"""
    print_test("Database Setup")
    
    # Check if database file exists
    db_path = "data/projects.db"
    if os.path.exists(db_path):
        print(f"✅ Database file exists: {db_path}")
    else:
        print(f"❌ Database file NOT found: {db_path}")
        return False
    
    # Check if tables exist
    from sqlalchemy import inspect
    inspector = inspect(db_manager.engine)
    tables = inspector.get_table_names()
    
    expected_tables = ['user_configs', 'projects', 'files', 'contributors', 'keywords']
    
    print(f"\nExpected tables: {expected_tables}")
    print(f"Found tables: {tables}")
    
    all_found = all(table in tables for table in expected_tables)
    
    if all_found:
        print("✅ All required tables exist")
    else:
        missing = [t for t in expected_tables if t not in tables]
        print(f"❌ Missing tables: {missing}")
    
    return all_found


def test_config_creation():
    """Test 2: Verify config can be created and retrieved"""
    print_test("Config Creation and Retrieval")
    
    try:
        config = config_manager.get_or_create_config()
        
        print(f"✅ Config created successfully")
        print(f"   Config ID: {config.id}")
        print(f"   Config Version: {config.config_version}")
        print(f"   Created at: {config.created_at}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create config: {e}")
        return False


def test_basic_consent_storage():
    """Test 3: Test basic file access consent storage"""
    print_test("Basic Consent Storage")
    
    try:
        # Grant consent
        print("Granting basic consent...")
        config_manager.grant_basic_consent()
        
        # Retrieve and verify
        config = config_manager.get_or_create_config()
        
        print(f"Basic consent granted: {config.basic_consent_granted}")
        print(f"Consent timestamp: {config.basic_consent_timestamp}")
        
        if config.basic_consent_granted and config.basic_consent_timestamp:
            print("✅ Basic consent stored successfully")
            
            # Test helper function
            if has_basic_consent():
                print("✅ Helper function confirms consent")
            else:
                print("❌ Helper function failed")
                return False
            
            return True
        else:
            print("❌ Basic consent not stored correctly")
            return False
            
    except Exception as e:
        print(f"❌ Error testing basic consent: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_consent_storage():
    """Test 4: Test AI/LLM consent storage"""
    print_test("AI Consent Storage")
    
    try:
        # Grant AI consent
        print("Granting AI consent...")
        config_manager.grant_ai_consent()
        
        # Retrieve and verify
        config = config_manager.get_or_create_config()
        
        print(f"AI consent granted: {config.ai_consent_granted}")
        print(f"AI enabled: {config.ai_enabled}")
        print(f"AI provider: {config.ai_provider}")
        print(f"AI model: {config.ai_model}")
        print(f"Consent timestamp: {config.ai_consent_timestamp}")
        
        if config.ai_consent_granted and config.ai_enabled:
            print("✅ AI consent stored successfully")
            
            # Test helper functions
            if has_ai_consent():
                print("✅ Helper function confirms AI consent")
            else:
                print("❌ Helper function failed")
                return False
            
            ai_config = get_ai_config()
            print(f"✅ AI config retrieved: {ai_config}")
            
            return True
        else:
            print("❌ AI consent not stored correctly")
            return False
            
    except Exception as e:
        print(f"❌ Error testing AI consent: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_consent_revocation():
    """Test 5: Test consent revocation"""
    print_test("Consent Revocation")
    
    try:
        # Revoke basic consent
        print("Revoking basic consent...")
        config_manager.revoke_basic_consent()
        
        config = config_manager.get_or_create_config()
        
        if not config.basic_consent_granted:
            print("✅ Basic consent revoked successfully")
        else:
            print("❌ Basic consent still granted after revocation")
            return False
        
        # Revoke AI consent
        print("\nRevoking AI consent...")
        config_manager.revoke_ai_consent()
        
        config = config_manager.get_or_create_config()
        
        if not config.ai_consent_granted and not config.ai_enabled:
            print("✅ AI consent revoked successfully")
        else:
            print("❌ AI consent still granted after revocation")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing consent revocation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_persistence():
    """Test 6: Test that consent persists across sessions"""
    print_test("Consent Persistence")
    
    try:
        # Grant consent
        config_manager.grant_basic_consent()
        config_manager.grant_ai_consent()
        
        # Create a new config manager instance (simulates new session)
        print("Creating new config manager instance...")
        new_manager = ConfigManager(db_manager)
        
        config = new_manager.get_or_create_config()
        
        if config.basic_consent_granted and config.ai_consent_granted:
            print("✅ Consent persisted across sessions")
            return True
        else:
            print("❌ Consent not persisted")
            print(f"   Basic: {config.basic_consent_granted}")
            print(f"   AI: {config.ai_consent_granted}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing persistence: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_updates():
    """Test 7: Test config update functionality"""
    print_test("Config Updates")
    
    try:
        # Update various settings
        updates = {
            'anonymous_mode': True,
            'ai_provider': 'openai',
            'ai_model': 'gpt-4',
            'max_file_size_scan': 200_000_000
        }
        
        print(f"Updating config with: {updates}")
        config_manager.update_config(updates)
        
        config = config_manager.get_or_create_config()
        
        # Verify updates
        all_correct = True
        for key, expected_value in updates.items():
            actual_value = getattr(config, key)
            if actual_value == expected_value:
                print(f"✅ {key}: {actual_value}")
            else:
                print(f"❌ {key}: expected {expected_value}, got {actual_value}")
                all_correct = False
        
        return all_correct
        
    except Exception as e:
        print(f"❌ Error testing config updates: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_excluded_items():
    """Test 8: Test excluded folders and file types"""
    print_test("Excluded Items Management")
    
    try:
        # Add excluded folders
        folders = ['/test/folder1', '/test/folder2']
        for folder in folders:
            config_manager.add_excluded_folder(folder)
        
        # Add excluded file types
        extensions = ['.log', '.tmp', '.cache']
        for ext in extensions:
            config_manager.add_excluded_file_type(ext)
        
        config = config_manager.get_or_create_config()
        
        print(f"Excluded folders: {config.excluded_folders}")
        print(f"Excluded file types: {config.excluded_file_types}")
        
        folders_correct = all(f in config.excluded_folders for f in folders)
        extensions_correct = all(e in config.excluded_file_types for e in extensions)
        
        if folders_correct and extensions_correct:
            print("✅ Excluded items stored correctly")
            
            # Test removal
            config_manager.remove_excluded_folder(folders[0])
            config_manager.remove_excluded_file_type(extensions[0])
            
            config = config_manager.get_or_create_config()
            
            if folders[0] not in config.excluded_folders and extensions[0] not in config.excluded_file_types:
                print("✅ Excluded items removed correctly")
                return True
            else:
                print("❌ Failed to remove excluded items")
                return False
        else:
            print("❌ Excluded items not stored correctly")
            return False
            
    except Exception as e:
        print(f"❌ Error testing excluded items: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "=" * 70)
    print("CONSENT SYSTEM TEST SUITE")
    print("=" * 70)
    print(f"Started at: {datetime.now()}")
    
    tests = [
        ("Database Setup", test_database_setup),
        ("Config Creation", test_config_creation),
        ("Basic Consent Storage", test_basic_consent_storage),
        ("AI Consent Storage", test_ai_consent_storage),
        ("Consent Revocation", test_consent_revocation),
        ("Consent Persistence", test_persistence),
        ("Config Updates", test_config_updates),
        ("Excluded Items", test_excluded_items),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} CRASHED: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("The consent system is working correctly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("Please review the errors above")
    
    return passed == total


if __name__ == "__main__":
    # Optional: Clean slate for testing
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        print("🗑️  Cleaning database for fresh test...")
        if os.path.exists("data/projects.db"):
            os.remove("data/projects.db")
        print("✅ Database cleaned")
    
    success = run_all_tests()
    sys.exit(0 if success else 1)