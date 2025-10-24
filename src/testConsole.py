import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import functions from getConsent.py
try:
    from src.UserPrompts.getConsent import get_user_consent, show_consent_status  # Example functions
    from src.Helpers.fileFormatCheck import check_file_format, InvalidFileFormatError
    from src.Extraction.zipHandler import validate_zip_file, extract_zip, get_zip_contents, count_files_in_zip, ZipExtractionError
    from src.Extraction.keywordExtractorText import extract_keywords_with_scores
    from src.Extraction.keywordExtractorCode import extract_code_keywords_with_scores, read_code_file, CODE_STOPWORDS
except ImportError:
    print("Could not import functions from either getConsent, zipHandler, fileFormatCheck, or keywordExtractor. Please check the file and function names.")
    sys.exit(1)

# Simple clear command, specifies by OS
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

# Console-based dashboard to test initial functions
def dashboard():
    while True:
        clear_console()
        print("=== Console Testing Dashboard ===")
        print("1. Get User Consent")
        print("2. Show Consent Status")
        print("3. Test Keyword Extraction")
        print("4. Exit")
        choice = input("Select an option (1-4): ").strip()

        # Basic input selection. Runs corresponding functions when called
        if choice == '1':
            result = get_user_consent()
            print(f"Consent result: {result}")
            input("Press Enter to continue...")
        elif choice == '2':
            status = show_consent_status()
            print(f"Consent status: {status}")
            input("Press Enter to continue...")
        elif choice == '3':
            run_keyword_extraction_test()  # <-- new function call
            input("Press Enter to continue...")
        elif choice == '4':
            print("Exiting dashboard.")
            break
        else:
            print("Invalid choice. Try again.")
            input("Press Enter to continue...")

def test_file_format():
    """Test file format validation with sample files"""
    clear_console()
    print("=== File Format Validation Test ===\n")
    
    # Test cases - mix of valid and invalid formats
    test_files = [
        "project_data.zip",
        "document.txt",
        "archive.tar.gz",
        "MY_PROJECT.ZIP",
        "data.json"
    ]
    
    print("Testing file format validation:\n")
    for file_path in test_files:
        try:
            if check_file_format(file_path):
                print(f"✓ {file_path} - Valid format")
        except InvalidFileFormatError as e:
            print(f"✗ {file_path} - {e}")
    
    print("\nTest completed.")

def test_zip_handling():
    """Test ZIP file operations"""
    clear_console()
    print("=== ZIP File Handling Test ===\n")
    
    # get zip path from user
    zip_path = input("Enter path to ZIP file (or press Enter to skip): ").strip()
    
    if not zip_path:
        print("Skipping test.")
        return
    
    if not os.path.exists(zip_path):
        print(f"File {zip_path} does not exist.")
        return
    
    try:
        # validate
        print("\n1. Validating ZIP file...")
        if validate_zip_file(zip_path):
            print("   ✓ ZIP file is valid")
        
        # count files
        print("\n2. Counting files in ZIP...")
        file_count = count_files_in_zip(zip_path)
        print(f"   Found {file_count} files")
        
        # list contents
        print("\n3. Listing ZIP contents...")
        contents = get_zip_contents(zip_path)
        print(f"   Total items: {len(contents)}")
        if len(contents) <= 10:
            for item in contents:
                print(f"   - {item}")
        else:
            print("   (showing first 10)")
            for item in contents[:10]:
                print(f"   - {item}")
        
        # ask if user wants to extract
        extract = input("\n4. Extract ZIP file? (yes/no): ").strip().lower()
        if extract == 'yes':
            print("   Extracting...")
            extract_path = extract_zip(zip_path)
            print(f"   ✓ Extracted to: {extract_path}")
        
        print("\nAll tests passed!")
        
    except InvalidFileFormatError as e:
        print(f"Format error: {e}")
    except ZipExtractionError as e:
        print(f"ZIP error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def run_keyword_extraction_test():
    """Test keyword extraction with user-provided text or a file"""
    clear_console()
    print("=== Keyword Extraction Test ===\n")

    print("1. Enter text manually")
    print("2. Load text from a file")
    print("3. Load code from a file")
    mode = input("Choose input method (1, 2, or 3): ").strip()

    text = ""

    if mode == '1':
        print("\nEnter/paste your text below. Press Enter twice to finish:\n")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        text = "\n".join(lines)

    elif mode == '2':
        file_path = input("Enter path to text file: ").strip()
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    elif mode == '3':
        file_path = input("Enter path to code file: ").strip()
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
        with open(file_path, "r", encoding="utf-8") as f:
            code_text = f.read()

        # If a helper is available, prefer it (safe fallback to raw code_text)
        try:
            code_text = read_code_file(file_path)
        except Exception:
            pass

        print("\nExtracting code keywords...\n")
        code_results = extract_code_keywords_with_scores(code_text)

        if not code_results:
            print("No keywords found in code.")
            return

        print("Extracted Code Keywords (with scores):\n")
        for score, phrase in code_results:
            print(f"{score:.2f}  -  {phrase}")
        return

    else:
        print("Invalid choice.")
        return

    if not text.strip():
        print("No text provided.")
        return

    print("\nExtracting keywords...\n")
    results = extract_keywords_with_scores(text)

    if not results:
        print("No keywords found.")
        return

    print("Extracted Keywords (with scores):\n")
    for score, phrase in results:
        print(f"{score:.2f}  -  {phrase}")

if __name__ == "__main__":
    dashboard()