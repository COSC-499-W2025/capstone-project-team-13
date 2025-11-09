"""
Digital Artifact Mining Software - Main Entry Point
Integrates all components for a complete workflow

"""
import sys
import os
from pathlib import Path
import re

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
from src.Analysis.visualMediaAnalyzer import analyze_visual_project
from src.Extraction.keywordExtractorText import extract_keywords_with_scores
from src.Databases.database import db_manager
from src.Analysis.summarizeProjects import summarize_projects
from src.Analysis.runSummaryFromDb import fetch_projects_for_summary
from src.Analysis.projectcollabtype import identify_project_type

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
    Check if a project is collaborative
    
    TODO: Implement proper collaboration detection using:
    - Git history analysis (git log --format=%aN)
    - File metadata analysis (@author tags, file ownership)
    - Database contributor records
    
    For now, returns 'Unknown' as placeholder.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        str: 'Individual Project', 'Collaborative Project', or 'Unknown'
    """
    # Placeholder - check database if project already exists
    existing = db_manager.get_project_by_path(str(project_path))
    if existing:
        contributors = db_manager.get_contributors_for_project(existing.id)
        if len(contributors) > 1:
            return 'Collaborative Project'
        elif len(contributors) == 1:
            return 'Individual Project'
    
    return 'Unknown (no contributor data found)'

def get_user_choice():
    """Get user's choice for what to analyze"""
    print_header("Digital Artifact Mining Software")
    print("What would you like to analyze?\n")
    print("1. Coding Project (folder containing code files)")
    print("2. Visual/Media Project (folder containing design/media files)")
    print("3. Single Document (text file for keyword extraction)")
    print("4. ZIP Archive (extract and analyze)")
    print("5. Any Folder (auto-detect type)")
    print("6. View All Projects in Database")
    print("7. Generate Project Summary")
    print("8. Exit")
    
    choice = input("\nEnter your choice (1-8): ").strip()
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
        print(f"   Scanned: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    if project.project_type == 'code':
        print(f"\n📈 Code Metrics:")
        print(f"   Lines of Code: {project.lines_of_code:,}")
        print(f"   File Count: {project.file_count}")
        print(f"   Total Size: {project.total_size_bytes / (1024*1024):.2f} MB")
        
        if project.date_created:
            print(f"   First Created: {project.date_created.strftime('%Y-%m-%d')}")
        if project.date_modified:
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
    
    print(f"\n{'='*70}")

def handle_coding_project():
    """Handle scanning a coding project"""
    print_header("Scan Coding Project")
    
    path = get_path_input("Enter path to coding project folder: ")
    if not path:
        return
    
    if not os.path.isdir(path):
        print("❌ Path must be a directory (folder)")
        return
    
    # Normalize path to absolute for consistent comparison
    path = os.path.abspath(path)
    
    # Check if already exists BEFORE scanning
    existing = db_manager.get_project_by_path(path)
    if existing:
        print(f"\n⚠️  This project already exists in the database!")
        print(f"   Project: {existing.name}")
        print(f"   Database ID: {existing.id}") 
        if existing.date_scanned:
            from datetime import timezone
            local_time = existing.date_scanned.replace(tzinfo=timezone.utc).astimezone()
            print(f"   Last scanned: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        rescan = input("\n   Would you like to re-scan and update? (yes/no): ").strip().lower()
        if rescan != 'yes':
            print("\n✅ Using existing project data.")
            display_project_details(existing)
            return
        
        # Delete old project to re-scan
        print("\n⏳ Deleting old data and re-scanning...")
        db_manager.delete_project(existing.id)
    
    # Check if collaborative
    print("\n🔍 Analyzing collaboration type...")
    collab_type = check_if_collaborative(path)
    
    if collab_type == 'Collaborative Project':
        print(f"🤝 Collaborative Project Detected")
    elif collab_type == 'Individual Project':
        print(f"👤 Individual Project Detected")
    else:
        print(f"❓ Collaboration Type: Unknown")
    
    # The scanner handles all the analysis and display internally
    project_id = scan_coding_project(path)
    
    if not project_id:
        print("\n❌ Failed to scan project or no code files found.")
        return
    
    # Update collaboration type if detected
    if collab_type != 'Unknown (no contributor data found)':
        db_manager.update_project(project_id, {'collaboration_type': collab_type})

def handle_visual_project():
    """Handle analyzing a visual/media project"""
    print_header("Analyze Visual/Media Project")
    
    path = get_path_input("Enter path to media project folder: ")
    if not path:
        return
    
    if not os.path.isdir(path):
        print("❌ Path must be a directory (folder)")
        return
    
    # Normalize path
    path = os.path.abspath(path)
    
    # Check if already exists
    existing = db_manager.get_project_by_path(path)
    if existing and existing.project_type == 'media':
        print(f"\n⚠️  This media project already exists in database (ID: {existing.id})")
        display_project_details(existing)
        return
    
    print("\n⏳ Analyzing visual project...")
    
    try:
        result = analyze_visual_project(path)
        
        print(f"\n✅ Analysis Complete!")
        print(f"\n📊 Visual Project Analysis:")
        print(f"   Type: {result['type']}")
        print(f"   Files Found: {result['num_files']}")
        
        if result['software_used']:
            print(f"\n   Software Detected:")
            for software in result['software_used']:
                print(f"      • {software}")
        
        if result['skills_detected']:
            print(f"\n   Skills Detected:")
            for skill in result['skills_detected']:
                print(f"      • {skill}")
        
        # Optionally store in database
        if result['num_files'] > 0:
            store = input("\n💾 Would you like to store this in the database? (yes/no): ").strip().lower()
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
                print(f"✅ Stored in database with ID: {project.id}")
    
    except Exception as e:
        print(f"\n❌ Error analyzing project: {e}")

def handle_document():
    """Handle single document keyword extraction"""
    print_header("Extract Keywords from Document")
    
    path = get_path_input("Enter path to text document: ")
    if not path:
        return
    
    if not os.path.isfile(path):
        print("❌ Path must be a file")
        return
    
    print("\n⏳ Extracting keywords...")
    
    try:
        # Validate format
        check_file_format(path)
        
        # Parse file
        parsed = parse_file(path)
        
        # Extract keywords from content
        if parsed.get('content'):
            content = parsed['content']
            if isinstance(content, dict):
                content = str(content)
            
            keywords = extract_keywords_with_scores(content)
            
            print(f"\n✅ Keyword Extraction Complete!")
            print(f"\n📊 Document Analysis:")
            print(f"   File: {os.path.basename(path)}")
            print(f"   Type: {parsed['type']}")
            
            if keywords:
                print(f"\n   Top Keywords (score, phrase):")
                for score, phrase in keywords[:15]:
                    print(f"      {score:5.2f}  →  {phrase}")
            else:
                print("\n   No keywords extracted.")
        else:
            print("❌ Could not extract text content from file.")
    
    except (InvalidFileFormatError, FileParseError) as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

def handle_zip_archive():
    """Handle ZIP archive extraction and analysis"""
    print_header("Extract and Analyze ZIP Archive")
    
    path = get_path_input("Enter path to ZIP file: ")
    if not path:
        return
    
    if not path.lower().endswith('.zip'):
        print("❌ File must have .zip extension")
        return
    
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
        
        # Automatically detect project type
        print("\n🔍 Detecting project type...")
        detection_result = detect_project_type(extract_path)
        project_type = detection_result['type']
        
        print(f"✅ {detection_result['details']}")
        
        # Check if collaborative
        collab_type = check_if_collaborative(extract_path)
        if collab_type == 'Collaborative Project':
            print("🤝 Collaborative project detected")
        elif collab_type == 'Individual Project':
            print("👤 Individual project detected")
        
        # Handle based on project type
        if project_type == 'code':
            print("\n⏳ Scanning as coding project...")
            project_id = scan_coding_project(extract_path)
            if project_id and collab_type != 'Unknown (no contributor data found)':
                db_manager.update_project(project_id, {'collaboration_type': collab_type})
                
        elif project_type == 'media':
            print("\n⏳ Analyzing as visual project...")
            result = analyze_visual_project(extract_path)
            
            print(f"\n✅ Analysis Complete!")
            print(f"   Files Found: {result['num_files']}")
            if result['software_used']:
                print(f"   Software: {', '.join(result['software_used'])}")
            if result['skills_detected']:
                print(f"   Skills: {', '.join(result['skills_detected'])}")
            
            # Ask if they want to store it
            if result['num_files'] > 0:
                store = input("\n💾 Store in database? (yes/no): ").strip().lower()
                if store == 'yes':
                    project_data = {
                        'name': os.path.basename(extract_path),
                        'file_path': extract_path,
                        'file_count': result['num_files'],
                        'project_type': 'media',
                        'skills': result['skills_detected'],
                        'tags': result['software_used']
                    }
                    project = db_manager.create_project(project_data)
                    print(f"✅ Stored with ID: {project.id}")
                
        elif project_type == 'mixed':
            print("\n📦 Mixed project detected - processing both code and media files...")
            
            # Scan code files
            print("\n⏳ Analyzing code files...")
            code_project_id = scan_coding_project(extract_path)
            if code_project_id:
                if collab_type != 'Unknown (no contributor data found)':
                    db_manager.update_project(code_project_id, {'collaboration_type': collab_type})
                print(f"✅ Code analysis complete (Project ID: {code_project_id})")
            
            # Analyze media files
            print("\n⏳ Analyzing media files...")
            media_result = analyze_visual_project(extract_path)
            if media_result['num_files'] > 0:
                print(f"✅ Found {media_result['num_files']} media files")
                print(f"   Software: {', '.join(media_result['software_used']) if media_result['software_used'] else 'None detected'}")
                
                # Optionally store media analysis separately
                store_media = input("\n💾 Store media analysis separately? (yes/no): ").strip().lower()
                if store_media == 'yes':
                    project_data = {
                        'name': f"{os.path.basename(extract_path)} (Media)",
                        'file_path': extract_path,
                        'file_count': media_result['num_files'],
                        'project_type': 'media',
                        'skills': media_result['skills_detected'],
                        'tags': media_result['software_used']
                    }
                    media_project = db_manager.create_project(project_data)
                    print(f"✅ Media analysis stored with ID: {media_project.id}")
        else:
            print("\n⚠️  Could not determine project type automatically.")
            print("   The folder may not contain recognizable code or media files.")
            
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
            if project_id and collab_type != 'Unknown (no contributor data found)':
                db_manager.update_project(project_id, {'collaboration_type': collab_type})
                
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
                    
    elif project_type == 'mixed':
        print("\n📦 This folder contains both code and media files.")
        choice = input("Analyze as: (1) Code project, (2) Media project, (3) Both: ").strip()
        
        if choice in ['1', '3']:
            print("\n⏳ Analyzing code files...")
            project_id = scan_coding_project(path)
            if project_id and collab_type != 'Unknown (no contributor data found)':
                db_manager.update_project(project_id, {'collaboration_type': collab_type})
        
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

def generate_summary():
    """Generate summary of all projects using existing module"""
    print_header("Generate Project Summary")
    
    # Use existing fetch function instead of duplicating logic
    project_dicts = fetch_projects_for_summary()
    
    if not project_dicts:
        print("📭 No projects found in database.")
        print("\nTip: Scan some projects first!")
        return
    
    print(f"Found {len(project_dicts)} project(s). Generating summary...\n")
    
    # Generate summary
    result = summarize_projects(project_dicts, top_k=min(5, len(project_dicts)))
    
    print("="*70)
    print("  📊 PROJECT PORTFOLIO SUMMARY")
    print("="*70)
    print(f"\n{result['summary']}\n")
    
    print(f"{'='*70}")
    print(f"  🏆 Top {len(result['selected_projects'])} Projects")
    print(f"{'='*70}\n")
    
    for i, proj in enumerate(result['selected_projects'], 1):
        print(f"{i}. {proj['project_name']}")
        print(f"   Overall Score: {proj['overall_score']:.3f}")
        print(f"   Skills: {', '.join(proj['skills'][:5])}")
        if len(proj['skills']) > 5:
            print(f"           {', '.join(proj['skills'][5:])}")
        print()
    
    print(f"{'='*70}")
    print(f"  🎯 All Unique Skills ({len(result['unique_skills'])} total)")
    print(f"{'='*70}")
    print(f"{', '.join(result['unique_skills'])}\n")

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
    
    # Step 2: Optional AI service consent (not required for basic functionality)
    print("\n" + "="*70)
    ai_consent = request_ai_consent()
    
    if not ai_consent:
        print("\n⚠️  Note: AI features disabled. Basic analysis will still work.")
        input("Press Enter to continue...")
    else:
        print("\n✅ AI features enabled.")
        input("Press Enter to continue...")
    
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
            print("\n👋 Thank you for using Digital Artifact Mining Software!")
            print("   All your data has been saved to the database.\n")
            sys.exit(0)
        else:
            print("\n❌ Invalid choice. Please enter 1-8.")
        
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