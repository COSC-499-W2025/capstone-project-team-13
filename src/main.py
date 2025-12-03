"""
Digital Artifact Mining Software - Main Entry Point
Integrates all components for a complete workflow

"""
import json
import sys
import os
from pathlib import Path
import re
import math

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Helpers.installDependencies import install_requirements
install_requirements()
from src.Analysis import codeIdentifier, visualMediaAnalyzer
from src.UserPrompts.getConsent import get_user_consent
from src.UserPrompts.externalPermissions import request_ai_consent
from src.Helpers.fileFormatCheck import check_file_format, InvalidFileFormatError
from src.Helpers.fileParser import parse_file, FileParseError
from src.Extraction.zipHandler import (
    validate_zip_file, extract_zip, get_zip_contents, 
    count_files_in_zip, ZipExtractionError
)
from src.Helpers.fileDataCheck import sniff_supertype
from src.Helpers.classifier import supertype_from_extension
from src.Analysis.codingProjectScanner import scan_coding_project
from src.Analysis.textDocumentScanner import scan_text_document
from src.Analysis.mediaProjectScanner import scan_media_project
from src.Analysis.visualMediaAnalyzer import analyze_visual_project
from src.Extraction.keywordExtractorText import extract_keywords_with_scores
from src.Databases.database import db_manager
from src.Analysis.summarizeProjects import summarize_projects
from src.Analysis.runSummaryFromDb import fetch_projects_for_summary
from src.Analysis.projectcollabtype import identify_project_type
from src.AI.ai_project_analyzer import AIProjectAnalyzer
from src.AI.ai_enhanced_summarizer import (
    summarize_projects_with_ai,
    generate_resume_bullets
)
from src.Analysis.importanceScores import assign_importance_scores
from src.Analysis.importanceRanking import get_ranked_projects
from src.Analysis.rank_projects_by_date import rank_projects_chronologically, format_project_timeline
from src.Analysis.codeEfficiency import grade_efficiency
from src.AI.ai_text_project_analyzer import AITextProjectAnalyzer
from src.AI.ai_media_project_analyzer import AIMediaProjectAnalyzer

# Import Resume menu
try:
    from src.Resume.resumeMenu import run_resume_menu
    RESUME_FEATURES_AVAILABLE = True
except ImportError:
    RESUME_FEATURES_AVAILABLE = False
    print("⚠️  Resume features not available (modules not found)")

# Import deletion management features
try:
    from src.deletion_manager import DeletionManager
    from src.enhanced_deletion import (
        delete_project_enhanced,
        bulk_delete_projects,
        view_shared_files_report
    )
    DELETION_FEATURES_AVAILABLE = True
except ImportError:
    DELETION_FEATURES_AVAILABLE = False
    print("⚠️  Deletion features not available (modules not found)")

