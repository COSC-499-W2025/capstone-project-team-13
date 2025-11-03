import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import functions from getConsent.py
try:
    from src.Analysis.summarizeProjects import summarize_projects
    from src.UserPrompts.getConsent import get_user_consent, show_consent_status  # Example functions
    from src.Helpers.fileFormatCheck import check_file_format, InvalidFileFormatError
    from src.Extraction.zipHandler import validate_zip_file, extract_zip, get_zip_contents, count_files_in_zip, ZipExtractionError
    from src.Extraction.keywordExtractorText import extract_keywords_with_scores
    from src.Extraction.keywordExtractorCode import extract_code_keywords_with_scores, read_code_file, CODE_STOPWORDS
    from src.Analysis.keywordAnalytics import technical_density, keyword_clustering
    from src.Analysis.codingProjectScanner import scan_coding_project, CodingProjectScanner
    from src.Databases.database import db_manager
    from src.AI.ai_service import get_ai_service
    from src.Analysis.rank_projects_by_date import rank_projects_chronologically, format_project_timeline


except ImportError:
    print("Could not import functions from either getConsent, zipHandler, fileFormatCheck, or keywordExtractor. Please check the file and function names.")
    sys.exit(1)


# Simple clear command, specifies by OS
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def test_ai_generation():
        """Test AI generation capabilities"""
        clear_console()
        print("=== AI Service Test ===\n")
        
        ai = get_ai_service()
        
        print("1. Generate text from prompt")
        print("2. View usage statistics")
        print("3. Clear cache")
        print("4. Run all examples")
        print("5. Back to main menu")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            prompt = input("\nEnter your prompt: ")
            print("\nGenerating...\n")
            response = ai.generate_text(prompt, max_tokens=200)
            if response:
                print(f"Response:\n{response}\n")
            else:
                print("❌ Generation failed\n")
        
        elif choice == '2':
            ai.print_usage_report()
        
        elif choice == '3':
            ai.clear_cache()
            print("✓ Cache cleared")
        
        input("\nPress Enter to continue...")

def run_project_ranking_test():
    """Rank projects by creation/update date and display"""
    clear_console()
    print("=== Project Timeline ===\n")

    # Sample project data — replace with real DB fetch later
    projects = [
        {"name": "Capstone Project", "created_at": "2023-10-03", "updated_at": "2024-05-15"},
        {"name": "Project 1", "created_at": "2024-02-01", "updated_at": "2024-09-20"},
        {"name": "Project 2", "created_at": "2025-01-12", "updated_at": "2025-03-02"},
    ]

    sorted_projects = rank_projects_chronologically(projects)
    output = format_project_timeline(sorted_projects)
    print(output)

# Console-based dashboard to test initial functions
def dashboard():
    while True:
        clear_console()
        print("=== Console Testing Dashboard ===")
        print("1. Get User Consent")
        print("2. Show Consent Status")
        print("3. Test Keyword Extraction")
        print("4. Test Project Summarizer")
        print("5. Test Coding Project Scanner")
        print("6. Test AI Service")  
        print("7. Show Project Timeline")
        print("8. Exit")

        choice = input("Select an option (1-8): ").strip()

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
            clear_console()
            print("1. Get Keywords")
            print("2. Get Keywords Analytics")
            print("3. Get Keyword Clustering")
            choice = input("Select an option (1-2): ").strip()
            if choice == '1':
                run_keyword_extraction_test()
            elif choice == '2':
                run_keyword_analytics()
            elif choice == '3':
                run_keyword_clustering()
        elif choice == '4':
            test_project_summarizer()
            input("Press Enter to continue...")
        elif choice == '5':
            test_coding_project_scanner()
        elif choice == '6':
            test_ai_generation()   
        elif choice == '7':
            run_project_ranking_test()
            input("Press Enter to continue...")
        elif choice == '8':
            print("Exiting dashboard.")
            break
        else:
            print("Invalid choice. Try again.")
            input("Press Enter to continue...")
