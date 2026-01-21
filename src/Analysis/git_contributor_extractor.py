"""
Git Contributor Extractor
Extracts contributor information from Git repositories and populates the contributors table
Uses direct git commands for accuracy matching GitHub Insights
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import re

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')
)
sys.path.insert(0, PROJECT_ROOT)

from src.Databases.database import db_manager, Project


def run_git_command(repo_path: str, command: List[str]) -> Optional[str]:
    """
    Execute a git command in the repository directory.
    
    Args:
        repo_path: Path to the git repository
        command: Git command as list of arguments
        
    Returns:
        Command output as string, or None if error
    """
    try:
        result = subprocess.run(
            ['git'] + command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Git command error: {e.stderr}")
        return None
    except Exception as e:
        print(f"Error running git command: {e}")
        return None


def is_git_repository(path: str) -> bool:
    """Check if path is a git repository"""
    result = run_git_command(path, ['rev-parse', '--git-dir'])
    return result is not None


def extract_git_contributors(project_path: str, since_date: Optional[str] = None, until_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract contributor information from a Git repository using direct git commands.
    This approach better matches GitHub Insights statistics.
    
    Args:
        project_path: Path to the Git repository
        since_date: Optional start date (format: YYYY-MM-DD)
        until_date: Optional end date (format: YYYY-MM-DD)
        
    Returns:
        List of contributor dictionaries with name, email, commits, and line changes
    """
    if not is_git_repository(project_path):
        print(f"Not a Git repository: {project_path}")
        return []
    
    print(f"\nAnalyzing Git repository: {project_path}")
    if since_date or until_date:
        date_range = f" (from {since_date or 'start'} to {until_date or 'now'})"
        print(f"Date range: {date_range}")
    print("Extracting contributor data using git commands...")
    
    # Track contributors by username (GitHub username when available, otherwise name)
    contributors = defaultdict(lambda: {
        'name': None,
        'email': None,
        'commit_count': 0,
        'lines_added': 0,
        'lines_deleted': 0
    })
    
    # Build date range arguments
    date_args = []
    if since_date:
        date_args.extend(['--since', since_date])
    if until_date:
        # Use --before to be inclusive of the end date (GitHub behavior)
        # Add one day to include the full end date
        from datetime import datetime, timedelta
        try:
            end_date = datetime.strptime(until_date, '%Y-%m-%d')
            next_day = (end_date + timedelta(days=1)).strftime('%Y-%m-%d')
            date_args.extend(['--before', next_day])
        except ValueError:
            # If date parsing fails, use as-is
            date_args.extend(['--before', until_date])
    
    # Method 1: Get commit counts using git shortlog
    # This matches GitHub's commit counting methodology (using default branch)
    shortlog_cmd = ['shortlog', '-sne', 'HEAD', '--no-merges'] + date_args
    shortlog_output = run_git_command(project_path, shortlog_cmd)
    
    if shortlog_output:
        for line in shortlog_output.strip().split('\n'):
            if not line.strip():
                continue
            
            # Parse: "    5  John Doe <john@example.com>"
            match = re.match(r'\s*(\d+)\s+(.+?)\s+<(.+?)>', line)
            if match:
                commits = int(match.group(1))
                name = match.group(2).strip()
                email = match.group(3).strip()
                
                # Extract GitHub username from noreply email if available
                # Format: 123456+username@users.noreply.github.com
                github_match = re.search(r'\d+\+([^@]+)@users\.noreply\.github\.com', email)
                contributor_key = github_match.group(1) if github_match else email
                
                contributors[contributor_key]['name'] = name
                contributors[contributor_key]['email'] = email
                contributors[contributor_key]['commit_count'] = commits
    
    # Method 2: Get line changes using git log --numstat
    # This provides accurate line-by-line changes per author
    log_cmd = ['log', 'HEAD', '--no-merges', '--numstat', '--pretty=format:COMMIT:%ae'] + date_args
    log_output = run_git_command(project_path, log_cmd)
    
    if log_output:
        current_author = None
        for line in log_output.split('\n'):
            line = line.strip()
            
            if line.startswith('COMMIT:'):
                email = line.split(':', 1)[1]
                # Convert email to same key format used in shortlog
                github_match = re.search(r'\d+\+([^@]+)@users\.noreply\.github\.com', email)
                current_author = github_match.group(1) if github_match else email
            elif line and current_author and '\t' in line:
                # Parse numstat line: "additions\tdeletions\tfilename"
                parts = line.split('\t')
                if len(parts) >= 3:
                    try:
                        # Handle binary files (marked as '-')
                        additions = int(parts[0]) if parts[0] != '-' else 0
                        deletions = int(parts[1]) if parts[1] != '-' else 0
                        
                        if current_author in contributors:
                            contributors[current_author]['lines_added'] += additions
                            contributors[current_author]['lines_deleted'] += deletions
                    except (ValueError, IndexError):
                        continue
    
    # Convert to list
    contributor_list = list(contributors.values())
    
    # Filter out any invalid entries
    contributor_list = [c for c in contributor_list if c['name'] and c['email']]
    
    if contributor_list:
        print(f"  Found {len(contributor_list)} unique contributors")
        
        # Calculate contribution percentages based on total lines changed
        total_lines = sum(c['lines_added'] + c['lines_deleted'] for c in contributor_list)
        
        if total_lines > 0:
            for contrib in contributor_list:
                lines_changed = contrib['lines_added'] + contrib['lines_deleted']
                contrib['contribution_percent'] = round((lines_changed / total_lines) * 100, 1)
        else:
            # Fallback to commit-based percentages
            total_commits = sum(c['commit_count'] for c in contributor_list)
            if total_commits > 0:
                for contrib in contributor_list:
                    contrib['contribution_percent'] = round((contrib['commit_count'] / total_commits) * 100, 1)
            else:
                for contrib in contributor_list:
                    contrib['contribution_percent'] = 0.0
    else:
        print("  No contributors found")
    
    return contributor_list