def clear_screen():
    """Clear console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def detect_project_type(folder_path):
    """
    Automatically detect project type by scanning folder contents
    
    Returns:
        dict: {
            'type': 'code', 'media', 'mixed', or 'unknown',
            'code_count': int,
            'media_count': int,
            'text_count': int,
            'details': str (description)
        }
    """
    from src.Settings.config import EXT_SUPERTYPES
    
    type_counts = {'code': 0, 'media': 0, 'text': 0}
    skip_dirs = {'node_modules', '__pycache__', '.git', '.venv', 'venv', 'env', 
                 'dist', 'build', '.next', '.cache', 'vendor', '__MACOSX'}
    
    # Scan folder and count file types
    for root, dirs, files in os.walk(folder_path):
        # Remove skip directories from dirs list
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        
        for filename in files:
            if filename.startswith('.'):
                continue
                
            ext = os.path.splitext(filename)[1].lower()
            file_type = EXT_SUPERTYPES.get(ext)
            
            if file_type in type_counts:
                type_counts[file_type] += 1
    
    total_files = sum(type_counts.values())
    
    if total_files == 0:
        return {
            'type': 'unknown',
            'code_count': 0,
            'media_count': 0,
            'text_count': 0,
            'details': 'No recognizable files found'
        }
    
    # Calculate percentages
    code_pct = type_counts['code'] / total_files
    media_pct = type_counts['media'] / total_files
    
    # Determine project type
    if code_pct > 0.7:  # More than 70% code files
        project_type = 'code'
        details = f"Primarily code ({type_counts['code']} code files)"
    elif media_pct > 0.7:  # More than 70% media files
        project_type = 'media'
        details = f"Primarily media ({type_counts['media']} media files)"
    elif code_pct > 0.2 and media_pct > 0.2:  # Both significant
        project_type = 'mixed'
        details = f"Mixed project ({type_counts['code']} code, {type_counts['media']} media files)"
    elif type_counts['code'] > 0:  # Any code files present
        project_type = 'code'
        details = f"Small code project ({type_counts['code']} code files)"
    elif type_counts['media'] > 0:  # Any media files present
        project_type = 'media'
        details = f"Small media project ({type_counts['media']} media files)"
    else:
        project_type = 'unknown'
        details = f"Unrecognized project type ({total_files} files)"
    
    return {
        'type': project_type,
        'code_count': type_counts['code'],
        'media_count': type_counts['media'],
        'text_count': type_counts['text'],
        'details': details
    }

def check_if_collaborative(project_path):
    """
    Determine if a project is collaborative by using:
    - metadata (owners, editors)
    - git analysis (if .git exists)
    - file-level contributor extraction
    """

    try:
        from src.Analysis.projectcollabtype import identify_project_type

        # Minimal metadata so the function can still run
        project_data = {"files": []}

        collab_type = identify_project_type(project_path, project_data)
        return collab_type

    except Exception as e:
        print("Collaboration detection error:", e)
        return "Unknown"

def get_user_choice():
    """Get user's choice for what to analyze"""
    print_header("Digital Artifact Mining Software")
    print("What would you like to analyze?\n")
    print("1.  Coding Project (folder containing code files)")
    print("2.  Visual/Media Project (folder containing design/media files)")
    print("3.  Single Document (text file for keyword extraction)")
    print("4.  ZIP Archive (extract and analyze)")
    print("5.  Any Folder (auto-detect type)")
    print("6.  View All Projects in Database")
    print("7.  Generate Project Summary")
    print("8.  Resume Items")
    print("9.  AI Project Analysis")
    print("10. Rank Projects")  
    print("11. Code Efficiency Analysis")
    print("12. Delete Project")
    print("13. Delete AI Insights Only")
    print("14. Exit")
    
    choice = input("\nEnter your choice (1-14): ").strip()
    return choice

def get_path_input(prompt="Enter the path: "):
    """Get and validate path from user"""
    while True:
        path = input(prompt).strip()
        
        if not path:
            print("❌ Please enter a valid path.")
            continue
        
        if not os.path.exists(path):
            print(f"❌ Path does not exist: {path}")
            retry = input("Try again? (yes/no): ").strip().lower()
            if retry != 'yes':
                return None
            continue
        
        return path

