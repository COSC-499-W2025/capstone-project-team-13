import os
import sys
from getConsent import get_user_consent
from fileFormatCheck import check_file_format, InvalidFileFormatError

def get_file_path():
    """
    Prompt user for file path and validate it exists
    
    Returns:
        str: Valid file path or None if user cancels
    """
    while True:
        print("\nEnter the file path (or 'quit' to exit):")
        file_path = input("> ").strip()
        
        if file_path.lower() == 'quit':
            return None
        
        if not file_path:
            print("Please enter a valid path.")
            continue
        
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist.")
            retry = input("Try again? (yes/no): ").strip().lower()
            if retry != 'yes':
                return None
            continue
        
        return file_path

def main():
    """Main entry point for file upload system"""
    print("=== File Upload and Parsing System ===\n")
    
    # Get user consent first
    consent = get_user_consent()
    if consent != 'allow':
        print("\nExiting program.")
        sys.exit(0)
    
    # Get file path from user
    file_path = get_file_path()
    if file_path is None:
        print("\nOperation cancelled.")
        sys.exit(0)
    
    # Validate file format
    try:
        check_file_format(file_path)
        print(f"\n✓ File format validated: {os.path.basename(file_path)}")
    except InvalidFileFormatError as e:
        print(f"\n✗ {e}")
        sys.exit(1)
    
    print(f"\nFile ready for processing: {file_path}")
    # TODO: Add parsing logic in next phase

if __name__ == "__main__":
    main()