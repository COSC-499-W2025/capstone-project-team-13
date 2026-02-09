import hashlib
import os
import sys
import re
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Databases.database import db_manager


# ============================================
# HELPER FUNCTIONS
# ============================================

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with a salt"""
    salt = "dam_salt_2025"  # In production, use a unique salt per user (e.g. via os.urandom)
    return hashlib.sha256((salt + password).encode()).hexdigest()


def validate_email(email: str) -> bool:
    """Basic email format validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def parse_date(date_string: str) -> datetime:
    """
    Parse a date string in MM/YYYY format and return a datetime object.
    Returns None if the string is empty or invalid.
    """
    if not date_string.strip():
        return None
    try:
        return datetime.strptime(date_string.strip(), "%m/%Y").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def get_logged_in_user():
    """
    Prompt user for email and password, verify against the database.
    Returns the User object if successful, None otherwise.
    """
    print("\n" + "=" * 50)
    print("  LOGIN REQUIRED")
    print("=" * 50)
    email = input("\nEnter your email: ").strip()
    password = input("Enter your password: ").strip()

    if not email or not password:
        print("❌ Email and password cannot be empty.")
        return None

    user = db_manager.get_user_by_email(email)
    if not user:
        print("❌ No account found with that email.")
        return None

    if user.password_hash != hash_password(password):
        print("❌ Incorrect password.")
        return None

    print(f"✓ Logged in as {user.first_name} {user.last_name}")
    return user


# ============================================
# SIGN UP
# ============================================

def sign_up():
    """Collect user details and create a new account"""
    print("\n" + "=" * 50)
    print("  SIGN UP")
    print("=" * 50)

    # Collect basic info
    first_name = input("\nFirst name: ").strip()
    if not first_name:
        print("❌ First name cannot be empty.")
        input("Press Enter to continue...")
        return

    last_name = input("Last name: ").strip()
    if not last_name:
        print("❌ Last name cannot be empty.")
        input("Press Enter to continue...")
        return

    email = input("Email: ").strip()
    if not email:
        print("❌ Email cannot be empty.")
        input("Press Enter to continue...")
        return
    if not validate_email(email):
        print("❌ Invalid email format. Please use format: name@domain.com")
        input("Press Enter to continue...")
        return

    # Check if email already exists
    existing_user = db_manager.get_user_by_email(email)
    if existing_user:
        print("❌ An account with this email already exists.")
        input("Press Enter to continue...")
        return

    password = input("Password: ").strip()
    if not password:
        print("❌ Password cannot be empty.")
        input("Press Enter to continue...")
        return
    if len(password) < 6:
        print("❌ Password must be at least 6 characters.")
        input("Press Enter to continue...")
        return

    confirm_password = input("Confirm password: ").strip()
    if password != confirm_password:
        print("❌ Passwords do not match.")
        input("Press Enter to continue...")
        return

    # Confirm details before creating
    print("\n--- Please confirm your details ---")
    print(f"  Name:  {first_name} {last_name}")
    print(f"  Email: {email}")
    confirm = input("\nCreate account? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Account creation cancelled.")
        input("Press Enter to continue...")
        return

    # Create the user
    try:
        user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password_hash': hash_password(password),
        }
        user = db_manager.create_user(user_data)
        print(f"\n✓ Account created successfully! Welcome, {user.first_name}.")
    except Exception as e:
        print(f"❌ Failed to create account: {e}")

    input("Press Enter to continue...")


# ============================================
# LOGIN
# ============================================

def login():
    """Authenticate user and display profile summary"""
    user = get_logged_in_user()
    if not user:
        input("Press Enter to continue...")
        return

    print("\n" + "=" * 50)
    print("  YOUR PROFILE")
    print("=" * 50)
    print(f"  Name:  {user.first_name} {user.last_name}")
    print(f"  Email: {user.email}")

    # Show education count
    education = db_manager.get_education_for_user(user.id)
    print(f"  Education entries:   {len(education)}")

    # Show work history count
    work_history = db_manager.get_work_history_for_user(user.id)
    print(f"  Work history entries: {len(work_history)}")

    # Show portfolio/resume status
    print(f"  Portfolio: {'✓ Set' if user.portfolio else '✗ Not set'}")
    print(f"  Resume:    {'✓ Set' if user.resume else '✗ Not set'}")

    input("\nPress Enter to continue...")


# ============================================
# ADD EDUCATION
# ============================================

