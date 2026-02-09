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
from datetime import datetime, timezone

# Filter out Git error messages globally
_original_print = print
def print(*args, **kwargs):
    message = ' '.join(str(arg) for arg in args)
    if 'Git' not in message and 'git' not in message:
        _original_print(*args, **kwargs)
import builtins
builtins.print = print



# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.Databases.user_config import ConfigManager

from src.Helpers.installDependencies import install_requirements
install_requirements()
from src.UserPrompts.getConsent import get_user_consent
from src.UserPrompts.config_integration import (
    show_current_configuration,
    configure_privacy_settings,
    configure_analysis_preferences,
    request_and_store_basic_consent,
    request_and_store_ai_consent,
    quick_setup_wizard,
    config_manager,
)
from src.UserPrompts.externalPermissions import request_ai_consent
from src.Extraction.zipHandler import (
    validate_zip_file, extract_zip, get_zip_contents, 
    count_files_in_zip, ZipExtractionError, InvalidFileFormatError
)
from src.Portfolio.portfolioFormatter import PortfolioFormatter
from src.Helpers.fileDataCheck import sniff_supertype
from src.Helpers.classifier import supertype_from_extension
from src.Analysis.codingProjectScanner import scan_coding_project
from src.Analysis.textDocumentScanner import scan_text_document
from src.Analysis.mediaProjectScanner import scan_media_project
from src.Analysis.visualMediaAnalyzer import analyze_visual_project
from src.Extraction.keywordExtractorText import extract_keywords_with_scores
from src.Analysis.summarizeProjects import summarize_projects
from src.Analysis.runSummaryFromDb import fetch_projects_for_summary
from src.Analysis.projectcollabtype import identify_project_type
from src.AI.ai_project_analyzer import AIProjectAnalyzer
from src.AI.ai_project_ranker import AIProjectRanker
from src.AI.ai_enhanced_summarizer import (
    summarize_projects_with_ai,
    generate_resume_bullets
)
from src.Analysis.importanceScores import assign_importance_scores
from src.Analysis.importanceRanking import get_ranked_projects
from src.Analysis.rank_projects_by_date import get_ranked_timeline_from_db
from src.Analysis.codeEfficiency import grade_efficiency
from src.Analysis.folderEfficiency import grade_folder
from src.AI.ai_text_project_analyzer import AITextProjectAnalyzer
from src.AI.ai_media_project_analyzer import AIMediaProjectAnalyzer
from src.Analysis.incrementalZipHandler import handle_incremental_zip_upload
from src.Analysis.incrementalFileHandler import handle_add_files_to_project
from src.Databases.database import db_manager

# Import evidence management features
try:
    from src.Evidence.evidenceMenu import evidence_main_menu
    from src.Evidence.evidenceManager import evidence_manager
    EVIDENCE_FEATURES_AVAILABLE = True
except ImportError:
    EVIDENCE_FEATURES_AVAILABLE = False
    print("⚠️  Evidence management features not available (modules not found)")

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

# Import resume menu
try:
    from src.Resume.resumeMenu import run_resume_menu
    RESUME_FEATURES_AVAILABLE = True
except ImportError:
    RESUME_FEATURES_AVAILABLE = False
    print("⚠️  Resume features not available (modules not found)")

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
    import sys
    from io import StringIO

    try:
        from src.Analysis.projectcollabtype import identify_project_type

        # Suppress all output (stdout and stderr)
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        
        try:
            project_data = {"files": []}
            collab_type = identify_project_type(project_path, project_data)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        return collab_type

    except Exception:
        return "Unknown"

def extract_evidence_for_project(project_id: int, project_path: str):
    """
    Helper function to automatically extract evidence after project upload
    
    Args:
        project_id: Database ID of the project
        project_path: Path to project directory
    """
    if not EVIDENCE_FEATURES_AVAILABLE:
        return
    
    try:
        project = db_manager.get_project(project_id)
        if not project:
            return
        
        print("\n🔍 Extracting evidence of success from project files...")
        evidence = evidence_manager.extract_and_store_evidence(project, project_path)
        
        if evidence and len(evidence) > 0:
            print("✅ Evidence extracted successfully!")
            
            # Show highlights
            if 'test_coverage' in evidence:
                print(f"   - Test Coverage: {evidence['test_coverage']}%")
            
            # Note: Git statistics are shown separately in Git insights
            
            if 'readme_badges' in evidence and evidence['readme_badges']:
                print(f"   - README Badges: {len(evidence['readme_badges'])} found")
            
            # Calculate success score from evidence (0-100%)
            success_score = 0.0
            if 'test_coverage' in evidence and evidence['test_coverage']:
                success_score += evidence['test_coverage'] * 0.6  # 60% weight
            if 'readme_badges' in evidence and evidence['readme_badges']:
                badge_score = min(len(evidence['readme_badges']) * 10, 40)  # up to 40%
                success_score += badge_score
            
            # Store success_score in database
            db_manager.update_project(project_id, {'success_score': success_score})
            
            print("\n   💡 You can view full evidence details in: View & Analysis > Manage Project Evidence")
        else:
            print("ℹ️  No automatic evidence found.")
            print("   💡 You can add evidence manually in: View & Analysis > Manage Project Evidence")
    
    except Exception as e:
        print(f"⚠️  Could not extract evidence: {e}")



def get_user_choice():
    """Simplified main menu with three submenus and exit"""
    print_header("Digital Artifact Mining Software - Main Menu")
    print("Choose an option:\n")
    print("1. Upload a Project or Thumbnail")
    print("2. View and Analyze Previously Uploaded Projects")
    print("3. Resume Tools")
    print("4. AI Menu")
    print("5. Delete")
    print("6. Settings")
    print("7. Exit")

    choice = input("\nEnter your choice (1-7): ").strip()
    return choice