def populate_contributors_for_project(project: Project, since_date: Optional[str] = None, until_date: Optional[str] = None) -> int:
    """
    Extract Git contributors and populate the contributors table for a project.
    
    Args:
        project: Project database object
        since_date: Optional start date (format: YYYY-MM-DD)
        until_date: Optional end date (format: YYYY-MM-DD)
        
    Returns:
        Number of contributors added
    """
    print(f"\n{'='*60}")
    print(f"Populating Contributors for: {project.name}")
    print(f"{'='*60}")
    
    # Extract contributors from Git
    contributors = extract_git_contributors(project.file_path, since_date, until_date)
    
    if not contributors:
        print("\n⚠️  No Git contributors found")
        return 0
    
    # Add contributors to database
    print(f"\nStoring {len(contributors)} contributors in database...")
    
    added_count = 0
    for contrib in contributors:
        try:
            db_manager.add_contributor_to_project({
                'project_id': project.id,
                'name': contrib['name'],
                'contributor_identifier': contrib['email'],
                'commit_count': contrib['commit_count'],
                'lines_added': contrib['lines_added'],
                'lines_deleted': contrib['lines_deleted'],
                'contribution_percent': contrib['contribution_percent']
            })
            
            print(f"  ✓ {contrib['name']} ({contrib['email']})")
            print(f"    • Commits: {contrib['commit_count']}")
            print(f"    • Lines added: {contrib['lines_added']}")
            print(f"    • Lines deleted: {contrib['lines_deleted']}")
            print(f"    • Contribution: {contrib['contribution_percent']}%")
            added_count += 1
            
        except Exception as e:
            print(f"  ✗ Failed to add {contrib['name']}: {e}")
    
    print(f"\n✓ Successfully populated {added_count} contributors")
    return added_count


