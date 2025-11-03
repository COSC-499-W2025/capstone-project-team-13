import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Analysis import codeIdentifier, visualMediaAnalyzer
from src.UserPrompts.getConsent import get_user_consent
from src.Helpers.fileFormatCheck import check_file_format, InvalidFileFormatError
from src.Helpers.fileParser import parse_file, FileParseError
from src.Extraction.zipHandler import validate_zip_file, extract_zip, get_zip_contents, count_files_in_zip, ZipExtractionError
from src.Helpers.fileDataCheck import sniff_supertype
from src.Helpers.classifier import supertype_from_extension


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

    # Check if it's a ZIP file
    if file_path.lower().endswith('.zip'):
        try:
            validate_zip_file(file_path)
            print("✓ Valid ZIP file detected")
            
            # Get and display contents
            contents = get_zip_contents(file_path)
            file_count = count_files_in_zip(file_path)
            
            print(f"\nZIP Summary:")
            print(f"  Total items: {len(contents)}")
            print(f"  Files: {file_count}")
            print(f"  Folders: {len(contents) - file_count}")
            
            print("\nContents:")
            for item in contents[:20]:  # Show first 20 items
                item_type = "📁" if item.endswith('/') else "📄"
                print(f"  {item_type} {item}")
            if len(contents) > 20:
                print(f"  ... and {len(contents) - 20} more items")
            
            print("\n✓ ZIP file parsed successfully!")
            
        except (InvalidFileFormatError, ZipExtractionError) as e:
            print(f"\n✗ ZIP error: {e}")
            sys.exit(1)
        
    # Sniff file type
    try:
        # --- Determine declared and inferred file type ---
        extension_type = supertype_from_extension(file_path)
        print(extension_type)
        sniffed_type = sniff_supertype(file_path)
        print(sniffed_type)

        # --- Detect mismatch ---
        if extension_type and sniffed_type and extension_type != sniffed_type:
            print(f"\n✗ Content mismatch: extension suggests '{extension_type}', "
                f"but content looks like '{sniffed_type}'. Please verify the file, and update the extension if necessary.")
            sys.exit(1)

        print(f"✓ Type check passed — {extension_type or 'unknown'} (content agrees)")
    except Exception as e:
        print(f"\n✗ Type detection error: {e}")
        sys.exit(1)

    # if sniffed_type == "code":
    #     analyzedData = codeIdentifier(file_path)

    # elif sniffed_type == "media":
    #     analyzedData = visualMediaAnalyzer(file_path)

    # elif sniffed_type == "text":
    #     analyzedData = parse_file(file_path)

    # else:
    #     print("Unknown type"); sys.exit(1)




if __name__ == "__main__":
    main()