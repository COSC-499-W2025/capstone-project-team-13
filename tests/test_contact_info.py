import os
import sys
import pytest
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Users.profileMenu import validate_phone, validate_email, hash_password
from src.Databases.database import DatabaseManager


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def test_db():
    """Create a temporary test database"""
    db = DatabaseManager('data/test_contact.db')
    yield db
    # Cleanup
    db.clear_all_data()
    db.close()
    if os.path.exists('data/test_contact.db'):
        os.remove('data/test_contact.db')


@pytest.fixture
def test_user(test_db):
    """Create a test user"""
    user_data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com',
        'password_hash': hash_password('password123'),
    }
    return test_db.create_user(user_data)


# ============================================
# VALIDATION TESTS
# ============================================

class TestValidation:
    """Test input validation"""

    def test_valid_phone_formats(self):
        """Test various valid phone formats"""
        assert validate_phone("1234567890")
        assert validate_phone("123-456-7890")
        assert validate_phone("(123) 456-7890")
        assert validate_phone("+1-234-567-8901")

    def test_invalid_phone(self):
        """Test invalid phone numbers"""
        assert not validate_phone("12345")  # Too short
        assert not validate_phone("123456789a")  # Has letters
        assert not validate_phone("")  # Empty

    def test_valid_email(self):
        """Test valid email formats"""
        assert validate_email("user@example.com")
        assert validate_email("user.name@example.co.uk")
        assert validate_email("user+tag@example.com")

    def test_invalid_email(self):
        """Test invalid emails"""
        assert not validate_email("userexample.com")  # No @
        assert not validate_email("user@example")  # No extension
        assert not validate_email("")  # Empty


# ============================================
# DATABASE CRUD TESTS
# ============================================

class TestContactInfoCRUD:
    """Test Contact Info CRUD operations"""

    def test_add_contact_info(self, test_db, test_user):
        """Test adding contact info"""
        contact = test_db.add_contact_info({
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        })

        assert contact.id is not None
        assert contact.address == '123 Main St'
        assert contact.phone == '1234567890'

    def test_get_contact_info(self, test_db, test_user):
        """Test retrieving contact info"""
        test_db.add_contact_info({
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        })

        contacts = test_db.get_contact_info_for_user(test_user.id)
        assert len(contacts) == 1
        assert contacts[0].phone == '1234567890'

    def test_update_contact_info(self, test_db, test_user):
        """Test updating contact info"""
        contact = test_db.add_contact_info({
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1111111111',
        })

        updated = test_db.update_contact_info(
            contact.id,
            {'phone': '9999999999', 'address': '456 Oak Ave'}
        )

        assert updated.phone == '9999999999'
        assert updated.address == '456 Oak Ave'

    def test_delete_contact_info(self, test_db, test_user):
        """Test deleting contact info"""
        contact = test_db.add_contact_info({
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        })

        success = test_db.delete_contact_info(contact.id)
        assert success

        contacts = test_db.get_contact_info_for_user(test_user.id)
        assert len(contacts) == 0

    def test_delete_nonexistent(self, test_db):
        """Test deleting non-existent contact"""
        assert not test_db.delete_contact_info(99999)


# ============================================
# INTEGRATION TESTS
# ============================================

class TestContactInfoIntegration:
    """Integration tests"""

    def test_full_workflow(self, test_db, test_user):
        """Test complete create-read-update-delete workflow"""
        # Create
        contact = test_db.add_contact_info({
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        })
        assert contact.id is not None

        # Read
        contacts = test_db.get_contact_info_for_user(test_user.id)
        assert len(contacts) == 1

        # Update
        test_db.update_contact_info(contact.id, {'phone': '9999999999'})
        contacts = test_db.get_contact_info_for_user(test_user.id)
        assert contacts[0].phone == '9999999999'

        # Delete
        test_db.delete_contact_info(contact.id)
        assert len(test_db.get_contact_info_for_user(test_user.id)) == 0

    def test_contact_timestamps(self, test_db, test_user):
        """Test contact has proper timestamps"""
        contact = test_db.add_contact_info({
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        })

        assert isinstance(contact.created_at, datetime)
        assert isinstance(contact.updated_at, datetime)

    def test_contact_to_dict(self, test_db, test_user):
        """Test contact can convert to dictionary"""
        contact = test_db.add_contact_info({
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        })

        contact_dict = contact.to_dict()
        assert contact_dict['address'] == '123 Main St'
        assert contact_dict['phone'] == '1234567890'
        assert 'created_at' in contact_dict


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