def display_project_details(project):
    """Display detailed project information"""
    if not project:
        return
    
    print(f"\n{'='*70}")
    print(f"  📊 Project Analysis Results")
    print(f"{'='*70}")
    print(f"\n📁 Project: {project.name}")
    print(f"   Path: {project.file_path}")
    print(f"   Type: {project.project_type}")
    
    # Show collaboration type if detected
    if hasattr(project, 'collaboration_type') and project.collaboration_type:
        print(f"   Collaboration: {project.collaboration_type}")
    
    if project.date_scanned:
        from datetime import timezone
        # Convert to local time for display
        local_time = project.date_scanned.replace(tzinfo=timezone.utc).astimezone()
        print(f"   Scanned: {local_time.strftime('%Y-%m-%d %H:%M')}")
    
    # Statistics based on project type
    if project.project_type == 'code':
        if project.lines_of_code:
            print(f"\n📈 Statistics:")
            print(f"   Lines of code: {project.lines_of_code:,}")
        if project.file_count:
            print(f"   Files: {project.file_count}")
        if project.languages:
            print(f"   Languages: {', '.join(project.languages[:5])}")
        if project.frameworks:
            print(f"   Frameworks: {', '.join(project.frameworks[:5])}")
    
    elif project.project_type == 'visual_media':
        if project.file_count:
            print(f"\n📈 Statistics:")
            print(f"   Media files: {project.file_count}")
        if project.total_size_bytes:
            size_mb = project.total_size_bytes / (1024 * 1024)
            print(f"   Total size: {size_mb:.2f} MB")
        if project.languages:  # Software used
            print(f"   Software: {', '.join(project.languages[:5])}")
    
    elif project.project_type == 'text':
        if project.word_count:
            print(f"\n📈 Statistics:")
            print(f"   Word count: {project.word_count:,}")
        if project.file_count:
            print(f"   Documents: {project.file_count}")
    
    # Skills
    if project.skills:
        print(f"\n🎯 Skills detected:")
        for skill in project.skills[:8]:
            print(f"   • {skill}")
    
    # Keywords
    keywords = db_manager.get_keywords_for_project(project.id)
    if keywords:
        print(f"\n🔑 Top keywords:")
        for kw in keywords[:5]:
            print(f"   • {kw.keyword} (score: {kw.score:.2f})")
    
    print(f"\n{'='*70}")


def handle_resume_items():
    """Handle resume items menu option"""
    print_header("Resume Items")
    
    if not RESUME_FEATURES_AVAILABLE:
        print("❌ Resume features are not available.")
        print("   Please ensure the Resume module is properly installed.")
        input("\nPress Enter to continue...")
        return
    
    # Check if user has analyzed projects
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("📭 No projects found in database.")
        print("\n⚠️  You need to analyze a project first before generating resume items.")
        print("   Please go back to the main menu and use options 1-5 to analyze a project.")
        input("\nPress Enter to continue...")
        return
    
    # Ask if project has been analyzed
    print("Has the project you want resume items for already been analyzed?\n")
    print("1. Yes - Take me to the Resume menu")
    print("2. No  - I need to analyze it first")
    print("3. Cancel - Return to main menu")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == '1':
        # Show available projects for confirmation
        print(f"\n✓ Found {len(projects)} analyzed project(s) in database:")
        print("-" * 50)
        for i, p in enumerate(projects[:10], 1):
            project_type = p.project_type or "unknown"
            print(f"   {i}. {p.name} ({project_type})")
        if len(projects) > 10:
            print(f"   ... and {len(projects) - 10} more")
        print()
        
        # Launch resume menu
        run_resume_menu()
        
    elif choice == '2':
        print("\n📋 To analyze a project, return to the main menu and select:")
        print("   • Option 1 - For coding projects")
        print("   • Option 2 - For visual/media projects")
        print("   • Option 3 - For text documents")
        print("   • Option 5 - For auto-detection")
        print("\nOnce analyzed, come back here to generate resume items.")
        input("\nPress Enter to return to main menu...")
        
    elif choice == '3':
        print("\nReturning to main menu...")
    else:
        print("\n❌ Invalid option. Returning to main menu...")


# Keep all existing functions from original main.py
# (handle_coding_project, handle_visual_project, handle_document, etc.)
# These are truncated in the upload but should remain unchanged

def handle_coding_project():
    """Handle coding project analysis"""
    print_header("Coding Project Analysis")
    
    path = get_path_input("Enter path to coding project folder: ")
    if not path:
        return
    
    if not os.path.isdir(path):
        print("❌ Path must be a directory.")
        return
    
    print(f"\n🔍 Scanning coding project: {path}")
    
    # Check collaboration type
    collab_type = check_if_collaborative(path)
    print(f"   Collaboration type: {collab_type}")
    
    # Scan project
    project_id = scan_coding_project(path)
    
    if project_id:
        project = db_manager.get_project(project_id)
        display_project_details(project)
    else:
        print("❌ Failed to scan project.")