def get_path_input(prompt="Enter the path: "):
    """Get and validate path from user"""
    while True:
        raw = input(prompt)
        if not raw:
            print("❌ Please enter a valid path.")
            continue

        # 🔧 sanitize input (handles ", ', and smart quotes)
        path = raw.strip().strip('"\'' + "“”‘’")
        path = os.path.abspath(os.path.expanduser(path))

        if not os.path.exists(path):
            print(f"❌ Path does not exist: {path}")  # print sanitized path
            retry = input("Try again? (yes/no): ").strip().lower()
            if retry not in ("yes", "y"):
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
        print(f"   Scanned: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    if project.project_type == 'code':
        print(f"\n📈 Code Metrics:")
        print(f"   Lines of Code: {project.lines_of_code:,}")
        print(f"   File Count: {project.file_count}")
        print(f"   Total Size: {project.total_size_bytes / (1024*1024):.2f} MB")
        
        if project.date_created and project.date_modified:
            # Ensure dates are logical (created <= modified)
            first = min(project.date_created, project.date_modified)
            last = max(project.date_created, project.date_modified)
            print(f"   First Created: {first.strftime('%Y-%m-%d')}")
            print(f"   Last Modified: {last.strftime('%Y-%m-%d')}")
        elif project.date_created:
            print(f"   First Created: {project.date_created.strftime('%Y-%m-%d')}")
        elif project.date_modified:
            print(f"   Last Modified: {project.date_modified.strftime('%Y-%m-%d')}")
        
        print(f"\n💻 Technologies:")
        if project.languages:
            print(f"   Languages: {', '.join(project.languages)}")
        if project.frameworks:
            print(f"   Frameworks: {', '.join(project.frameworks)}")
        if project.skills:
            print(f"   Skills Detected: {', '.join(project.skills[:10])}")
            if len(project.skills) > 10:
                print(f"                    ... and {len(project.skills) - 10} more")
        
        # Show AI insights if available
        if hasattr(project, 'ai_description') and project.ai_description:
            print(f"\n🤖 AI-Generated Description:")
            print(f"   {project.ai_description}")
        
        # Show contributors if any
        contributors = db_manager.get_contributors_for_project(project.id)
        if contributors:
            print(f"\n👥 Contributors ({len(contributors)}):")
            for contrib in contributors[:5]:
                print(f"   • {contrib.name} ({contrib.commit_count} commits)")
            if len(contributors) > 5:
                print(f"   ... and {len(contributors) - 5} more")
        
        # Show keywords
        keywords = db_manager.get_keywords_for_project(project.id)
        if keywords:
            print(f"\n🔑 Top Keywords:")
            for i, kw in enumerate(keywords[:10], 1):
                print(f"   {i:2d}. {kw.keyword} (score: {kw.score:.2f})")
    
    elif project.project_type == 'media':
        print(f"\n📊 Media Metrics:")
        print(f"   File Count: {project.file_count}")
        if project.skills:
            print(f"   Skills: {', '.join(project.skills)}")
        if project.tags:
            print(f"   Software: {', '.join(project.tags)}")
    
    # Show if files are shared with other projects
    if DELETION_FEATURES_AVAILABLE:
        try:
            manager = DeletionManager()
            shared_files = manager.get_shared_files(project.id)
            if shared_files:
                print(f"\n⚠️  Shared Files:")
                print(f"   {len(shared_files)} file(s) are used in other projects")
        except:
            pass
    
    print(f"\n{'='*70}")

def sanitize_path(p: str) -> str:
    if p is None:
        return ""

    # trim whitespace
    p = p.strip()

    # handle pasted “smart quotes” too
    p = p.strip('"\'' + "“”‘’")

    # also remove any remaining quote characters anywhere (rare but safe)
    p = p.replace('"', '').replace("'", "").replace("“", "").replace("”", "").replace("‘", "").replace("’", "")

    return os.path.abspath(os.path.expanduser(p))

def handle_coding_project():
    """Handle scanning a coding project"""
    print_header("Scan Coding Project")
    
    path = get_path_input("Enter path to coding project folder: ")
    if not path:
        return
    
    print("RAW:", repr(path))

    # your sanitize logic...
    path = path.strip()
    if (path.startswith('"') and path.endswith('"')) or (path.startswith("'") and path.endswith("'")):
        path = path[1:-1]
    path = os.path.abspath(os.path.expanduser(path))

    print("SANITIZED:", repr(path))
    
    
    # Check if collaborative
    print("\n🔍 Analyzing collaboration type...")
    collab_type = check_if_collaborative(path)
    
    if collab_type == 'Collaborative Project':
        print(f"🤝 Collaborative Project Detected")
    elif collab_type == 'Individual Project':
        print(f"👤 Individual Project Detected")
    else:
        print(f"❓ Collaboration Type: Unknown")
    
    # The scanner handles all the analysis, duplicate detection, and display internally
    project_id = scan_coding_project(path)
    
    if not project_id:
        print("\n❌ Failed to scan project or no code files found.")
        return
    
    # Update collaboration type if detected
    if collab_type != 'Unknown (no contributor data found)':
        db_manager.update_project(project_id, {'collaboration_type': collab_type})
    
    # Extract evidence of success
    extract_evidence_for_project(project_id, path)

# ============================================
# PATCH FOR handle_visual_project()
# ============================================

def handle_visual_project():
    """Handle analyzing a visual/media project"""
    print_header("Analyze Visual/Media Project")
    
    path = get_path_input("Enter path to media project folder: ")
    if not path:
        return
    
    # Normalize path to absolute for consistent comparison
    path = os.path.abspath(path)
    
    # Check if already exists BEFORE scanning
    existing = db_manager.get_project_by_path(path)
    if existing:
        # ============ START OF CHANGE ============
        print(f"\n✅ PROJECT ALREADY EXISTS IN DATABASE")
        print(f"="*70)
        print(f"   Project Name: {existing.name}")
        print(f"   Project ID: {existing.id}") 
        print(f"   Type: {existing.project_type}")
        print(f"   Files: {existing.file_count}")
        
        if existing.date_scanned:
            from datetime import timezone
            local_time = existing.date_scanned.replace(tzinfo=timezone.utc).astimezone()
            print(f"   Last Scanned: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n💡 No duplicate created - using existing project.")
        print(f"\n   To add more files, use:")
        print(f"   • Upload Menu → Add individual file(s)")
        print(f"   • Upload Menu → Add ZIP to existing project")
        print(f"="*70)
        
        display_project_details(existing)
        return
        # ============ END OF CHANGE ============
    
    # The scanner handles all the analysis and display internally
    project_id = scan_media_project(path)
    
    if not project_id:
        print("\n❌ Failed to scan project or no media files found.")
        return
    
    # Extract evidence of success
    extract_evidence_for_project(project_id, path)

def handle_document():
    """Handle scanning a single text document"""
    print_header("Scan Text Document")
    
    path = get_path_input("Enter path to document: ")
    if not path:
        return
    
    # if not os.path.isfile(path):
    #     print("❌ Path must be a file")
    #     return
    
    # Normalize path to absolute for consistent comparison
    path = os.path.abspath(path)
    
    # Check if already exists BEFORE scanning
    existing = db_manager.get_project_by_path(path)
    if existing:
        print(f"\n⚠️  This document already exists in the database!")
        print(f"   Project: {existing.name}")
        print(f"   Database ID: {existing.id}") 
        if existing.date_scanned:
            from datetime import timezone
            local_time = existing.date_scanned.replace(tzinfo=timezone.utc).astimezone()
            print(f"   Last scanned: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        rescan = input("\n   Would you like to re-scan and update? (yes/no): ").strip().lower()
        if rescan != 'yes':
            print("\n✅ Using existing project data.")
            return
        
        # Delete old project to re-scan
        print("\n⏳ Deleting old data and re-scanning...")
        db_manager.delete_project(existing.id)
        
    # The scanner handles all the analysis and display internally
    project_id = scan_text_document(path, single_file=True)
    
    if not project_id:
        print("\n❌ Failed to scan document.")
        return
    
    # Extract evidence of success
    extract_evidence_for_project(project_id, os.path.dirname(path))

def handle_zip_archive():
    """Handle ZIP archive extraction and analysis"""
    print_header("Extract and Analyze ZIP Archive")
    
    path = get_path_input("Enter path to ZIP file: ")
    if not path:
        return
    
    if not path.lower().endswith('.zip'):
        print("❌ File must have .zip extension")
        return
    
    # Store original ZIP name for later use
    original_zip_name = os.path.splitext(os.path.basename(path))[0]
    
    try:
        # Validate ZIP
        validate_zip_file(path)
        print("✅ Valid ZIP file")
        
        # Get contents
        contents = get_zip_contents(path)
        file_count = count_files_in_zip(path)
        
        print(f"\n📦 ZIP Contents:")
        print(f"   Total items: {len(contents)}")
        print(f"   Files: {file_count}")
        print(f"   Folders: {len(contents) - file_count}")
        
        # Show preview
        print("\n   Contents preview (first 20 items):")
        for item in contents[:20]:
            item_type = "📁" if item.endswith('/') else "📄"
            print(f"      {item_type} {item}")
        
        if len(contents) > 20:
            print(f"      ... and {len(contents) - 20} more items")
        
        # Ask if user wants to extract and analyze
        extract = input("\n📂 Extract and analyze? (yes/no): ").strip().lower()
        if extract != 'yes':
            return
        
        print("\n⏳ Extracting...")
        extract_path = extract_zip(path)
        print(f"✅ Extracted to: {extract_path}")
        
        # Check if collaborative
        print("\n🔍 Analyzing collaboration type...")
        collab_type = check_if_collaborative(extract_path)
        if collab_type == 'Collaborative Project':
            print("🤝 Collaborative project detected")
        elif collab_type == 'Individual Project':
            print("👤 Individual project detected")
        
        # ====================================================================
        # COMPREHENSIVE MULTI-TYPE FILE SCANNING
        # Use scanner classes directly to avoid duplicate path conflicts
        # ====================================================================
        
        print("\n" + "="*70)
        print("  🔍 ANALYZING ALL FILES IN ZIP")
        print("="*70)
        
        # Import scanner classes
        from src.Analysis.codingProjectScanner import CodingProjectScanner
        from src.Analysis.mediaProjectScanner import MediaProjectScanner
        from src.Analysis.textDocumentScanner import TextDocumentScanner
        
        main_project_id = None
        all_file_data = []
        all_keywords = []
        combined_metadata = {
            'languages': set(),
            'frameworks': set(),
            'skills': set(),
            'tags': set(),
            'software': set(),
            'total_files': 0,
            'total_size': 0,
            'word_count': 0,
            'lines_of_code': 0
        }
        
        # Step 1: Scan code files
        print("\n⏳ Step 1: Scanning for code files...")
        try:
            code_scanner = CodingProjectScanner(extract_path)
            code_scanner._find_code_files()
            
            if code_scanner.code_files:
                print(f"  ✓ Found {len(code_scanner.code_files)} code files")
                code_scanner._detect_languages_and_frameworks()
                
                # Collect code file data
                for file_path in code_scanner.code_files:
                    from src.Analysis.file_hasher import compute_file_hash
                    all_file_data.append({
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'file_type': file_path.suffix,
                        'file_size': file_path.stat().st_size,
                        'file_created': datetime.fromtimestamp(file_path.stat().st_ctime, tz=timezone.utc),
                        'file_modified': datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
                        'file_hash': compute_file_hash(str(file_path))
                    })
                
                combined_metadata['languages'].update(code_scanner.languages)
                combined_metadata['frameworks'].update(code_scanner.frameworks)
                combined_metadata['total_files'] += len(code_scanner.code_files)
                print(f"  ✓ Languages: {', '.join(code_scanner.languages) or 'None'}")
                print(f"  ✓ Frameworks: {', '.join(code_scanner.frameworks) or 'None'}")
            else:
                print("  No code files found")
        except Exception as e:
            print(f"  ⚠️  Code scanning error: {str(e)}")
        
        # Step 2: Scan media files
        print("\n⏳ Step 2: Scanning for media files...")
        try:
            media_scanner = MediaProjectScanner(extract_path)
            media_scanner._find_files()
            
            if media_scanner.media_files:
                print(f"  ✓ Found {len(media_scanner.media_files)} media files")
                media_scanner._analyze_media()
                
                # Collect media file data
                for file_path in media_scanner.media_files:
                    from src.Analysis.file_hasher import compute_file_hash
                    all_file_data.append({
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'file_type': file_path.suffix,
                        'file_size': file_path.stat().st_size,
                        'file_created': datetime.fromtimestamp(file_path.stat().st_ctime, tz=timezone.utc),
                        'file_modified': datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
                        'file_hash': compute_file_hash(str(file_path))
                    })
                
                combined_metadata['software'].update(media_scanner.software_used)
                combined_metadata['skills'].update(media_scanner.skills_detected)
                combined_metadata['total_files'] += len(media_scanner.media_files)
                print(f"  ✓ Software: {', '.join(sorted(media_scanner.software_used)[:5]) or 'None'}")
                print(f"  ✓ Skills: {', '.join(sorted(media_scanner.skills_detected)[:5]) or 'None'}")
                
                # Collect media keywords
                media_scanner._extract_keywords()
                for keyword, score in media_scanner.all_keywords:
                    all_keywords.append({'keyword': keyword, 'score': score, 'category': 'media'})
            else:
                print("  No media files found")
        except Exception as e:
            print(f"  ⚠️  Media scanning error: {str(e)}")
        
        # Step 3: Scan text documents
        print("\n⏳ Step 3: Scanning for text documents...")
        try:
            text_scanner = TextDocumentScanner(extract_path)
            text_scanner._find_text_files()
            
            if text_scanner.text_files:
                print(f"  ✓ Found {len(text_scanner.text_files)} text files")
                text_scanner._detect_document_types()
                
                # Collect text file data
                for file_path in text_scanner.text_files:
                    from src.Analysis.file_hasher import compute_file_hash
                    all_file_data.append({
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'file_type': file_path.suffix,
                        'file_size': file_path.stat().st_size,
                        'file_created': datetime.fromtimestamp(file_path.stat().st_ctime, tz=timezone.utc),
                        'file_modified': datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
                        'file_hash': compute_file_hash(str(file_path))
                    })
                
                combined_metadata['tags'].update(text_scanner.document_types)
                combined_metadata['total_files'] += len(text_scanner.text_files)
                print(f"  ✓ Document types: {', '.join(sorted(text_scanner.document_types)) or 'None'}")
                
                # Collect text keywords
                text_scanner._extract_keywords()
                for keyword, score in text_scanner.all_keywords:
                    all_keywords.append({'keyword': keyword, 'score': score, 'category': 'text'})
            else:
                print("  No text documents found")
        except Exception as e:
            print(f"  ⚠️  Text scanning error: {str(e)}")
        
        # Step 4: Create single comprehensive project
        print("\n⏳ Step 4: Creating comprehensive project...")
        if all_file_data:
            # Determine project type
            has_code = any('languages' in str(combined_metadata) and combined_metadata['languages'])
            has_media = any('software' in str(combined_metadata) and combined_metadata['software'])
            has_text = any('tags' in str(combined_metadata) and combined_metadata['tags'])
            
            if (has_code and has_media) or (has_code and has_text) or (has_media and has_text):
                project_type = 'mixed'
            elif has_code:
                project_type = 'code'
            elif has_media:
                project_type = 'visual_media'
            else:
                project_type = 'text'
            
            # Calculate total size
            total_size = sum(f['file_size'] for f in all_file_data)
            
            # Create project
            project_data = {
                'name': original_zip_name,
                'file_path': extract_path,
                'project_type': project_type,
                'file_count': len(all_file_data),
                'total_size_bytes': total_size,
                'languages': list(combined_metadata['languages']),
                'frameworks': list(combined_metadata['frameworks']),
                'skills': list(combined_metadata['skills'].union(combined_metadata['software']))[:20],
                'tags': list(combined_metadata['tags'].union(combined_metadata['software'])),
                'date_scanned': datetime.now(timezone.utc),
                'collaboration_type': collab_type if collab_type != 'Unknown (no contributor data found)' else None
            }
            
            project = db_manager.create_project(project_data)
            main_project_id = project.id
            
            # Calculate and store importance score
            from src.Analysis.importanceScores import calculate_importance_score
            importance_score = calculate_importance_score(project)
            db_manager.update_project(main_project_id, {'importance_score': importance_score})
            
            print(f"  ✓ Project created (ID: {main_project_id}, Type: {project_type})")
            
            # Store all files
            print(f"\n⏳ Step 5: Storing {len(all_file_data)} files...")
            for file_data in all_file_data:
                file_data['project_id'] = main_project_id
                db_manager.add_file_to_project(file_data)
            print(f"  ✓ All files stored")
            
            # Store keywords
            if all_keywords:
                print(f"\n⏳ Step 6: Storing {len(all_keywords)} keywords...")
                for kw_data in all_keywords[:50]:  # Top 50 keywords
                    db_manager.add_keyword({
                        'project_id': main_project_id,
                        'keyword': kw_data['keyword'],
                        'score': kw_data['score'],
                        'category': kw_data.get('category', 'general')
                    })
                print(f"  ✓ Keywords stored")
        else:
            print("  ⚠️  No files found to process")
        
        # Final summary
        print("\n" + "="*70)
        if main_project_id:
            final_project = db_manager.get_project(main_project_id)
            
            if final_project:
                print(f"✅ ZIP UPLOAD COMPLETE!")
                print("="*70)
                print(f"  Project Name: {final_project.name}")
                print(f"  Project ID: {final_project.id}")
                print(f"  Project Type: {final_project.project_type}")
                print(f"  Total Files: {final_project.file_count}")
                if final_project.total_size_bytes:
                    print(f"  Total Size: {final_project.total_size_bytes / (1024*1024):.2f} MB")
                if final_project.languages:
                    print(f"  Languages: {', '.join(final_project.languages)}")
                if final_project.tags:
                    print(f"  Software/Types: {', '.join(final_project.tags[:10])}")
                if final_project.skills:
                    print(f"  Skills: {', '.join(final_project.skills[:10])}")
                print("="*70)
            else:
                print(f"⚠️  Error: Could not retrieve project with ID {main_project_id}")
                print("="*70)
        else:
            print("⚠️  No recognizable files found in ZIP")
            print("="*70)
            
    except (InvalidFileFormatError, ZipExtractionError) as e:
        print(f"\n❌ ZIP error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

def handle_auto_detect():
    """Handle auto-detection of any folder type"""
    print_header("Auto-Detect Folder Type")
    
    path = get_path_input("Enter path to any folder: ")
    if not path:
        return
    
    if not os.path.isdir(path):
        print("❌ Path must be a directory (folder)")
        return
    
    # Normalize path
    path = os.path.abspath(path)
    
    # Check if already exists
    existing = db_manager.get_project_by_path(path)
    if existing:
        print(f"\n⚠️  This project already exists in database (ID: {existing.id})")
        display_project_details(existing)
        return
    
    # Detect project type
    print("\n🔍 Analyzing folder contents...")
    detection_result = detect_project_type(path)
    project_type = detection_result['type']
    
    print(f"\n✅ Detection Result:")
    print(f"   {detection_result['details']}")
    print(f"   Type: {project_type}")
    
    # Check if collaborative
    collab_type = check_if_collaborative(path)
    if collab_type == 'Collaborative Project':
        print("   🤝 Collaborative project")
    elif collab_type == 'Individual Project':
        print("   👤 Individual project")
    
    # Proceed based on type
    if project_type == 'code':
        proceed = input("\n📝 Proceed with code analysis? (yes/no): ").strip().lower()
        if proceed == 'yes':
            project_id = scan_coding_project(path)
            if project_id:
                
                if collab_type != 'Unknown (no contributor data found)':
                    db_manager.update_project(project_id, {'collaboration_type': collab_type})
                
                # Extract evidence of success
                extract_evidence_for_project(project_id, path)
                
    elif project_type == 'media':
        proceed = input("\n📝 Proceed with media analysis? (yes/no): ").strip().lower()
        if proceed == 'yes':
            result = analyze_visual_project(path)
            if result['num_files'] > 0:
                store = input("\n💾 Store in database? (yes/no): ").strip().lower()
                if store == 'yes':
                    project_data = {
                        'name': os.path.basename(path),
                        'file_path': path,
                        'file_count': result['num_files'],
                        'project_type': 'media',
                        'skills': result['skills_detected'],
                        'tags': result['software_used']
                    }
                    project = db_manager.create_project(project_data)
                    print(f"✅ Stored with ID: {project.id}")
                    
                    # Extract evidence of success
                    extract_evidence_for_project(project.id, path)
                    
    elif project_type == 'mixed':
        print("\n📦 This folder contains both code and media files.")
        choice = input("Analyze as: (1) Code project, (2) Media project, (3) Both: ").strip()
        
        if choice in ['1', '3']:
            print("\n⏳ Analyzing code files...")
            project_id = scan_coding_project(path)
            if project_id:
                if collab_type != 'Unknown (no contributor data found)':
                    db_manager.update_project(project_id, {'collaboration_type': collab_type})
                
                # Extract evidence of success
                extract_evidence_for_project(project_id, path)
        
        if choice in ['2', '3']:
            print("\n⏳ Analyzing media files...")
            result = analyze_visual_project(path)
            if result['num_files'] > 0 and choice == '3':
                store = input("\n💾 Store media analysis separately? (yes/no): ").strip().lower()
                if store == 'yes':
                    project_data = {
                        'name': f"{os.path.basename(path)} (Media)",
                        'file_path': path,
                        'file_count': result['num_files'],
                        'project_type': 'media',
                        'skills': result['skills_detected'],
                        'tags': result['software_used']
                    }
                    project = db_manager.create_project(project_data)
                    print(f"✅ Media analysis stored with ID: {project.id}")
    else:
        print("\n⚠️  Unable to analyze this folder.")
        print("   It may not contain recognizable project files.")


def view_all_projects():
    """View all projects in database"""
    print_header("All Projects in Database")
    
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("📭 No projects found in database.")
        print("\nTip: Scan some projects first using options 1-5!")
        return
    
    print(f"Found {len(projects)} project(s):\n")
    
    # Display table header
    print(f"{'ID':<5} {'Name':<35} {'Type':<10} {'Collab':<8} {'Languages/Skills':<30}")
    print("-" * 98)
    
    # Display each project
    for project in projects:
        # Get languages or skills
        info = ', '.join(project.languages[:3]) if project.languages else ', '.join(project.skills[:3]) if project.skills else 'N/A'
        if len(project.languages) > 3:
            info += f" (+{len(project.languages) - 3})"
        
        name = project.name[:33] + '..' if len(project.name) > 35 else project.name
        collab = project.collaboration_type[:6] if hasattr(project, 'collaboration_type') and project.collaboration_type else 'Solo'
        
        print(f"{project.id:<5} {name:<35} {project.project_type:<10} {collab:<8} {info:<30}")
    
    # Offer to view details
    view_detail = input("\n🔍 Enter project ID to view details (or press Enter to skip): ").strip()
    if view_detail.isdigit():
        project = db_manager.get_project(int(view_detail))
        if project:
            display_project_details(project)

def view_saved_showcases():
    print_header("Saved Showcase Projects")

    formatter = PortfolioFormatter()

    # pull only featured projects
    featured_projects = db_manager.get_featured_projects()

    if not featured_projects:
        print("📭 No showcase projects saved yet.")
        print("Tip: Customize a project and set Featured = y (and Hidden = n).")
        return

    # format as cards (reuse your portfolio formatter)
    cards = [formatter._format_project_card(p) for p in featured_projects]

    # sort by rank (if set), then importance
    def sort_key(card):
        rank = card.get("user_rank")
        rank_key = rank if rank is not None else 10**9
        return (rank_key, -card.get("importance_score", 0))

    cards.sort(key=sort_key)

    print(f"⭐ Showcase projects found: {len(cards)}\n")
    for i, card in enumerate(cards, 1):
        formatter._display_project_card(card, i, featured=True)

def _apply_showcase_preset(selected_projects: list[dict]):
    """
    Marks selected projects as featured and assigns rank.
    """
    if not selected_projects:
        print("⚠️ No projects to save.")
        return

    print("DEBUG saving projects:", selected_projects)

    for i, p in enumerate(selected_projects, start=1):
        pid = p.get("project_id") 

        if not pid:
            print(f"⚠️ Skipping project without ID: {p.get('project_name')}")
            continue

        db_manager.update_project(pid, {
            "is_featured": True,
            "is_hidden": False,   # ensure visible
            "user_rank": i,
        })

        print(f"Saved: {p.get('project_name')} (ID {pid}) as rank {i}")


def generate_summary():
    print_header("Generate Project Summary + Portfolio")

    formatter = PortfolioFormatter()
    project_dicts = formatter.get_projects_for_summary_input(include_hidden=False)
    
    if not project_dicts:
        print("📭 No projects found in database.")
        return
        

    result = summarize_projects(project_dicts, top_k=min(5, len(project_dicts)))
    print("DEBUG selected IDs:", [(p.get("project_id"), p.get("project_name")) for p in result.get("selected_projects", [])])

    print("=" * 70)
    print("  📊 PROJECT PORTFOLIO SUMMARY")
    print("=" * 70)
    print(f"\n{result.get('summary', '')}\n")

    # Show portfolio view (your new style)
    formatter.display_portfolio_view()

    print("\nWhat would you like to do next?")
    print("  S) Save top projects as Showcase (feature + rank them)")
    print("  C) Customize a project")
    print("  Enter) Back")
    choice = input("Choice: ").strip().lower()

    if choice == "s":
        _apply_showcase_preset(result.get("selected_projects", []))
        print("✅ Saved! Top projects are now Featured and Ranked.")
    elif choice == "c":
        customize_portfolio_project()


def _prompt_bool(label: str, current: bool) -> bool:
    val = input(f"{label} [{ 'y' if current else 'n' }]: ").strip().lower()
    if val in ("y", "yes", "1", "true", "t"): return True
    if val in ("n", "no", "0", "false", "f"): return False
    return current

def _prompt_int(label: str, current: int | None) -> int | None:
    val = input(f"{label} [{'' if current is None else current}]: ").strip()
    if val == "":
        return current
    try:
        return int(val)
    except ValueError:
        print("⚠️  Please enter a valid integer.")
        return current

def _prompt_float(label: str, current: float | None) -> float | None:
    val = input(f"{label} [{'' if current is None else current}]: ").strip()
    if val == "":
        return current
    try:
        return float(val)
    except ValueError:
        print("⚠️  Please enter a valid number.")
        return current

def _prompt_list_csv(label: str, current_list: list[str]) -> list[str]:
    current_str = ", ".join(current_list) if current_list else ""
    val = input(f"{label} (comma-separated) [{current_str}]: ").strip()
    if val == "":
        return current_list
    return [v.strip() for v in val.split(",") if v.strip()]

def customize_portfolio_project():
    print("\n🎯 Customize Portfolio Showcase Project")
    project_id_str = input("Enter project ID: ").strip()
    if not project_id_str.isdigit():
        print("⚠️  Invalid ID.")
        return

    project_id = int(project_id_str)
    project = db_manager.get_project(project_id)

    if not project:
        print("📭 Project not found.")
        return

    print("\nCurrent settings")
    print("─" * 70)
    print(f"ID: {project.id}")
    print(f"Name: {project.name}")
    print(f"Type: {project.project_type}")
    print(f"Featured: {project.is_featured}")
    print(f"Hidden: {project.is_hidden}")
    print(f"User rank: {project.user_rank}")
    print(f"Role: {project.user_role}")
    print(f"Contribution %: {project.user_contribution_percent}")
    print(f"Custom description: {(project.custom_description or '').strip()[:120]}")
    print(f"Skills: {', '.join(project.skills) if project.skills else '—'}")
    print(f"Tags: {', '.join(project.tags) if project.tags else '—'}")
    print("─" * 70)

    print("\nEnter new values (press Enter to keep current)\n")

    # Showcase controls
    new_featured = _prompt_bool("Featured?", bool(project.is_featured))
    new_hidden = _prompt_bool("Hidden?", bool(project.is_hidden))
    new_rank = _prompt_int("User rank (lower = higher priority)", project.user_rank)

    # Role + contribution
    new_role = input(f"Your role [{project.user_role or ''}]: ").strip() or project.user_role
    contrib = _prompt_float("Your contribution % (0-100)", project.user_contribution_percent)
    if contrib is not None:
        contrib = max(0.0, min(100.0, contrib))

    # Descriptions
    cd = input("Custom description (one paragraph) [leave blank to keep]: ").strip()
    new_custom_desc = project.custom_description if cd == "" else cd

    # Skills/tags (portfolio-facing)
    new_skills = _prompt_list_csv("Skills", project.skills or [])
    new_tags = _prompt_list_csv("Tags", project.tags or [])

    # Optional: allow languages/frameworks only for code projects
    new_languages = project.languages
    new_frameworks = project.frameworks
    if (project.project_type or "").lower() == "code":
        new_languages = _prompt_list_csv("Languages", project.languages or [])
        new_frameworks = _prompt_list_csv("Frameworks", project.frameworks or [])

    updates = {
        "is_featured": new_featured,
        "is_hidden": new_hidden,
        "user_rank": new_rank,
        "user_role": new_role,
        "user_contribution_percent": contrib,
        "custom_description": new_custom_desc,
        "skills": new_skills,
        "tags": new_tags,
    }

    if (project.project_type or "").lower() == "code":
        updates["languages"] = new_languages
        updates["frameworks"] = new_frameworks

    db_manager.update_project(project_id, updates)
    print("\n✅ Saved! Your project is updated for portfolio display.\n")


        if success_score is not None:
            if activity_type in ["text", "media"]:
                print(f"   Quality Score:       {success_score * 100:5.1f}%")
                print(f"      (Reflects primarily quantity)")
            else:
                print(f"   Success Score:       {success_score * 100:5.1f}%")
                print(f"      (Reflects size, languages/frameworks, testing coverage, and documentation)")
        if contrib_score is not None:
            print(f"   Contribution Score:  {contrib_score * 100:5.1f}%")


def ai_project_analysis_menu():
    """AI Project Analysis submenu"""
    # Optional AI service consent (not required for basic functionality)
    print("\n" + "="*70)
    ai_consent = request_ai_consent()
    
    if not ai_consent:
        print("\n⚠️  AI features require consent to proceed.")
        print("   Returning to main menu...\n")
        input("Press Enter to continue...")
        return
    
    print("\n✅ AI consent granted. Proceeding with AI features...")
    input("Press Enter to continue...")
    clear_screen()

    while True:
        print_header("AI Project Analysis")
        
        print("Choose an analysis option:\n")

        print("1. Analyze Single Project")
        print("2. Analyze Media Project")
        print("3. Analyze Text Project")
        print("4. Generate AI Summaries for All")
        print("5. Generate Resume Bullet Points")
        print("6. Batch Analyze All Projects")
        print("7. View AI Statistics")
        print("8. Run AI Project Ranking Menu")
        print("9. Return to Main Menu")

        
        choice = input("\nEnter your choice (1-9): ").strip()

    
        if choice == '1':
            analyze_single_project_ai()
        elif choice == '2':
            analyzeMediaProject()
        elif choice == '3':
            analyzeTextProject()        
        elif choice == '4':
            generate_ai_summaries_all()
        elif choice == '5':
            generate_resume_bullets_menu()
        elif choice == '6':
            batch_analyze_all_projects()
        elif choice == '7':
            view_ai_statistics()
        elif choice == '8':
            run_ai_project_ranking_menu()
        elif choice == '9':
            print("\nReturning to main menu...\n")
            break
        else:
            print("❌ Invalid choice. Please try again.")
            input("\nPress Enter to continue...")

def analyze_single_project_ai():
    """Analyze a single project with AI - provides deep technical insights"""
    print_header("AI Project Analysis")
    
    # Get all projects
    projects = db_manager.get_all_projects()
    if not projects:
        print("📭 No projects found in database.")
        print("\nTip: Scan some projects first using options 1-5!")
        input("\nPress Enter to continue...")
        return
    
    # Display available projects
    print(f"Found {len(projects)} project(s):\n")
    print(f"{'ID':<5} {'Name':<40} {'Type':<10}")
    print("-" * 60)
    for project in projects[:20]:  # Show first 20
        name = project.name[:38] + '..' if len(project.name) > 40 else project.name
        print(f"{project.id:<5} {name:<40} {project.project_type:<10}")
    
    if len(projects) > 20:
        print(f"\n... and {len(projects) - 20} more projects")
    
    # Get project ID
    print()
    project_id = input("Enter project ID to analyze (or press Enter to cancel): ").strip()
    
    if not project_id:
        return
    
    if not project_id.isdigit():
        print("❌ Invalid project ID")
        input("\nPress Enter to continue...")
        return
    
    project_id = int(project_id)
    project = db_manager.get_project(project_id)
    
    if not project:
        print(f"❌ Project with ID {project_id} not found")
        input("\nPress Enter to continue...")
        return
    
    # Confirm analysis
    print(f"\n📁 Selected: {project.name}")
    
    # Run AI analysis
    print(f"\n{'='*70}")
    print(f"🤖 Running AI Analysis...")
    print(f"{'='*70}\n")
    print("This may take 10-30 seconds...\n")
    
    try:
        analyzer = AIProjectAnalyzer()
        results = analyzer.analyze_project_complete(project_id)
        
        # Display results
        print(f"{'='*70}")
        print(f"📊 AI Analysis Results")
        print(f"{'='*70}\n")
        
        print(f"📁 Project: {results['project_name']}\n")
        
        # Overview
        if results.get('overview'):
            print("📝 Project Overview:")
            print(f"{results['overview']}\n")
        
        # Technical depth
        if results.get('technical_depth'):
            print("🔬 Technical Analysis:")
            tech_text = results['technical_depth'].get('raw_analysis', 'Not available')
            if tech_text is None or tech_text == 'Not available':
                print("❌ Technical analysis unavailable\n")
            elif len(tech_text) > 800:
                print(f"{tech_text[:800]}...\n")
                print("(Analysis truncated for display)\n")
            else:
                print(f"{tech_text}\n")
        
        # Skills
        if results.get('skills'):
            print(f"💡 Demonstrated Skills ({len(results['skills'])}):")
            for i, skill in enumerate(results['skills'][:10], 1):
                print(f"   {i}. {skill['skill']} ({skill['evidence']})")
                if skill.get('justification'):
                    print(f"      → {skill['justification']}")
            if len(results['skills']) > 10:
                print(f"   ... and {len(results['skills']) - 10} more skills")
            print()
        
        # Statistics
        stats = results.get('cache_stats', {})
        print(f"📊 Analysis Statistics:")
        print(f"   API calls made: {stats.get('analyses_run', 0)}")
        print(f"   Cache hits: {stats.get('cache_hits', 0)}")
        
        # Offer to save
        print(f"\n{'='*70}")
        save = input("💾 Save AI description to database? (yes/no): ").strip().lower()
        if save == 'yes':
            success = analyzer.update_database_with_analysis(project_id, results)
            if success:
                print("✅ AI description saved to database!")
            else:
                print("⚠️  Could not update database")
        
    except Exception as e:
        import traceback
        print(f"\n❌ Error during analysis: {e}")
        print("\n🔍 FULL ERROR DETAILS:")
        traceback.print_exc()
        print("\nPossible issues:")
        print("  • Check your GEMINI_API_KEY is set")
        print("  • Verify you have internet connection")
        print("  • Check API quota limits")
        
    input("\nPress Enter to continue...")

def analyzeMediaProject():
    """Analyze a media project with AI - provides deep technical insights"""
    print_header("AI Media Project Analysis")
    
    # Get all media projects
    projects = db_manager.get_all_projects()
    if not projects:
        print("📭 No projects found in database.")
        print("\nTip: Scan some projects first using options 1-5!")
        input("\nPress Enter to continue...")
        return
    
    # Display available projects
    print(f"Found {len(projects)} project(s):\n")
    print(f"{'ID':<5} {'Name':<40} {'Type':<10}")
    print("-" * 60)
    for project in projects[:20]:  # Show first 20
        name = project.name[:38] + '..' if len(project.name) > 40 else project.name
        print(f"{project.id:<5} {name:<40} {project.project_type:<10}")
    
    if len(projects) > 20:
        print(f"\n... and {len(projects) - 20} more projects")
    
    # Get project ID
    print()
    project_id = input("Enter media project ID to analyze (or press Enter to cancel): ").strip()
    
    if not project_id:
        return
    
    if not project_id.isdigit():
        print("❌ Invalid project ID")
        input("\nPress Enter to continue...")
        return
    
    project_id = int(project_id)
    project = db_manager.get_project(project_id)
    
    if not project or project.project_type != 'visual_media':
        print(f"❌ Media project with ID {project_id} not found")
        input("\nPress Enter to continue...")
        return
    
    # Confirm analysis
    print(f"\n📁 Selected: {project.name}")
    
    # Run AI analysis
    print(f"\n{'='*70}")
    print(f"🤖 Running AI Media Analysis...")
    print(f"{'='*70}\n")
    print("This may take 10-30 seconds...\n")

    project_dict = {
        "project_name": project.name,
        "media_type": project.project_type,
        "details": project.description or project.file_path or ""
    }
    
    try:

        analyzer = AIMediaProjectAnalyzer()
        results = analyzer.analyze_project_complete(project_dict)
        
        # Display results
        print(f"{'='*70}")
        print(f"📊 AI Media Analysis Results")
        print(f"{'='*70}\n")
        print(f"📁 Project: {results['project_name']}\n")

        # Description
        if results.get("ai_description"):
            print("📝 AI Project Description:")
            print(results["ai_description"])
            print()

        # Skills
        if results.get("extracted_skills"):
            skills = results["extracted_skills"]
            print(f"💡 Skills Detected ({len(skills)}):")
            for s in skills[:8]:
                print(f"   • {s}")
            if len(skills) > 8:
                print(f"   ... and {len(skills)-8} more")
            print()
        
        if results.get("contribution_score") is not None:
            print("📈 Estimated Contribution Score:")
            print(f"   {results['contribution_score']}/10\n")

        # Save?
        print(f"{'='*70}")
        save = input("💾 Save this analysis to database? (yes/no): ").strip().lower()
        
        if save == "yes":
            db_manager.update_project(
                project_id,
                {
                    "ai_description": results["ai_description"],
                    "skills": ", ".join(results["extracted_skills"]),
                    "contribution_score": results["contribution_score"]
                }
            )
            print("✅ Saved to database!")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        print("\nPossible issues:")
        print("  • Check your GEMINI_API_KEY is set")
        print("  • Verify you have internet connection")
        print("  • Check API quota limits")
    
    input("\nPress Enter to continue...")

def analyzeTextProject():
    """Analyze a text document project with AI - provides deep insights"""
    print_header("AI Text Document Analysis")
    
    # Get all text document projects
    projects = db_manager.get_all_projects()
    if not projects:
        print("📭 No projects found in database.")
        print("\nTip: Scan some projects first using options 1-5!")
        input("\nPress Enter to continue...")
        return
    
    # Display available projects
    print(f"Found {len(projects)} project(s):\n")
    print(f"{'ID':<5} {'Name':<40} {'Type':<10}")
    print("-" * 60)
    for project in projects[:20]:  # Show first 20
        name = project.name[:38] + '..' if len(project.name) > 40 else project.name
        print(f"{project.id:<5} {name:<40} {project.project_type:<10}")
    
    if len(projects) > 20:
        print(f"\n... and {len(projects) - 20} more projects")
    
    # Get project ID
    print()
    project_id = input("Enter text document project ID to analyze (or press Enter to cancel): ").strip()
    
    if not project_id:
        return
    
    if not project_id.isdigit():
        print("❌ Invalid project ID")
        input("\nPress Enter to continue...")
        return
    
    project_id = int(project_id)
    project = db_manager.get_project(project_id)
    
    if not project or project.project_type != 'text':
        print(f"❌ Text document project with ID {project_id} not found")
        input("\nPress Enter to continue...")
        return
    
    # Confirm analysis
    print(f"\n📁 Selected: {project.name}")
    
    # Run AI analysis
    print(f"\n{'='*70}")
    print(f"🤖 Running AI Text Document Analysis...")
    print(f"{'='*70}\n")
    print("This may take 10-30 seconds...\n")

    project_dict = {
        "project_name": project.name,
        "document_type": project.project_type,
        "details": project.description or project.file_path or ""
    }
    
    try:

        analyzer = AITextProjectAnalyzer()
        results = analyzer.analyze_project_complete(project_dict)
        print(f"{'='*70}")
        print(f"📊 AI Text Project Analysis Results")
        print(f"{'='*70}\n")
        print(f"📁 Project: {results['project_name']}\n")

        if results.get("ai_description"):
            print("📝 AI Description:")
            print(results["ai_description"])
            print()

        # Skills
        if results.get("extracted_skills"):
            print(f"💡 Extracted Skills ({len(results['extracted_skills'])}):")
            for i, skill in enumerate(results["extracted_skills"], 1):
                print(f"   {i}. {skill}")
            print()

        print("📈 Contribution Score:")
        print(f"   {results.get('contribution_score', 'N/A')}")
        print()

        # Cache stats
        print("📊 Analysis Stats:")
        print(f"   Cache hits: {analyzer.cache_hits}")
        print()

        # Save?
        print("="*70)
        save = input("💾 Save AI results to database? (yes/no): ").strip().lower()
        if save == "yes":
            update_data = {
                "ai_description": results.get("ai_description"),
                "skills": ", ".join(results.get("extracted_skills", [])),
                "contribution_score": results.get("contribution_score")
            }
            try:
                db_manager.update_project(project_id, update_data)
                print("✅ AI analysis saved to database!")
            except Exception as e:
                print(f"⚠️ Could not update database: {e}")
    
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        print("\nPossible issues:")
        print("  • Check your GEMINI_API_KEY is set")
        print("  • Verify you have internet connection")
        print("  • Check API quota limits")
    
    input("\nPress Enter to continue...")

def generate_ai_summaries_all():
    """Generate AI-enhanced summaries for all projects"""
    print_header("Generate AI Project Summaries")
    
    # Import needed function
    from src.Analysis.runSummaryFromDb import fetch_projects_for_summary
    
    # Fetch projects
    try:
        projects = fetch_projects_for_summary()
    except Exception as e:
        print(f"❌ Error fetching projects: {e}")
        input("\nPress Enter to continue...")
        return
    
    if not projects:
        print("📭 No projects found in database.")
        print("\nTip: Scan some projects first!")
        input("\nPress Enter to continue...")
        return
    
    print(f"Found {len(projects)} project(s)\n")
    
    # Options
    print("Enhancement Options:")
    print("1. Quick Summary (Top 3 projects, overview only)")
    print("   • Fast")
    print("   • Good for quick portfolio view")
    print()
    print("2. Standard Summary (Top 5 projects, overview + skills)")
    print("   • Moderate")
    print("   • Good for resume building")
    print()
    print("3. Deep Analysis (All projects, complete analysis)")
    print("   • Thorough")
    print("   • Best for comprehensive portfolio")
    print()
    print("4. Cancel")
    
    choice = input("\nChoice (1-4): ").strip()
    
    # Configure based on choice
    if choice == '1':
        top_k, enhance_all, include_tech = 3, False, False
    elif choice == '2':
        top_k, enhance_all, include_tech = 5, False, True
    elif choice == '3':
        top_k, enhance_all, include_tech = min(10, len(projects)), True, True
    elif choice == '4':
        return
    else:
        print("Invalid choice")
        input("\nPress Enter to continue...")
        return
    
    # Confirm
    confirm = input("Proceed with AI enhancement? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Cancelled.")
        input("\nPress Enter to continue...")
        return
    
    # Process
    print(f"\n{'='*70}")
    print("🤖 Generating AI Summaries...")
    print(f"{'='*70}\n")
    print("This may take 30-60 seconds...\n")
    
    try:
        result = summarize_projects_with_ai(
            projects=projects,
            top_k=top_k,
            use_ai=True,
            enhance_all=enhance_all,
            include_technical_depth=include_tech
        )
        
        # Display results
        print(f"\n{'='*70}")
        print("📊 AI Summary Results")
        print(f"{'='*70}\n")
        
        # Portfolio summary
        if 'ai_summary' in result:
            print("🤖 AI-Generated Portfolio Summary:")
            print(f"{result['ai_summary']}\n")
        else:
            print("📝 Standard Summary:")
            print(f"{result['summary']}\n")
        
        # Top projects
        print(f"{'='*70}")
        print(f"🏆 Top {len(result['selected_projects'])} Projects")
        print(f"{'='*70}\n")
        
        for i, proj in enumerate(result['selected_projects'], 1):
            print(f"{i}. {proj['project_name']} (Score: {proj['overall_score']:.3f})")
            print(f"   Skills: {', '.join(proj['skills'][:5])}")
            
            if 'ai_description' in proj:
                print(f"   📝 {proj['ai_description']}")
            
            if 'technical_insights' in proj:
                print(f"   🔬 {proj['technical_insights']}")
            
            print()
        
        print(f"{'='*70}")
        
    except Exception as e:
        print(f"\n❌ Error generating summaries: {e}")
    
    input("\nPress Enter to continue...")

def generate_resume_bullets_menu():
    """Generate professional resume bullets for a project"""
    print_header("Generate Resume Bullets")
    
    # Import needed function
    from src.Analysis.runSummaryFromDb import fetch_projects_for_summary
    from src.Analysis.summarizeProjects import summarize_projects
    
    # Fetch and rank projects
    try:
        projects = fetch_projects_for_summary()
    except Exception as e:
        print(f"❌ Error fetching projects: {e}")
        input("\nPress Enter to continue...")
        return
    
    if not projects:
        print("📭 No projects found in database.")
        input("\nPress Enter to continue...")
        return
    
    # Get top projects
    result = summarize_projects(projects, top_k=min(10, len(projects)))
    
    print(f"Top {len(result['selected_projects'])} Projects:\n")
    for i, proj in enumerate(result['selected_projects'], 1):
        print(f"{i}. {proj['project_name']} (Score: {proj['overall_score']:.3f})")
        print(f"   Skills: {', '.join(proj['skills'][:4])}")
    
    # Get choice
    print()
    choice = input(f"Select project (1-{len(result['selected_projects'])}) or Enter to cancel: ").strip()
    
    if not choice:
        return
    
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(result['selected_projects']):
        print("❌ Invalid choice")
        input("\nPress Enter to continue...")
        return
    
    selected_project = result['selected_projects'][int(choice) - 1]
    
    # Confirm
    print(f"\n📁 Selected: {selected_project['project_name']}")
    confirm = input("Generate resume bullets? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        return
    
    # Generate bullets
    print(f"\n{'='*70}")
    print("🤖 Generating Resume Bullets...")
    print(f"{'='*70}\n")
    
    try:
        bullets = generate_resume_bullets(selected_project, num_bullets=3)
        
        print(f"📋 Resume Bullets for: {selected_project['project_name']}\n")
        print("Copy these to your resume:\n")
        for bullet in bullets:
            print(f"• {bullet}\n")
        
        print(f"{'='*70}")
        
    except Exception as e:
        print(f"❌ Error generating bullets: {e}")
    
    input("\nPress Enter to continue...")

def batch_analyze_all_projects():
    """Batch analyze all projects in database"""
    print_header("Batch Analyze All Projects")
    
    projects = db_manager.get_all_projects()
    if not projects:
        print("📭 No projects in database")
        input("\nPress Enter to continue...")
        return
    
    print(f"Found {len(projects)} projects in database\n")
    
    # Options
    print("Analysis Options:")
    print("1. Overview only (Fast)")
    print("2. Overview + Skills (Moderate)")
    print("3. Complete analysis (Thorough)")
    print("4. Cancel")
    
    choice = input("\nChoice (1-4): ").strip()
    
    # Configure
    if choice == '1':
        analysis_types = ['overview']
    elif choice == '2':
        analysis_types = ['overview', 'skills']
    elif choice == '3':
        analysis_types = ['overview', 'technical_depth', 'skills']
    elif choice == '4':
        return
    else:
        print("Invalid choice")
        input("\nPress Enter to continue...")
        return
    
    confirm = input("\nProceed with batch analysis? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        input("\nPress Enter to continue...")
        return
    
    # Analyze
    print(f"\n{'='*70}")
    print("🤖 Batch Analyzing Projects...")
    print(f"{'='*70}\n")
    print("This may take several minutes...\n")
    
    try:
        analyzer = AIProjectAnalyzer()
        project_ids = [p.id for p in projects]
        results = analyzer.batch_analyze_projects(project_ids, analysis_types)
        
        # Display summary
        print(f"\n{'='*70}")
        print("📊 Batch Analysis Complete")
        print(f"{'='*70}\n")
        print(f"✅ Analyzed {len(results)} projects")
        
        successful = sum(1 for r in results if 'error' not in r)
        failed = len(results) - successful
        
        print(f"   Successful: {successful}")
        if failed > 0:
            print(f"   Failed: {failed}")
        
        # Offer to update database
        print()
        update = input("💾 Update all projects in database with AI descriptions? (yes/no): ").strip().lower()
        if update == 'yes':
            updated = 0
            for result in results:
                if 'error' not in result and 'overview' in result:
                    if analyzer.update_database_with_analysis(result['project_id'], result):
                        updated += 1
            print(f"✅ Updated {updated} projects in database")
        
    except Exception as e:
        print(f"\n❌ Error during batch analysis: {e}")
    
    input("\nPress Enter to continue...")

def view_ai_statistics():
    """View AI analysis statistics and cached analyses"""
    print_header("AI Analysis Statistics")
    
    import json
    from pathlib import Path
    
    # Check cache directory
    cache_dir = Path("data/ai_project_analysis_cache")
    
    if not cache_dir.exists():
        print("📊 No AI analyses have been run yet.\n")
        print("Tip: Run 'Analyze Single Project' to start using AI features!")
        input("\nPress Enter to continue...")
        return
    
    # Get cache files
    cache_files = list(cache_dir.glob("*.json"))
    
    if not cache_files:
        print("📊 No cached analyses found.\n")
        input("\nPress Enter to continue...")
        return
    
    # Analyze cache
    total_analyses = len(cache_files)
    analysis_types = {'overview': 0, 'technical_depth': 0, 'skills': 0}
    project_ids = set()
    
    print(f"📊 AI Analysis Statistics\n")
    print(f"{'='*70}\n")
    
    for cache_file in cache_files:
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            analysis_type = data.get('analysis_type', 'unknown')
            if analysis_type in analysis_types:
                analysis_types[analysis_type] += 1
            
            project_id = data.get('project_id')
            if project_id:
                project_ids.add(project_id)
        except:
            pass
    
    print(f"Total cached analyses: {total_analyses}")
    print(f"Unique projects analyzed: {len(project_ids)}")
    print()
    
    print("Analysis breakdown:")
    print(f"  • Overviews: {analysis_types['overview']}")
    print(f"  • Technical depth: {analysis_types['technical_depth']}")
    print(f"  • Skills: {analysis_types['skills']}")
    print()
    
    # Show recent analyses
    print("Recent analyses:")
    recent = sorted(cache_files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]
    
    for cache_file in recent:
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            project_id = data.get('project_id', 'unknown')
            analysis_type = data.get('analysis_type', 'unknown')
            timestamp = data.get('timestamp', 'unknown')
            
            # Get project name
            try:
                project = db_manager.get_project(int(project_id))
                project_name = project.name if project else f"Project {project_id}"
            except:
                project_name = f"Project {project_id}"
            
            print(f"  • {project_name} - {analysis_type}")
            if timestamp != 'unknown':
                print(f"    {timestamp[:19]}")
        except:
            pass
    
    print(f"\n{'='*70}")
    
    # Option to clear cache
    print()
    clear = input("🗑️  Clear all cached analyses? (yes/no): ").strip().lower()
    if clear == 'yes':
        import shutil
        confirm = input("⚠️  This cannot be undone. Confirm? (yes/no): ").strip().lower()
        if confirm == 'yes':
            try:
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(parents=True, exist_ok=True)
                print("✅ Cache cleared!")
            except Exception as e:
                print(f"❌ Error clearing cache: {e}")
    
    input("\nPress Enter to continue...")

def run_ai_project_ranking_menu():
    print("\n=== 🤖 AI Project Ranking ===\n")

    # Fetch all projects from DB
    projects = fetch_projects_for_summary()

    if not projects:
        print("No projects found in database.")
        input("\nPress Enter to continue...")
        return

    # Ask user for skills to prioritize
    skills_input = input("Enter skills to prioritize (comma-separated), or press Enter for none:\n").strip()
    target_skills = [s.strip() for s in skills_input.split(",")] if skills_input else None

    # Ask how many top projects they want
    try:
        top_k = int(input("\nHow many top projects do you want ranked? (default = 3): ").strip() or 3)
    except ValueError:
        top_k = 3

    # Create the ranker
    ranker = AIProjectRanker()

    # Run ranking
    result = ranker.rank(projects, target_skills=target_skills, top_k=top_k)

    # Display results
    print("\n=== 🏆 Top Ranked Projects ===\n")
    for i, proj in enumerate(result["selected"], 1):
        print(f"{i}. {proj['project_name']}  (Score: {proj['_rank_score']:.3f})")
        if proj.get("skills"):
            print(f"   Skills: {', '.join(proj['skills'])}")
        print()

    print("Done.")
    input("\nPress Enter to continue...")

def run_importance_test():
    print("=== Running Importance Score Test ===")

    # Step 1 — assign importance scores to all projects
    assign_importance_scores()
    print("Assigned importance scores.\n")

    # Step 2 — fetch ranked list
    ranked_projects = get_ranked_projects()

    # Step 3 — display results
    print("=== Ranked Projects ===")
    i=1
    for p in ranked_projects:
        print(f"[{i}] {p.name} → {p.importance_score}")
        i += 1
    i=0
    print("\nDone.")

def run_project_ranking_test():
    """Rank projects by creation/update date and display (DB-backed)"""
    print("=== Project Timeline ===\n")
    print(get_ranked_timeline_from_db())



def run_code_efficiency_test():
    """
    Prompt the user for a file or directory path and analyze code efficiency.
    Prints results for each code file or folder summary.
    """
    path_input = input("Enter the path to a code file or directory: ").strip()
    target = Path(path_input)

    if not target.exists():
        print(f"Error: '{path_input}' does not exist.")
        return

    # Case 1: single file
    if target.is_file():
        try:
            code = target.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Could not read '{target}': {e}")
            return

        result = grade_efficiency(code, str(target))
        print(f"\n=== Efficiency Analysis for {target} ===")
        print(f"Time Score: {result['time_score']}")
        print(f"Space Score: {result['space_score']}")
        print(f"Overall Efficiency Score: {result['efficiency_score']}")
        print(f"Max Loop Depth: {result['max_loop_depth']}")
        print(f"Total Loops: {result['total_loops']}")
        if result.get("notes"):
            print("Notes:")
            for note in result["notes"]:
                print(f"- {note}")

    # Case 2: folder
    elif target.is_dir():
        summary = grade_folder(str(target))
        print(f"\n=== Folder Efficiency Summary for {target} ===")
        for k, v in summary.items():
            if k != "all_notes":
                print(f"{k}: {v}")

    else:
        print(f"Error: '{path_input}' is neither a file nor a directory.")


# ============================================
# DELETION MANAGEMENT FUNCTIONS
# ============================================

def deletion_management_menu():
    """Deletion management submenu"""
    if not DELETION_FEATURES_AVAILABLE:
        print("\n❌ Deletion features are not available.")
        print("   Please ensure deletion_manager.py and enhanced_deletion.py are in src/")
        input("\nPress Enter to continue...")
        return
    
    while True:
        clear_screen()
        print_header("Deletion Management")
        
        print("Choose an option:\n")
        print("1. Delete Project (Safe - protects shared files)")
        print("2. Delete AI Insights (Single Project)")
        print("3. Delete ALL AI Insights")
        print("4. Bulk Delete Projects")
        print("5. View Shared Files Report")
        print("6. View Cache Statistics")
        print("7. Return to Main Menu")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            delete_project_enhanced()
        elif choice == '2':
            delete_single_project_insights()
        elif choice == '3':
            delete_all_insights_confirm()
        elif choice == '4':
            bulk_delete_projects()
        elif choice == '5':
            view_shared_files_report()
        elif choice == '6':
            view_deletion_cache_stats()
        elif choice == '7':
            break
        else:
            print("❌ Invalid choice. Please try again.")
            input("\nPress Enter to continue...")

def delete_single_project_insights():
    """Delete AI insights for a single project"""
    print_header("Delete AI Insights (Single Project)")
    
    # Get all projects
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

def delete_all_insights_confirm():
    """Delete ALL AI insights with confirmation"""
    print_header("Delete ALL AI Insights")
    
    print("⚠️⚠️⚠️  WARNING  ⚠️⚠️⚠️")
    print("\nThis will delete ALL AI-generated insights from:")
    print("  • Project descriptions in database")
    print("  • All cached AI analyses")
    print("\nThis action affects ALL projects in the system.")
    
    confirm = input("\nAre you absolutely sure? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("\nDeletion cancelled")
        input("\nPress Enter to continue...")
        return
    
    # Double confirmation
    confirm2 = input("⚠️  Type 'DELETE ALL' to confirm: ").strip()
    
    if confirm2 != 'DELETE ALL':
        print("\nDeletion cancelled")
        input("\nPress Enter to continue...")
        return
    
    print("\n🔄 Deleting all AI insights...")
    
    manager = DeletionManager()
    results = manager.delete_all_ai_insights()
    
    print(f"\n✅ Deletion complete!")
    print(f"  Projects updated: {results['projects_updated']}")
    print(f"  Cache files deleted: {results['cache_files_deleted']}")
    
    if results['errors']:
        print(f"\n⚠️  Errors encountered ({len(results['errors'])}):")
        for error in results['errors'][:5]:
            print(f"  • {error}")
        if len(results['errors']) > 5:
            print(f"  ... and {len(results['errors']) - 5} more")
    
    input("\nPress Enter to continue...")

def view_deletion_cache_stats():
    """View cache statistics"""
    print_header("Cache Statistics")
    
    manager = DeletionManager()
    stats = manager.get_cache_statistics()
    
    print(f"📊 Cache Information:")
    print(f"  Total cache files: {stats['total_cache_files']}")
    print(f"  Total cache size: {stats['total_cache_size_bytes'] / 1024:.2f} KB")
    
    if stats['cache_by_type']:
        print(f"\n📋 Cache by type:")
        for cache_type, count in stats['cache_by_type'].items():
            print(f"  • {cache_type}: {count}")
    
    if stats['oldest_cache']:
        print(f"\n📅 Cache age:")
        print(f"  Oldest: {stats['oldest_cache']}")
        print(f"  Newest: {stats['newest_cache']}")
    
    # Option to clear cache
    if stats['total_cache_files'] > 0:
        print()
        clear = input("🗑️  Clear all cache? (yes/no): ").strip().lower()
        if clear == 'yes':
            confirm = input("⚠️  This cannot be undone. Confirm? (yes/no): ").strip().lower()
            if confirm == 'yes':
                results = manager.delete_all_ai_insights()
                print(f"\n✅ Deleted {results['cache_files_deleted']} cache file(s)")
    
    input("\nPress Enter to continue...")


def handle_resume_items():
    """Handle resume items menu option"""
    print_header("Resume Items")
    
    if not RESUME_FEATURES_AVAILABLE:
        print("❌ Resume features are not available.")
        input("\nPress Enter to continue...")
        return
    
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("📭 No projects found in database.")
        print("\n⚠️  You need to analyze a project first before generating resume items.")
        print("   Please go back to the main menu and use options 1-5 to analyze a project.")
        input("\nPress Enter to continue...")
        return
    
    print("Has the project you want resume items for already been analyzed?\n")
    print("1. Yes - Take me to the Resume menu")
    print("2. No  - I need to analyze it first")
    print("3. Cancel - Return to Main Menu")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == '1':
        print(f"\n✓ Found {len(projects)} analyzed project(s) in database:")
        print("-" * 50)
        for i, p in enumerate(projects[:10], 1):
            project_type = p.project_type or "unknown"
            print(f"   {i}. {p.name} ({project_type})")
        if len(projects) > 10:
            print(f"   ... and {len(projects) - 10} more")
        print()
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

def handle_thumbnail_upload():
    """Handle uploading a thumbnail for an existing project"""
    print_header("Upload Thumbnail for Project")
    
    # Get all projects from database
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("📭 No projects found in database.")
        print("\n⚠️  You need to upload a project first before adding a thumbnail.")
        input("\nPress Enter to continue...")
        return
    
    # Display projects
    print("Available projects:\n")
    print("-" * 70)
    for i, project in enumerate(projects, 1):
        project_type = project.project_type or "unknown"
        has_thumbnail = "✓" if project.thumbnail_path else "✗"
        print(f"{i}. {project.name} ({project_type}) [Thumbnail: {has_thumbnail}]")
    print("-" * 70)
    
    # Get project selection
    try:
        choice = input(f"\nSelect project (1-{len(projects)}) or 'cancel' to go back: ").strip()
        if choice.lower() == 'cancel':
            print("Cancelled.")
            return
        
        project_index = int(choice) - 1
        if project_index < 0 or project_index >= len(projects):
            print("❌ Invalid project number.")
            return
        
        selected_project = projects[project_index]
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        return
    
    # Get thumbnail file path
    thumbnail_path = get_path_input("\nEnter the path to the thumbnail image: ")
    if not thumbnail_path:
        print("Cancelled.")
        return
    
    # Validate it's an image file
    valid_image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}
    file_ext = os.path.splitext(thumbnail_path)[1].lower()
    
    if file_ext not in valid_image_extensions:
        print(f"❌ Invalid image format. Supported formats: {', '.join(valid_image_extensions)}")
        return
    
    # Update project with thumbnail path
    update_data = {'thumbnail_path': thumbnail_path}
    success = db_manager.update_project(selected_project.id, update_data)
    
    if success:
        print(f"\n✅ Thumbnail successfully uploaded for project: {selected_project.name}")
        print(f"   Thumbnail path: {thumbnail_path}")
    else:
        print(f"\n❌ Failed to update project with thumbnail.")
    
    input("\nPress Enter to continue...")

def project_upload_menu():
    ...
    options = {
        '1': handle_coding_project,
        '2': handle_visual_project,
        '3': handle_document,
        '4': handle_zip_archive,
        '5': handle_auto_detect,
        '6': handle_add_files_to_project,     
        '7': handle_incremental_zip_upload,
        '8': handle_thumbnail_upload,
    }
    
    print("UPLOAD NEW PROJECT:")
    print("  1. Coding project")
    print("  2. Visual/media project")
    print("  3. Text document")
    print("  4. ZIP archive")
    print("  5. Auto-detect type")
    print("\nADD TO EXISTING PROJECT:")
    print("  6. Add individual file(s)")       
    print("  7. Add ZIP archive")
    print("  8. Upload thumbnail for a stored project")
    print("\n  9. Return to Main Menu")
    print("="*70)

    choice = input("\nEnter your choice (1-9): ").strip()
    if choice == '9':
        print("\nReturning to main menu...")
        return

    if choice in options:
        options[choice]()
    else:
        print("❌ Invalid choice. Please enter a number 1-8.")
        if choice in options:
            options[choice]()
        else:
            print("Invalid choice. Try again.")

def assign_and_view_roles():
    from src.Analysis.roleAttribution import test_role_attribution, lookup_roles

    while True:
        clear_screen()
        print("\n--- Assign / View Roles Menu ---")
        print("1. Assign Role by Project")
        print("2. View Role by Project")
        print("3. Back")

        sub = input("Select an option (1-3): ").strip()

        if sub == '3':
            return  # go back to View & Analysis menu
        elif sub == '1':
            clear_screen()
            test_role_attribution()
        elif sub == '2':
            clear_screen()
            lookup_roles()
        else:
            print("Invalid choice. Try again.")

        print("❌ Invalid choice. Please enter a number 1-9.")

def view_and_analysis_menu():
    clear_screen()
    options = {
        '1': view_all_projects,
        '2': generate_summary,
        '3': view_saved_showcases,
        '4': sort_and_score_projects_menu,
        '5': assign_and_view_roles,
        '6': evidence_main_menu if EVIDENCE_FEATURES_AVAILABLE else None
    }

    while True:
        print("\nView & Analysis Menu:")
        print("1. View all projects")
        print("2. Generate Portfolio")
        print("3. View saved showcases")
        print("4. Sort / score projects")
        print("5. Assign and View Roles")
        if EVIDENCE_FEATURES_AVAILABLE:
            print("7. Manage Project Evidence")
            print("8. Return to Main Menu")
            options['7'] = evidence_main_menu
            exit_choice = '8'
            max_choice = 8
        else:
            print("7. Return to Main Menu")
            exit_choice = '7'
            max_choice = 7

        choice = input(f"Enter your choice (1-{max_choice}): ").strip()

        if choice == exit_choice:
            print("Exiting view & analysis menu.")
            return

        if choice in options and options[choice] is not None:
            options[choice]()
        else:
            print("Invalid choice. Try again.")


def sort_and_score_projects_menu():
    clear_screen()
    while True:
        print("\n--- Sort / Score Projects Menu ---")
        print("1. Sort projects by date")
        print("2. Compute / grade importance scores")
        print("3. Back")

        sub = input("Select an option (1-3): ").strip()

        if sub == '3':
            return  # go back to View & Analysis menu
        elif sub == '1':
            run_project_ranking_test()
        elif sub == '2':
            run_importance_test()
        else:
            print("Invalid choice. Try again.")

def settings_menu():
    clear_screen()
    while True:
        print("1. View current configuration")
        print("2. Privacy & scanning settings")
        print("3. Analysis feature preferences")
        print("4. Consent settings (file + AI)")
        print("5. Quick setup wizard (rerun)")
        print("6. Reset configuration to defaults")
        print("7. Return to Main Menu")

        choice = input("\nChoose an option (1-7): ").strip()

        if choice == "1":
            show_current_configuration()

        elif choice == "2":
            configure_privacy_settings()

        elif choice == "3":
            configure_analysis_preferences()

        elif choice == "4":
            print("\n" + "-" * 70)
            print("CONSENT SETTINGS")
            print("-" * 70)
            print("1) Review / confirm file access consent")
            print("2) Review / confirm AI consent")
            print("3) Back")
            sub = input("\nChoose an option (1-3): ").strip()

            if sub == "1":
                request_and_store_basic_consent()
            elif sub == "2":
                request_and_store_ai_consent()
            # else back

        elif choice == "5":
            quick_setup_wizard()

        elif choice == "6":
            confirm = input(
                "\n⚠️  This will erase your saved settings and consents. Type 'reset' to confirm: "
            ).strip().lower()
            if confirm == "reset":
                ConfigManager.reset_to_defaults()
                print("✓ Configuration reset to defaults.")
            else:
                print("Cancelled.")

        elif choice == "7":
            return

        else:
            print("Invalid choice. Please enter a number 1-7.")

def ai_menu():
    clear_screen()
    while True:
        print("\nAI Menu:")
        print("1. AI project analysis")
        print("2. Delete AI insights for a project")
        print("3. Return to main menu")

        choice = input("Enter your choice (1-3): ").strip()

        if choice == '3':
            print("Exiting AI menu.")
            return

        elif choice == '1':
            ai_project_analysis_menu()

        elif choice == '2':
            manager = DeletionManager()
            pid = input("Enter project ID: ").strip()

            if pid.isdigit():
                ok = manager.delete_ai_insights_for_project(int(pid))
                print("AI insights deleted." if ok else "Invalid project ID.")
            else:
                print("Invalid ID.")

        else:
            print("Invalid choice. Try again.")


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
            project_upload_menu()
        elif choice == '2':
            view_and_analysis_menu()
        elif choice == '3':
            handle_resume_items()
        elif choice == '4':
            ai_menu()
        elif choice == '5':
            deletion_management_menu()
        elif choice == '6':
            settings_menu()
        elif choice == '7':
            print("Goodbye!")
            sys.exit(0)
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
