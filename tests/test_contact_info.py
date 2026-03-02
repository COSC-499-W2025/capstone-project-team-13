import os
import sys
import pytest
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Users.profileMenu import validate_phone, validate_email, hash_password
from src.Databases.database import DatabaseManager, User, ContactInfo


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
# PHONE VALIDATION TESTS
# ============================================

class TestPhoneValidation:
    """Test phone number validation"""

    def test_valid_phone_10_digits(self):
        """Test valid 10-digit phone"""
        assert validate_phone("1234567890") == True

    def test_valid_phone_with_hyphens(self):
        """Test valid phone with hyphens"""
        assert validate_phone("123-456-7890") == True

    def test_valid_phone_with_parentheses(self):
        """Test valid phone with parentheses"""
        assert validate_phone("(123) 456-7890") == True

    def test_valid_phone_with_plus(self):
        """Test valid international phone with plus"""
        assert validate_phone("+1-234-567-8901") == True

    def test_valid_phone_11_digits(self):
        """Test valid 11-digit phone"""
        assert validate_phone("12345678901") == True

    def test_invalid_phone_too_short(self):
        """Test invalid phone with less than 10 digits"""
        assert validate_phone("12345") == False

    def test_invalid_phone_with_letters(self):
        """Test invalid phone with letters"""
        assert validate_phone("123456789a") == False

    def test_invalid_phone_empty(self):
        """Test invalid empty phone"""
        assert validate_phone("") == False

    def test_valid_phone_with_spaces(self):
        """Test valid phone with spaces"""
        assert validate_phone("123 456 7890") == True

    def test_valid_phone_with_dots(self):
        """Test valid phone with dots"""
        assert validate_phone("123.456.7890") == True


# ============================================
# EMAIL VALIDATION TESTS
# ============================================

class TestEmailValidation:
    """Test email validation"""

    def test_valid_email(self):
        """Test valid email"""
        assert validate_email("user@example.com") == True

    def test_valid_email_with_numbers(self):
        """Test valid email with numbers"""
        assert validate_email("user123@example.com") == True

    def test_valid_email_with_underscores(self):
        """Test valid email with underscores"""
        assert validate_email("user_name@example.com") == True

    def test_valid_email_with_dots(self):
        """Test valid email with dots"""
        assert validate_email("first.last@example.com") == True

    def test_invalid_email_no_at(self):
        """Test invalid email without @"""
        assert validate_email("userexample.com") == False

    def test_invalid_email_no_domain(self):
        """Test invalid email without domain"""
        assert validate_email("user@.com") == False

    def test_invalid_email_no_extension(self):
        """Test invalid email without extension"""
        assert validate_email("user@example") == False

    def test_invalid_email_empty(self):
        """Test invalid empty email"""
        assert validate_email("") == False

    def test_invalid_email_spaces(self):
        """Test invalid email with spaces"""
        assert validate_email("user name@example.com") == False


# ============================================
# DATABASE CONTACT INFO TESTS
# ============================================

class TestAddContactInfo:
    """Test adding contact info to database"""

    def test_add_contact_info(self, test_db, test_user):
        """Test adding contact info"""
        contact_data = {
            'user_id': test_user.id,
            'address': '123 Main St, City, State 12345',
            'phone': '1234567890',
        }
        contact = test_db.add_contact_info(contact_data)

        assert contact.id is not None
        assert contact.user_id == test_user.id
        assert contact.address == '123 Main St, City, State 12345'
        assert contact.phone == '1234567890'

    def test_add_contact_info_with_formatting(self, test_db, test_user):
        """Test adding contact info with formatted phone"""
        contact_data = {
            'user_id': test_user.id,
            'address': '456 Oak Ave, Town, State 54321',
            'phone': '(123) 456-7890',
        }
        contact = test_db.add_contact_info(contact_data)

        assert contact.phone == '(123) 456-7890'
        assert contact.address == '456 Oak Ave, Town, State 54321'

    def test_add_contact_info_timestamps(self, test_db, test_user):
        """Test that timestamps are set correctly"""
        contact_data = {
            'user_id': test_user.id,
            'address': '789 Pine Ln, Village, State 99999',
            'phone': '9876543210',
        }
        contact = test_db.add_contact_info(contact_data)

        assert contact.created_at is not None
        assert contact.updated_at is not None
        # SQLite doesn't preserve timezone info, just verify it's a datetime
        assert isinstance(contact.created_at, datetime)
        assert isinstance(contact.updated_at, datetime)


# ============================================
# GET CONTACT INFO TESTS
# ============================================

class TestGetContactInfo:
    """Test retrieving contact info from database"""

    def test_get_contact_info_for_user(self, test_db, test_user):
        """Test getting contact info for a user"""
        contact_data = {
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        }
        test_db.add_contact_info(contact_data)

        contacts = test_db.get_contact_info_for_user(test_user.id)

        assert len(contacts) == 1
        assert contacts[0].address == '123 Main St'
        assert contacts[0].phone == '1234567890'

    def test_get_contact_info_empty_user(self, test_db, test_user):
        """Test getting contact info for user with no contact info"""
        contacts = test_db.get_contact_info_for_user(test_user.id)

        assert len(contacts) == 0

    def test_get_contact_info_multiple(self, test_db, test_user):
        """Test getting multiple contact info entries for a user"""
        contact1 = {
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1111111111',
        }
        contact2 = {
            'user_id': test_user.id,
            'address': '456 Oak Ave',
            'phone': '2222222222',
        }
        test_db.add_contact_info(contact1)
        test_db.add_contact_info(contact2)

        contacts = test_db.get_contact_info_for_user(test_user.id)

        assert len(contacts) == 2