def test_project_summarizer():
    """Manual test for summarize_projects"""
    clear_console()
    print("=== Project Summarizer Test ===\n")

    # Sample project data (mocked)
    sample_projects = [
        {
            "project_name": "Portfolio Website",
            "time_spent": 80,
            "success_score": 0.9,
            "contribution_score": 0.7,
            "skills": ["HTML", "CSS", "JavaScript"]
        },
        {
            "project_name": "Machine Learning Model",
            "time_spent": 200,
            "success_score": 0.85,
            "contribution_score": 0.95,
            "skills": ["Python", "TensorFlow", "Data Analysis"]
        },
        {
            "project_name": "Capstone Dashboard",
            "time_spent": 150,
            "success_score": 0.8,
            "contribution_score": 0.85,
            "skills": ["Python", "Flask", "SQL"]
        },
        {
            "project_name": "Unity Game Demo",
            "time_spent": 50,
            "success_score": 0.7,
            "contribution_score": 0.6,
            "skills": ["C#", "Unity", "3D Design"]
        }
    ]

    # Run the summarizer
    result = summarize_projects(sample_projects, top_k=3)
    
    # Print results
    print("\nSelected Top Projects:")
    for p in result["selected_projects"]:
        print(f" - {p['project_name']} (score: {p['overall_score']}) | Skills: {', '.join(p['skills'])}")

    print("\nUnique Skills Covered:")
    print(", ".join(result["unique_skills"]))

    print("\nGenerated Summary:")
    print(result["summary"])



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
        input("\nPress Enter to return to the dashboard...")

    elif mode == '2':
        file_path = input("Enter path to text file: ").strip()
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        input("\nPress Enter to return to the dashboard...")

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
            input("\nPress Enter to return to the dashboard...")
            return

        print("Extracted Code Keywords (with scores):\n")
        for score, phrase in code_results:
            print(f"{score:.2f}  -  {phrase}")
        input("\nPress Enter to return to the dashboard...")
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
    input("\nPress Enter to return to the dashboard...")

def run_keyword_analytics():
    file_path = input("Enter path to text file: ").strip()
    try:
        results = technical_density(file_path)
        print("\nKeyword Analytics Results:\n")
        for key, value in results.items():
            print(f"{key}: {value}")
    except Exception as e:
        print(f"Error: {e}")
    input("\nPress Enter to return to the dashboard...")

def run_keyword_clustering():
    file_path = input("Enter path to text file: ").strip()
    try:
        df = keyword_clustering(file_path)  # use the count-summary function
        if df.empty:
            print("\nNo keywords found.")
        else:
            print("\nKeyword Analytics Results:\n")
            # Print a clean table
            print(df.to_string(index=False))
    except Exception as e:
        print(f"Error: {e}")

    input("\nPress Enter to return to the dashboard...")

def test_coding_project_scanner():
    """Test the coding project scanner"""
    while True:
        clear_console()
        print("=== Coding Project Scanner Test ===\n")
        print("1. Scan a Coding Project")
        print("2. View All Scanned Projects")
        print("3. View Project Details")
        print("4. Delete a Project")
        print("5. View Database Stats")
        print("6. Back to Main Menu")
        
        choice = input("\nSelect an option (1-6): ").strip()
        
        if choice == '1':
            scan_new_project()
        elif choice == '2':
            view_all_projects()
        elif choice == '3':
            view_project_details()
        elif choice == '4':
            delete_project()
        elif choice == '5':
            view_database_stats()
        elif choice == '6':
            break
        else:
            print("Invalid choice. Try again.")
            input("Press Enter to continue...")


def scan_new_project():
    """Scan a new coding project"""
    clear_console()
    print("=== Scan New Coding Project ===\n")
    
    project_path = input("Enter path to coding project directory: ").strip()
    
    if not project_path:
        print("No path provided.")
        input("\nPress Enter to continue...")
        return
    
    if not os.path.exists(project_path):
        print(f"❌ Path does not exist: {project_path}")
        input("\nPress Enter to continue...")
        return
    
    if not os.path.isdir(project_path):
        print(f"❌ Path is not a directory: {project_path}")
        input("\nPress Enter to continue...")
        return
    
    print("\nScanning project...\n")
    
    try:
        project_id = scan_coding_project(project_path)
        
        if project_id:
            print(f"\n✅ Successfully scanned project!")
            print(f"Project ID: {project_id}")
            
            # Show project details
            project = db_manager.get_project(project_id)
            if project:
                print(f"\nProject Summary:")
                print(f"  Name: {project.name}")
                print(f"  Languages: {', '.join(project.languages)}")
                print(f"  Frameworks: {', '.join(project.frameworks) if project.frameworks else 'None'}")
                print(f"  Lines of Code: {project.lines_of_code:,}")
                print(f"  Files: {project.file_count}")
        else:
            print("\n❌ Failed to scan project or no code files found.")
    
    except Exception as e:
        print(f"\n❌ Error scanning project: {e}")
    
    input("\nPress Enter to continue...")