def handle_visual_project():
    """Handle visual/media project analysis"""
    print_header("Visual/Media Project Analysis")
    
    path = get_path_input("Enter path to media project folder: ")
    if not path:
        return
    
    if not os.path.isdir(path):
        print("❌ Path must be a directory.")
        return
    
    print(f"\n🔍 Scanning media project: {path}")
    
    # Scan project
    project_id = scan_media_project(path)
    
    if project_id:
        project = db_manager.get_project(project_id)
        display_project_details(project)
    else:
        print("❌ Failed to scan project.")

def handle_document():
    """Handle single document analysis"""
    print_header("Document Analysis")
    
    path = get_path_input("Enter path to text document: ")
    if not path:
        return
    
    if not os.path.isfile(path):
        print("❌ Path must be a file.")
        return
    
    print(f"\n🔍 Analyzing document: {path}")
    
    # Scan document
    project_id = scan_text_document(path, single_file=True)
    
    if project_id:
        project = db_manager.get_project(project_id)
        display_project_details(project)
    else:
        print("❌ Failed to analyze document.")

def handle_zip_archive():
    """Handle ZIP archive extraction and analysis"""
    print_header("ZIP Archive Analysis")
    
    path = get_path_input("Enter path to ZIP file: ")
    if not path:
        return
    
    if not path.lower().endswith('.zip'):
        print("❌ File must be a ZIP archive.")
        return
    
    try:
        # Validate ZIP
        validate_zip_file(path)
        
        # Show contents
        contents = get_zip_contents(path)
        file_count = count_files_in_zip(path)
        print(f"\n📦 ZIP contains {file_count} files")
        
        # Extract
        extract_path = get_path_input("Enter extraction destination: ")
        if not extract_path:
            return
        
        print(f"\n📂 Extracting to: {extract_path}")
        extracted = extract_zip(path, extract_path)
        
        print(f"✓ Extracted {len(extracted)} files")
        
        # Auto-detect and analyze
        project_info = detect_project_type(extract_path)
        print(f"\n🔍 Detected: {project_info['details']}")
        
        if project_info['type'] == 'code':
            project_id = scan_coding_project(extract_path)
        elif project_info['type'] == 'media':
            project_id = scan_media_project(extract_path)
        else:
            project_id = scan_text_document(extract_path, single_file=False)
        
        if project_id:
            project = db_manager.get_project(project_id)
            display_project_details(project)
            
    except ZipExtractionError as e:
        print(f"❌ ZIP error: {e}")

def handle_auto_detect():
    """Handle auto-detection of project type"""
    print_header("Auto-Detect Project Type")
    
    path = get_path_input("Enter path to folder: ")
    if not path:
        return
    
    if not os.path.isdir(path):
        print("❌ Path must be a directory.")
        return
    
    print(f"\n🔍 Analyzing folder: {path}")
    
    # Detect type
    project_info = detect_project_type(path)
    print(f"   Detected: {project_info['details']}")
    
    # Scan based on type
    if project_info['type'] == 'code':
        project_id = scan_coding_project(path)
    elif project_info['type'] == 'media':
        project_id = scan_media_project(path)
    elif project_info['type'] == 'text':
        project_id = scan_text_document(path, single_file=False)
    else:
        print("❌ Could not determine project type.")
        return
    
    if project_id:
        project = db_manager.get_project(project_id)
        display_project_details(project)
    else:
        print("❌ Failed to scan project.")

