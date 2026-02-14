import os
import sys
from typing import Optional
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.Databases.database import User


class SessionManager:
    """
    Manages user session state for the application.
    Tracks which user is currently logged in.
    """
    
    def __init__(self):
        """Initialize with no logged-in user"""
        self.current_user_id: Optional[int] = None
        self.current_user: Optional[User] = None
    
    def login(self, user: User) -> None:
        """
        Log in a user by setting the current session.
        
        Args:
            user: The User object to log in
        """
        self.current_user_id = user.id
        self.current_user = user
        print(f"✓ Session started for {user.first_name} {user.last_name}")
    
    def logout(self) -> None:
        """Log out the current user by clearing the session"""
        if self.current_user:
            print(f"✓ Logged out {self.current_user.first_name} {self.current_user.last_name}")
        self.current_user_id = None
        self.current_user = None
    
    def is_logged_in(self) -> bool:
        """
        Check if a user is currently logged in.
        
        Returns:
            True if a user is logged in, False otherwise
        """
        return self.current_user_id is not None
    
    def get_current_user(self) -> Optional[User]:
        """
        Get the currently logged-in user.
        
        Returns:
            The current User object, or None if not logged in
        """
        return self.current_user
    
    def get_current_user_id(self) -> Optional[int]:
        """
        Get the ID of the currently logged-in user.
        
        Returns:
            The current user's ID, or None if not logged in
        """
        return self.current_user_id
    
    def require_login(self) -> bool:
        """
        Check if user is logged in and print error message if not.
        Useful for menu options that require authentication.
        
        Returns:
            True if logged in, False otherwise
        """
        if not self.is_logged_in():
            print("❌ You must be logged in to perform this action.")
            print("   Please log in or sign up first.")
            return False
        return True


# Global session manager instance (singleton pattern)
session = SessionManager()