def view_all_projects():
    """View all scanned projects"""
    clear_console()
    print("=== All Scanned Projects ===\n")
    
    try:
        projects = db_manager.get_all_projects()
        
        if not projects:
            print("No projects found in database.")
            input("\nPress Enter to continue...")
            return
        
        print(f"Total Projects: {len(projects)}\n")
        
        # Display in a table format
        print(f"{'ID':<5} {'Name':<30} {'Type':<10} {'Languages':<30} {'LOC':<10}")
        print("-" * 90)
        
        for project in projects:
            languages = ', '.join(project.languages[:3])  # Show first 3 languages
            if len(project.languages) > 3:
                languages += f" (+{len(project.languages) - 3})"
            
            print(f"{project.id:<5} {project.name[:28]:<30} {project.project_type:<10} {languages:<30} {project.lines_of_code:<10,}")
        
    except Exception as e:
        print(f"❌ Error retrieving projects: {e}")
    
    input("\nPress Enter to continue...")


def view_project_details():
    """View detailed information about a specific project"""
    clear_console()
    print("=== View Project Details ===\n")
    
    try:
        project_id = input("Enter project ID: ").strip()
        
        if not project_id.isdigit():
            print("Invalid project ID.")
            input("\nPress Enter to continue...")
            return
        
        project_id = int(project_id)
        project = db_manager.get_project(project_id)
        
        if not project:
            print(f"❌ Project with ID {project_id} not found.")
            input("\nPress Enter to continue...")
            return
        
        # Display detailed information
        print(f"\n{'='*60}")
        print(f"Project: {project.name}")
        print(f"{'='*60}")
        print(f"\nBasic Information:")
        print(f"  ID: {project.id}")
        print(f"  Path: {project.file_path}")
        print(f"  Type: {project.project_type}")
        print(f"  Date Scanned: {project.date_scanned.strftime('%Y-%m-%d %H:%M:%S') if project.date_scanned else 'N/A'}")
        
        print(f"\nMetrics:")
        print(f"  Lines of Code: {project.lines_of_code:,}")
        print(f"  File Count: {project.file_count}")
        print(f"  Total Size: {project.total_size_bytes / (1024*1024):.2f} MB")
        
        print(f"\nTechnologies:")
        print(f"  Languages: {', '.join(project.languages) if project.languages else 'None'}")
        print(f"  Frameworks: {', '.join(project.frameworks) if project.frameworks else 'None'}")
        print(f"  Skills: {', '.join(project.skills[:10]) if project.skills else 'None'}")
        
        # Show top keywords
        keywords = db_manager.get_keywords_for_project(project_id)
        if keywords:
            print(f"\nTop Keywords:")
            for i, kw in enumerate(keywords[:10], 1):
                print(f"  {i}. {kw.keyword} (score: {kw.score:.2f})")
        
        print(f"\n{'='*60}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    input("\nPress Enter to continue...")


def delete_project():
    """Delete a project from the database"""
    clear_console()
    print("=== Delete Project ===\n")
    
    try:
        project_id = input("Enter project ID to delete: ").strip()
        
        if not project_id.isdigit():
            print("Invalid project ID.")
            input("\nPress Enter to continue...")
            return
        
        project_id = int(project_id)
        project = db_manager.get_project(project_id)
        
        if not project:
            print(f"❌ Project with ID {project_id} not found.")
            input("\nPress Enter to continue...")
            return
        
        print(f"\nProject to delete:")
        print(f"  ID: {project.id}")
        print(f"  Name: {project.name}")
        print(f"  Path: {project.file_path}")
        
        confirm = input("\n⚠️  Are you sure you want to delete this project? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            if db_manager.delete_project(project_id):
                print(f"\n✅ Project {project_id} deleted successfully.")
            else:
                print(f"\n❌ Failed to delete project.")
        else:
            print("\nDeletion cancelled.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    input("\nPress Enter to continue...")


def view_database_stats():
    """View database statistics"""
    clear_console()
    print("=== Database Statistics ===\n")
    
    try:
        stats = db_manager.get_stats()
        
        print(f"Total Projects: {stats['total_projects']}")
        print(f"Featured Projects: {stats['featured_projects']}")
        print(f"Total Files: {stats['total_files']}")
        print(f"Total Contributors: {stats['total_contributors']}")
        print(f"Total Keywords: {stats['total_keywords']}")
        
        # Additional stats
        projects = db_manager.get_all_projects()
        if projects:
            total_loc = sum(p.lines_of_code for p in projects)
            print(f"\nAggregate Metrics:")
            print(f"  Total Lines of Code: {total_loc:,}")
            print(f"  Average LOC per Project: {total_loc / len(projects):,.0f}")
            
            # Count by project type
            type_counts = {}
            for p in projects:
                type_counts[p.project_type] = type_counts.get(p.project_type, 0) + 1
            
            print(f"\nProjects by Type:")
            for ptype, count in type_counts.items():
                print(f"  {ptype}: {count}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    input("\nPress Enter to continue...")


if __name__ == "__main__":
    dashboard()