# ============================================
# UPDATE CONTACT INFO TESTS
# ============================================

class TestUpdateContactInfo:
    """Test updating contact info"""

    def test_update_contact_phone(self, test_db, test_user):
        """Test updating phone number"""
        contact_data = {
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1111111111',
        }
        contact = test_db.add_contact_info(contact_data)

        updated = test_db.update_contact_info(contact.id, {'phone': '9999999999'})

        assert updated.phone == '9999999999'
        assert updated.address == '123 Main St'

    def test_update_contact_address(self, test_db, test_user):
        """Test updating address"""
        contact_data = {
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        }
        contact = test_db.add_contact_info(contact_data)

        updated = test_db.update_contact_info(contact.id, {'address': '456 New Ave'})

        assert updated.address == '456 New Ave'
        assert updated.phone == '1234567890'

    def test_update_contact_both(self, test_db, test_user):
        """Test updating both phone and address"""
        contact_data = {
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1111111111',
        }
        contact = test_db.add_contact_info(contact_data)

        updated = test_db.update_contact_info(
            contact.id,
            {'phone': '9999999999', 'address': '789 Pine Ln'}
        )

        assert updated.phone == '9999999999'
        assert updated.address == '789 Pine Ln'

    def test_update_contact_updated_at(self, test_db, test_user):
        """Test that updated_at timestamp is updated"""
        contact_data = {
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        }
        contact = test_db.add_contact_info(contact_data)
        original_updated_at = contact.updated_at

        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)

        updated = test_db.update_contact_info(contact.id, {'phone': '9999999999'})

        assert updated.updated_at > original_updated_at

    def test_update_nonexistent_contact(self, test_db):
        """Test updating a contact that doesn't exist"""
        result = test_db.update_contact_info(99999, {'phone': '1111111111'})

        assert result is None


# ============================================
# DELETE CONTACT INFO TESTS
# ============================================

class TestDeleteContactInfo:
    """Test deleting contact info"""

    def test_delete_contact_info(self, test_db, test_user):
        """Test deleting contact info"""
        contact_data = {
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        }
        contact = test_db.add_contact_info(contact_data)

        success = test_db.delete_contact_info(contact.id)

        assert success == True
        contacts = test_db.get_contact_info_for_user(test_user.id)
        assert len(contacts) == 0

    def test_delete_nonexistent_contact(self, test_db):
        """Test deleting a contact that doesn't exist"""
        success = test_db.delete_contact_info(99999)

        assert success == False

    def test_delete_contact_cascade(self, test_db):
        """Test that contact is deleted when user is deleted"""
        user_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@example.com',
            'password_hash': hash_password('password123'),
        }
        user = test_db.create_user(user_data)

        contact_data = {
            'user_id': user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        }
        test_db.add_contact_info(contact_data)

        # Delete user
        test_db.delete_user(user.id)

        # Check that contact is also deleted
        contacts = test_db.get_contact_info_for_user(user.id)
        assert len(contacts) == 0


# ============================================
# INTEGRATION TESTS
# ============================================

class TestContactInfoIntegration:
    """Integration tests for contact info workflow"""

    def test_complete_contact_workflow(self, test_db, test_user):
        """Test complete workflow: create, read, update, delete"""
        # Create
        contact_data = {
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        }
        contact = test_db.add_contact_info(contact_data)
        assert contact.id is not None

        # Read
        contacts = test_db.get_contact_info_for_user(test_user.id)
        assert len(contacts) == 1
        assert contacts[0].phone == '1234567890'

        # Update
        updated = test_db.update_contact_info(contact.id, {'phone': '9999999999'})
        assert updated.phone == '9999999999'

        # Verify update
        contacts = test_db.get_contact_info_for_user(test_user.id)
        assert contacts[0].phone == '9999999999'

        # Delete
        success = test_db.delete_contact_info(contact.id)
        assert success == True

        # Verify deletion
        contacts = test_db.get_contact_info_for_user(test_user.id)
        assert len(contacts) == 0

    def test_contact_info_with_validation(self, test_db, test_user):
        """Test contact info with validated phone and email"""
        # Validate first
        assert validate_email(test_user.email)
        assert validate_phone("(555) 123-4567")

        # Then create
        contact_data = {
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '(555) 123-4567',
        }
        contact = test_db.add_contact_info(contact_data)

        assert contact.phone == '(555) 123-4567'


# ============================================
# TO_DICT TESTS
# ============================================

class TestContactInfoToDict:
    """Test ContactInfo.to_dict() method"""

    def test_to_dict(self, test_db, test_user):
        """Test converting contact info to dictionary"""
        contact_data = {
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        }
        contact = test_db.add_contact_info(contact_data)

        contact_dict = contact.to_dict()

        assert contact_dict['id'] is not None
        assert contact_dict['user_id'] == test_user.id
        assert contact_dict['address'] == '123 Main St'
        assert contact_dict['phone'] == '1234567890'
        assert 'created_at' in contact_dict
        assert 'updated_at' in contact_dict

    def test_to_dict_with_timestamps(self, test_db, test_user):
        """Test that to_dict includes ISO format timestamps"""
        contact_data = {
            'user_id': test_user.id,
            'address': '123 Main St',
            'phone': '1234567890',
        }
        contact = test_db.add_contact_info(contact_data)

        contact_dict = contact.to_dict()

        # Check that timestamps are ISO format strings
        assert isinstance(contact_dict['created_at'], str)
        assert isinstance(contact_dict['updated_at'], str)
        assert 'T' in contact_dict['created_at']  # ISO format includes 'T'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
