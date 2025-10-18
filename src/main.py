import os
import sys
from getConsent import get_user_consent
from fileFormatCheck import check_file_format, InvalidFileFormatError
from fileParser import parse_file, FileParseError

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

def display_parse_results(results):
    """
    Display parsed file results in a readable format
    
    Args:
        results (dict): Parsed file data
    """
    print("\n" + "="*50)
    print("PARSE RESULTS")
    print("="*50)
    
    file_type = results.get('type', 'unknown')
    print(f"\nFile Type: {file_type.upper()}")
    
    if file_type == 'text':
        print(f"Lines: {results['lines']}")
        print(f"Characters: {results['characters']}")
        print("\nContent Preview:")
        preview = results['content'][:200]
        print(preview + "..." if len(results['content']) > 200 else preview)
    
    elif file_type == 'json':
        print(f"Size: {results['size']} bytes")
        print("\nContent Preview:")
        print(str(results['content'])[:300] + "...")
    
    elif file_type == 'csv':
        print(f"Rows: {results['rows']}")
        print(f"Columns: {', '.join(results['columns'])}")
        if results['rows'] > 0:
            print("\nFirst Row Preview:")
            print(results['content'][0])
    
    elif file_type == 'python':
        print(f"Lines: {results['lines']}")
        print(f"Functions: {results['functions']}")
        print(f"Classes: {results['classes']}")

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
    
    # Parse file
    try:
        print("\nParsing file...")
        results = parse_file(file_path)
        display_parse_results(results)
        print("\n✓ File parsed successfully!")
    except FileParseError as e:
        print(f"\n✗ Parsing error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()