def populate_all_projects(since_date: Optional[str] = None, until_date: Optional[str] = None) -> None:
    """
    Populate contributors for all projects in the database that have Git repositories.
    
    Args:
        since_date: Optional start date (format: YYYY-MM-DD)
        until_date: Optional end date (format: YYYY-MM-DD)
    """
    print("\n" + "="*60)
    print("Populating Contributors for All Projects")
    print("="*60)
    
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("\n📭 No projects found in database")
        return
    
    processed = 0
    skipped = 0
    
    for project in projects:
        # Check if project path exists and is a directory
        if not os.path.exists(project.file_path):
            print(f"\n⚠️  Skipping '{project.name}': Path does not exist")
            skipped += 1
            continue
        
        if not os.path.isdir(project.file_path):
            print(f"\n⚠️  Skipping '{project.name}': Not a directory")
            skipped += 1
            continue
        
        # Check if already has contributors
        existing_contributors = db_manager.get_contributors_for_project(project.id)
        if existing_contributors:
            print(f"\n⚠️  Skipping '{project.name}': Already has {len(existing_contributors)} contributors")
            skipped += 1
            continue
        
        # Populate contributors
        count = populate_contributors_for_project(project, since_date, until_date)
        if count > 0:
            processed += 1
    
    print("\n" + "="*60)
    print(f"Summary:")
    print(f"  Projects processed: {processed}")
    print(f"  Projects skipped: {skipped}")
    print("="*60)


def populate_specific_project(project_name: str = None, project_id: int = None, since_date: Optional[str] = None, until_date: Optional[str] = None) -> None:
    """
    Populate contributors for a specific project.
    
    Args:
        project_name: Name of the project (optional)
        project_id: ID of the project (optional)
        since_date: Optional start date (format: YYYY-MM-DD)
        until_date: Optional end date (format: YYYY-MM-DD)
    """
    if project_id:
        project = db_manager.get_project(project_id)
    elif project_name:
        projects = db_manager.get_all_projects()
        project = next((p for p in projects if p.name == project_name), None)
    else:
        print("Error: Must provide either project_name or project_id")
        return
    
    if not project:
        print(f"❌ Project not found")
        return
    
    # Check if already has contributors
    existing_contributors = db_manager.get_contributors_for_project(project.id)
    if existing_contributors:
        print(f"\n⚠️  Project already has {len(existing_contributors)} contributors")
        print("\nExisting contributors:")
        for contrib in existing_contributors:
            print(f"  • {contrib.name} - {contrib.commit_count} commits, +{contrib.lines_added}/-{contrib.lines_deleted}")
        
        overwrite = input("\nDo you want to clear and re-extract? (y/n): ").strip().lower()
        if overwrite == 'y':
            # Delete existing contributors
            session = db_manager.get_session()
            try:
                for contrib in existing_contributors:
                    session.delete(contrib)
                session.commit()
                print("✓ Cleared existing contributors")
            except Exception as e:
                print(f"✗ Error clearing contributors: {e}")
                session.rollback()
            finally:
                session.close()
        else:
            print("Aborting.")
            return
    
    populate_contributors_for_project(project, since_date, until_date)