def view_all_projects():
    """View all projects in database"""
    print_header("All Projects in Database")
    
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("📭 No projects found in database.")
        return
    
    print(f"Found {len(projects)} project(s):\n")
    
    for project in projects:
        print(f"{'='*60}")
        print(f"ID: {project.id} | {project.name}")
        print(f"Type: {project.project_type} | Path: {project.file_path}")
        
        if project.project_type == 'code' and project.lines_of_code:
            print(f"LOC: {project.lines_of_code:,}")
        elif project.project_type == 'text' and project.word_count:
            print(f"Words: {project.word_count:,}")
        elif project.project_type == 'visual_media' and project.file_count:
            print(f"Files: {project.file_count}")

def generate_summary():
    """Generate project summary"""
    print_header("Generate Project Summary")
    
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("📭 No projects to summarize.")
        return
    
    print(f"Generating summary for {len(projects)} project(s)...\n")
    
    try:
        summary = summarize_projects(projects)
        print(summary)
    except Exception as e:
        print(f"❌ Error generating summary: {e}")

def ai_project_analysis_menu():
    """AI Project Analysis menu"""
    print_header("AI Project Analysis")
    
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("📭 No projects found.")
        return
    
    print(f"Found {len(projects)} project(s):\n")
    for i, p in enumerate(projects, 1):
        print(f"{i}. {p.name} ({p.project_type})")
    
    try:
        choice = int(input("\nSelect project number: ").strip())
        if 1 <= choice <= len(projects):
            project = projects[choice - 1]
            print(f"\n🤖 Analyzing {project.name} with AI...")
            
            # Use appropriate analyzer based on type
            if project.project_type == 'code':
                analyzer = AIProjectAnalyzer()
            elif project.project_type == 'text':
                analyzer = AITextProjectAnalyzer()
            elif project.project_type == 'visual_media':
                analyzer = AIMediaProjectAnalyzer()
            else:
                analyzer = AIProjectAnalyzer()
            
            result = analyzer.analyze_project(project.id)
            print(result)
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")

def run_importance_test():
    """Run importance scoring test"""
    print_header("Importance Scoring")
    
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("📭 No projects found.")
        return
    
    print("Computing importance scores...\n")
    
    try:
        scores = assign_importance_scores(projects)
        ranked = get_ranked_projects(projects)
        
        for project in ranked:
            print(f"{project.name}: {getattr(project, 'importance_score', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {e}")

def run_project_ranking_test():
    """Run project ranking by date"""
    print_header("Project Timeline")
    
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("📭 No projects found.")
        return
    
    try:
        ranked = rank_projects_chronologically(projects)
        timeline = format_project_timeline(ranked)
        print(timeline)
    except Exception as e:
        print(f"❌ Error: {e}")

def run_code_efficiency_test():
    """Run code efficiency analysis"""
    print_header("Code Efficiency Analysis")
    
    projects = db_manager.get_all_projects()
    code_projects = [p for p in projects if p.project_type == 'code']
    
    if not code_projects:
        print("📭 No code projects found.")
        return
    
    print(f"Found {len(code_projects)} code project(s):\n")
    for i, p in enumerate(code_projects, 1):
        print(f"{i}. {p.name}")
    
    try:
        choice = int(input("\nSelect project number: ").strip())
        if 1 <= choice <= len(code_projects):
            project = code_projects[choice - 1]
            print(f"\n📊 Analyzing efficiency for {project.name}...")
            
            result = grade_efficiency(project.file_path)
            print(f"\nEfficiency Grade: {result.get('grade', 'N/A')}")
            print(f"Score: {result.get('score', 'N/A')}/100")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")

