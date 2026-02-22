import sys
import os
import unittest
from datetime import datetime

# Setup path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')

# Add src directory to path if it exists
if os.path.exists(src_dir) and src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Try importing the modules
try:
    from Databases.sessionManager import SessionManager
    from Databases.database import User
except ImportError:
    try:
        from sessionManager import SessionManager
        from database import User
    except ImportError:
        print("ERROR: Could not import sessionManager or database modules.")
        sys.exit(1)


class TestSessionManager(unittest.TestCase):
    """Comprehensive tests for SessionManager functionality"""
    
    def setUp(self):
        """Create a fresh SessionManager instance for each test"""
        self.session = SessionManager()
        
        # Create mock user objects for testing
        self.user1 = User(
            id=1,
            first_name='Jane',
            last_name='Doe',
            email='jane@example.com',
            password_hash='hashed_password_123'
        )
        
        self.user2 = User(
            id=2,
            first_name='John',
            last_name='Smith',
            email='john@example.com',
            password_hash='hashed_password_456'
        )
    
    def tearDown(self):
        """Clean up after each test"""
        # Ensure session is cleared
        if self.session:
            self.session.logout()
    
    # ============ INITIALIZATION TESTS ============
    
    def test_initialization(self):
        """Test that SessionManager initializes with no logged-in user"""
        session = SessionManager()
        self.assertIsNone(session.current_user_id)
        self.assertIsNone(session.current_user)
        self.assertFalse(session.is_logged_in())
    
    # ============ LOGIN TESTS ============
    
    def test_login(self):
        """Test logging in a user"""
        self.session.login(self.user1)
        
        self.assertEqual(self.session.current_user_id, 1)
        self.assertEqual(self.session.current_user, self.user1)
        self.assertTrue(self.session.is_logged_in())
    
    def test_login_sets_correct_user_data(self):
        """Test that login sets all user attributes correctly"""
        self.session.login(self.user1)
        
        self.assertEqual(self.session.current_user.first_name, 'Jane')
        self.assertEqual(self.session.current_user.last_name, 'Doe')
        self.assertEqual(self.session.current_user.email, 'jane@example.com')
    
    def test_login_overwrites_previous_session(self):
        """Test that logging in a second user overwrites the first"""
        # Login user1
        self.session.login(self.user1)
        self.assertEqual(self.session.current_user_id, 1)
        
        # Login user2 (should replace user1)
        self.session.login(self.user2)
        self.assertEqual(self.session.current_user_id, 2)
        self.assertEqual(self.session.current_user.first_name, 'John')
    
    # ============ LOGOUT TESTS ============
    
    def test_logout(self):
        """Test logging out a user"""
        # First login
        self.session.login(self.user1)
        self.assertTrue(self.session.is_logged_in())
        
        # Then logout
        self.session.logout()
        self.assertIsNone(self.session.current_user_id)
        self.assertIsNone(self.session.current_user)
        self.assertFalse(self.session.is_logged_in())
    
    def test_logout_when_not_logged_in(self):
        """Test that logout works safely when no user is logged in"""
        # Should not raise any errors
        self.session.logout()
        self.assertIsNone(self.session.current_user_id)
        self.assertFalse(self.session.is_logged_in())
    
    def test_multiple_logouts(self):
        """Test that multiple logout calls work safely"""
        self.session.login(self.user1)
        self.session.logout()
        self.session.logout()  # Second logout should be safe
        self.session.logout()  # Third logout should be safe
        
        self.assertIsNone(self.session.current_user_id)
        self.assertFalse(self.session.is_logged_in())
    
    # ============ IS_LOGGED_IN TESTS ============
    
    def test_is_logged_in_false_initially(self):
        """Test that is_logged_in returns False for new session"""
        self.assertFalse(self.session.is_logged_in())
    
    def test_is_logged_in_true_after_login(self):
        """Test that is_logged_in returns True after login"""
        self.session.login(self.user1)
        self.assertTrue(self.session.is_logged_in())
    
    def test_is_logged_in_false_after_logout(self):
        """Test that is_logged_in returns False after logout"""
        self.session.login(self.user1)
        self.session.logout()
        self.assertFalse(self.session.is_logged_in())
    
    # ============ GET_CURRENT_USER TESTS ============
    
    def test_get_current_user_when_logged_in(self):
        """Test getting current user when logged in"""
        self.session.login(self.user1)
        user = self.session.get_current_user()
        
        self.assertIsNotNone(user)
        self.assertEqual(user.id, 1)
        self.assertEqual(user.email, 'jane@example.com')
    
    def test_get_current_user_when_not_logged_in(self):
        """Test getting current user when not logged in returns None"""
        user = self.session.get_current_user()
        self.assertIsNone(user)
    
    def test_get_current_user_after_logout(self):
        """Test getting current user after logout returns None"""
        self.session.login(self.user1)
        self.session.logout()
        user = self.session.get_current_user()
        self.assertIsNone(user)
    
    # ============ GET_CURRENT_USER_ID TESTS ============
    
    def test_get_current_user_id_when_logged_in(self):
        """Test getting current user ID when logged in"""
        self.session.login(self.user1)
        user_id = self.session.get_current_user_id()
        
        self.assertIsNotNone(user_id)
        self.assertEqual(user_id, 1)
    
    def test_get_current_user_id_when_not_logged_in(self):
        """Test getting current user ID when not logged in returns None"""
        user_id = self.session.get_current_user_id()
        self.assertIsNone(user_id)
    
    def test_get_current_user_id_after_logout(self):
        """Test getting current user ID after logout returns None"""
        self.session.login(self.user1)
        self.session.logout()
        user_id = self.session.get_current_user_id()
        self.assertIsNone(user_id)
    
    # ============ REQUIRE_LOGIN TESTS ============
    
    def test_require_login_when_logged_in(self):
        """Test require_login returns True when user is logged in"""
        self.session.login(self.user1)
        result = self.session.require_login()
        self.assertTrue(result)
    
    def test_require_login_when_not_logged_in(self):
        """Test require_login returns False when user is not logged in"""
        result = self.session.require_login()
        self.assertFalse(result)
    
    def test_require_login_after_logout(self):
        """Test require_login returns False after logout"""
        self.session.login(self.user1)
        self.session.logout()
        result = self.session.require_login()
        self.assertFalse(result)
    
    # ============ SESSION PERSISTENCE TESTS ============
    
    def test_session_persists_across_multiple_checks(self):
        """Test that session data persists across multiple method calls"""
        self.session.login(self.user1)
        
        # Multiple checks should all return the same data
        self.assertTrue(self.session.is_logged_in())
        self.assertEqual(self.session.get_current_user_id(), 1)
        self.assertEqual(self.session.get_current_user().email, 'jane@example.com')
        self.assertTrue(self.session.require_login())
        
        # All checks should still pass
        self.assertTrue(self.session.is_logged_in())
        self.assertEqual(self.session.current_user_id, 1)
    
    # ============ EDGE CASE TESTS ============
    
    def test_login_logout_login_cycle(self):
        """Test multiple login/logout cycles work correctly"""
        # First cycle
        self.session.login(self.user1)
        self.assertEqual(self.session.current_user_id, 1)
        self.session.logout()
        self.assertIsNone(self.session.current_user_id)
        
        # Second cycle with different user
        self.session.login(self.user2)
        self.assertEqual(self.session.current_user_id, 2)
        self.session.logout()
        self.assertIsNone(self.session.current_user_id)
        
        # Third cycle back to first user
        self.session.login(self.user1)
        self.assertEqual(self.session.current_user_id, 1)
    
    def test_user_object_reference_persistence(self):
        """Test that the User object reference is maintained correctly"""
        self.session.login(self.user1)
        
        # Get user reference multiple times
        user_ref1 = self.session.get_current_user()
        user_ref2 = self.session.get_current_user()
        user_ref3 = self.session.current_user
        
        # All references should point to the same object
        self.assertIs(user_ref1, user_ref2)
        self.assertIs(user_ref2, user_ref3)
        self.assertIs(user_ref1, self.user1)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)