def add_education():
    """Collect education details and store for the logged-in user"""
    user = get_logged_in_user()
    if not user:
        input("Press Enter to continue...")
        return

    print("\n" + "=" * 50)
    print("  ADD EDUCATION")
    print("=" * 50)

    institution = input("\nInstitution name: ").strip()
    if not institution:
        print("❌ Institution cannot be empty.")
        input("Press Enter to continue...")
        return

    print("\nDegree type examples: Bachelor's, Master's, PhD, Diploma, Certificate")
    degree_type = input("Degree type: ").strip()
    if not degree_type:
        print("❌ Degree type cannot be empty.")
        input("Press Enter to continue...")
        return

    topic = input("Topic/Major (e.g. Computer Science, Economics): ").strip()
    if not topic:
        print("❌ Topic cannot be empty.")
        input("Press Enter to continue...")
        return

    # Start date (required)
    print("\nEnter start date in MM/YYYY format (e.g. 09/2020):")
    start_input = input("Start date: ").strip()
    start_date = parse_date(start_input)
    if not start_date:
        print("❌ Invalid start date. Please use MM/YYYY format.")
        input("Press Enter to continue...")
        return

    # End date (optional — leave blank for "Present")
    print("End date (MM/YYYY), or press Enter for 'Present':")
    end_input = input("End date: ").strip()
    end_date = None
    if end_input:
        end_date = parse_date(end_input)
        if not end_date:
            print("❌ Invalid end date. Please use MM/YYYY format.")
            input("Press Enter to continue...")
            return

    # Confirm before saving
    print("\n--- Please confirm ---")
    print(f"  Institution: {institution}")
    print(f"  Degree:      {degree_type} in {topic}")
    print(f"  Dates:       {start_date.strftime('%m/%Y')} - {end_date.strftime('%m/%Y') if end_date else 'Present'}")
    confirm = input("\nSave? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        input("Press Enter to continue...")
        return

    try:
        education_data = {
            'user_id': user.id,
            'institution': institution,
            'degree_type': degree_type,
            'topic': topic,
            'start_date': start_date,
            'end_date': end_date,
        }
        db_manager.add_education(education_data)
        print(f"\n✓ Education entry added successfully.")
    except Exception as e:
        print(f"❌ Failed to save education: {e}")

    input("Press Enter to continue...")


# ============================================
# ADD WORK HISTORY
# ============================================

def add_work_history():
    """Collect work history details and store for the logged-in user"""
    user = get_logged_in_user()
    if not user:
        input("Press Enter to continue...")
        return

    print("\n" + "=" * 50)
    print("  ADD WORK HISTORY")
    print("=" * 50)

    company = input("\nCompany name: ").strip()
    if not company:
        print("❌ Company cannot be empty.")
        input("Press Enter to continue...")
        return

    role = input("Role/Title: ").strip()
    if not role:
        print("❌ Role cannot be empty.")
        input("Press Enter to continue...")
        return

    # Start date (required)
    print("\nEnter start date in MM/YYYY format (e.g. 06/2022):")
    start_input = input("Start date: ").strip()
    start_date = parse_date(start_input)
    if not start_date:
        print("❌ Invalid start date. Please use MM/YYYY format.")
        input("Press Enter to continue...")
        return

    # End date (optional — leave blank for "Present")
    print("End date (MM/YYYY), or press Enter for 'Present':")
    end_input = input("End date: ").strip()
    end_date = None
    if end_input:
        end_date = parse_date(end_input)
        if not end_date:
            print("❌ Invalid end date. Please use MM/YYYY format.")
            input("Press Enter to continue...")
            return

    # Confirm before saving
    print("\n--- Please confirm ---")
    print(f"  Company: {company}")
    print(f"  Role:    {role}")
    print(f"  Dates:   {start_date.strftime('%m/%Y')} - {end_date.strftime('%m/%Y') if end_date else 'Present'}")
    confirm = input("\nSave? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        input("Press Enter to continue...")
        return

    try:
        work_data = {
            'user_id': user.id,
            'company': company,
            'role': role,
            'start_date': start_date,
            'end_date': end_date,
        }
        db_manager.add_work_history(work_data)
        print(f"\n✓ Work history entry added successfully.")
    except Exception as e:
        print(f"❌ Failed to save work history: {e}")

    input("Press Enter to continue...")


# ============================================
# MAIN MENU
# ============================================

def run_profile_menu():
    """Main profile menu loop"""
    while True:
        print("\n" + "=" * 50)
        print("  USER PROFILE")
        print("=" * 50)
        print("  1. Sign Up")
        print("  2. Log In")
        print("  3. Add Education")
        print("  4. Add Work History")
        print("  5. Back to Main Menu")
        print("=" * 50)

        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == '1':
            sign_up()
        elif choice == '2':
            login()
        elif choice == '3':
            add_education()
        elif choice == '4':
            add_work_history()
        elif choice == '5':
            print("\nReturning to main menu...")
            break
        else:
            print("❌ Invalid choice. Please enter a number 1-5.")
            input("Press Enter to continue...")

if __name__ == '__main__':
    print("Starting profile menu...")
    run_profile_menu()