def delete_ai_insights_menu():
    """Delete AI insights for a project"""
    print_header("Delete AI Insights")
    
    if not DELETION_FEATURES_AVAILABLE:
        print("❌ Deletion features not available.")
        return
    
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("📭 No projects found in database.")
        input("\nPress Enter to continue...")
        return
    
    # Display projects
    print(f"Found {len(projects)} project(s):\n")
    print(f"{'ID':<5} {'Name':<40} {'Has AI':<10}")
    print("-" * 60)
    
    for project in projects[:20]:
        name = project.name[:38] + '..' if len(project.name) > 40 else project.name
        has_ai = 'Yes' if (hasattr(project, 'ai_description') and project.ai_description) else 'No'
        print(f"{project.id:<5} {name:<40} {has_ai:<10}")
    
    if len(projects) > 20:
        print(f"\n... and {len(projects) - 20} more projects")
    
    # Get project ID
    print()
    project_id = input("Enter project ID (or press Enter to cancel): ").strip()
    
    if not project_id:
        return
    
    if not project_id.isdigit():
        print("❌ Invalid project ID")
        input("\nPress Enter to continue...")
        return
    
    project_id = int(project_id)
    project = db_manager.get_project(project_id)
    
    if not project:
        print(f"❌ Project {project_id} not found")
        input("\nPress Enter to continue...")
        return
    
    # Get deletion preview
    manager = DeletionManager()
    preview = manager.get_deletion_preview(project_id)
    
    print(f"\n📁 Project: {preview['project_name']}")
    print(f"   AI insights in database: {'Yes' if preview['has_ai_insights'] else 'No'}")
    print(f"   Cached analysis files: {preview['cache_files_found']}")
    
    if not preview['has_ai_insights'] and preview['cache_files_found'] == 0:
        print("\n✅ No AI insights to delete")
        input("\nPress Enter to continue...")
        return
    
    # Confirm deletion
    confirm = input("\n⚠️  Delete AI insights? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        print("\n🔄 Deleting AI insights...")
        results = manager.delete_ai_insights_for_project(project_id)
        
        print(f"\n✅ Deletion complete!")
        print(f"  Database updated: {'Yes' if results['db_updated'] else 'No'}")
        print(f"  Cache files deleted: {results['cache_files_deleted']}")
        
        if results['errors']:
            print("\n⚠️  Errors:")
            for error in results['errors']:
                print(f"  • {error}")
    else:
        print("\nDeletion cancelled")
    
    input("\nPress Enter to continue...")


def main():
    """Main application loop"""
    clear_screen()
    
    # Step 1: Get user consent for device access
    print_header("Welcome to Digital Artifact Mining Software")
    print("This application helps you analyze and organize your digital work.\n")
    
    consent = get_user_consent()
    if consent != 'allow':
        print("\n❌ Device access denied. Cannot proceed.")
        sys.exit(0)
    
    clear_screen()
    
    # Main application loop
    while True:
        choice = get_user_choice()
        
        if choice == '1':
            handle_coding_project()
        elif choice == '2':
            handle_visual_project()
        elif choice == '3':
            handle_document()
        elif choice == '4':
            handle_zip_archive()
        elif choice == '5':
            handle_auto_detect()
        elif choice == '6':
            view_all_projects()
        elif choice == '7':
            generate_summary()
        elif choice == '8':
            handle_resume_items()
        elif choice == '9':
            ai_project_analysis_menu()
        elif choice == '10':
            print("\n--- Importance Score Menu ---")
            print("1. Sort projects by date")
            print("2. Compute/grade importance scores")
            sub = input("Select an option (1 or 2): ").strip()

            if sub == '1':
                run_project_ranking_test()
            elif sub == '2':
                run_importance_test()
            else:
                print("Invalid choice. Returning to main menu.")
        elif choice == '11':
            run_code_efficiency_test()
        elif choice == "12":
            if DELETION_FEATURES_AVAILABLE:
                delete_project_enhanced()
            else:
                print("❌ Deletion features not available.")
        elif choice == "13":
            if DELETION_FEATURES_AVAILABLE:
                delete_ai_insights_menu()
            else:
                print("❌ Deletion features not available.")
        elif choice == "14":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")
        
        input("\n⏸️  Press Enter to continue...")
        clear_screen()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)