def verify_git_stats(project_path: str, since_date: Optional[str] = None, until_date: Optional[str] = None) -> None:
    """
    Show detailed Git statistics for verification against GitHub Insights.
    Uses the same extraction method as populate functions for consistency.
    
    Args:
        project_path: Path to the Git repository
        since_date: Optional start date (format: YYYY-MM-DD) 
        until_date: Optional end date (format: YYYY-MM-DD)
    """
    print("\n" + "="*60)
    print("Git Statistics Verification")
    print("="*60)
    
    if not is_git_repository(project_path):
        print(f"❌ Not a Git repository: {project_path}")
        return
    
    print("\nAnalyzing repository using git commands...")
    
    # Get contributors using the same method as extract_git_contributors
    contributors = extract_git_contributors(project_path, since_date, until_date)
    
    if not contributors:
        print("❌ No contributors found")
        return
    
    # Display results
    print("\n" + "="*60)
    print("Contributor Statistics (matching GitHub Insights)")
    print("="*60)
    
    # Sort by commits
    sorted_contribs = sorted(contributors, 
                            key=lambda x: x['commit_count'], 
                            reverse=True)
    
    total_commits = sum(c['commit_count'] for c in contributors)
    total_additions = sum(c['lines_added'] for c in contributors)
    total_deletions = sum(c['lines_deleted'] for c in contributors)
    
    for contrib in sorted_contribs:
        print(f"\n{contrib['name']} <{contrib['email']}>")
        print(f"  Commits: {contrib['commit_count']:,} ({contrib['commit_count']/total_commits*100:.1f}%)")
        print(f"  Lines added: {contrib['lines_added']:,}")
        print(f"  Lines deleted: {contrib['lines_deleted']:,}")
        print(f"  Net change: {contrib['lines_added'] - contrib['lines_deleted']:+,}")
        print(f"  Contribution: {contrib['contribution_percent']}%")
    
    print("\n" + "="*60)
    print("Repository Totals:")
    print(f"  Total commits (no merges): {total_commits:,}")
    print(f"  Total additions: {total_additions:,}")
    print(f"  Total deletions: {total_deletions:,}")
    print(f"  Net change: {total_additions - total_deletions:+,}")
    print("="*60)
    print("\n💡 Compare these with: GitHub Repository > Insights > Contributors")
    print("   (Make sure GitHub is showing 'All branches' and appropriate time range)")
    print("="*60)


# -----------------------------
# Manual Testing
# -----------------------------

def interactive_populate():
    """Interactive menu for populating contributors"""
    print("\n" + "="*60)
    print("Git Contributor Extraction Tool")
    print("="*60)
    print("\nOptions:")
    print("1. Populate contributors for all projects")
    print("2. Populate contributors for a specific project")
    print("3. Verify Git stats for a project (compare with GitHub)")
    print("4. Exit")
    
    choice = input("\nSelect an option (1-4): ").strip()
    
    # Ask for date range if option 1 or 2
    since_date = None
    until_date = None
    if choice in ["1", "2"]:
        use_dates = input("\nFilter by date range? (y/n, default matches GitHub): ").strip().lower()
        if use_dates == 'n':
            pass  # Use all history
        else:
            # Default to GitHub's typical contributor view dates
            since_date = input("Start date (YYYY-MM-DD) [default: 2025-08-24]: ").strip() or "2025-08-24"
            until_date = input("End date (YYYY-MM-DD) [default: today]: ").strip() or None
    
    if choice == "1":
        populate_all_projects(since_date, until_date)
    elif choice == "2":
        projects = db_manager.get_all_projects()
        if not projects:
            print("\n📭 No projects found in database")
            return
        
        print("\n=== Select a Project ===")
        for idx, project in enumerate(projects, start=1):
            print(f"{idx}. {project.name}")
        
        try:
            selection = int(input("\nSelect a project: ").strip())
            if 1 <= selection <= len(projects):
                project = projects[selection - 1]
                populate_specific_project(project_id=project.id, since_date=since_date, until_date=until_date)
            else:
                print("Invalid selection")
        except ValueError:
            print("Invalid input")
    elif choice == "3":
        projects = db_manager.get_all_projects()
        if not projects:
            print("\n📭 No projects found in database")
            return
        
        print("\n=== Select a Project ===")
        for idx, project in enumerate(projects, start=1):
            print(f"{idx}. {project.name} ({project.file_path})")
        
        try:
            selection = int(input("\nSelect a project: ").strip())
            if 1 <= selection <= len(projects):
                project = projects[selection - 1]
                
                # Ask for date range
                use_dates = input("\nFilter by date range? (y/n, default matches GitHub): ").strip().lower()
                verify_since = None
                verify_until = None
                if use_dates != 'n':
                    verify_since = input("Start date (YYYY-MM-DD) [default: 2025-08-24]: ").strip() or "2025-08-24"
                    verify_until = input("End date (YYYY-MM-DD) [default: today]: ").strip() or None
                
                verify_git_stats(project.file_path, verify_since, verify_until)
            else:
                print("Invalid selection")
        except ValueError:
            print("Invalid input")
    elif choice == "4":
        print("\nGoodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    interactive_populate()
