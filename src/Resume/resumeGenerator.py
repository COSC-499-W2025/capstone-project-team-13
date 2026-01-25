"""
Resume Generator
================

Generates a complete resume document from projects with stored bullets.

Features:
- Ask for user's full name for resume header
- Let user select which projects to include
- Let user specify order of projects
- Generate formatted resume with all selected projects
- Display complete resume for review

Usage:
    from src.Resume.resumeGenerator import generate_full_resume
    generate_full_resume()
"""

import os
import sys
from typing import List, Tuple, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Databases.database import db_manager, Project


def get_projects_with_bullets() -> List[Project]:
    """
    Get all projects that have bullets stored
    
    Returns:
        List of Project objects that have bullets
    """
    projects = db_manager.get_all_projects()
    return [p for p in projects if p.bullets is not None]


def display_projects_for_selection(projects: List[Project]) -> None:
    """
    Display projects available for resume inclusion
    
    Args:
        projects: List of projects with bullets
    """
    print("\n" + "="*70)
    print("AVAILABLE PROJECTS")
    print("="*70)
    
    for i, project in enumerate(projects, 1):
        bullets_data = project.bullets
        num_bullets = bullets_data['num_bullets'] if bullets_data else 0
        project_type = project.project_type or "unknown"
        
        print(f"{i}. {project.name} ({project_type}) - {num_bullets} bullets")
    
    print()


def select_projects_for_resume(projects: List[Project]) -> List[Project]:
    """
    Let user select which projects to include in resume
    
    Args:
        projects: List of available projects with bullets
        
    Returns:
        List of selected projects
    """
    if not projects:
        return []
    
    display_projects_for_selection(projects)
    
    print("Select projects to include in your resume:")
    print("Enter project numbers separated by commas (e.g., 1,3,5)")
    print("Or enter 'all' to include all projects")
    print("Or enter 'c' to cancel")
    
    choice = input("\nYour selection: ").strip().lower()
    
    if choice == 'c':
        return []
    
    if choice == 'all':
        return projects
    
    try:
        # Parse comma-separated numbers
        indices = [int(x.strip()) - 1 for x in choice.split(',')]
        
        # Validate indices
        selected = []
        for idx in indices:
            if 0 <= idx < len(projects):
                selected.append(projects[idx])
            else:
                print(f"Warning: Ignoring invalid project number {idx + 1}")
        
        return selected
    
    except ValueError:
        print("Invalid input. Please enter numbers separated by commas.")
        input("Press Enter to continue...")
        return []


def order_projects(projects: List[Project]) -> List[Project]:
    """
    Let user specify the order of projects in the resume
    
    Args:
        projects: List of selected projects
        
    Returns:
        List of projects in user-specified order
    """
    if len(projects) <= 1:
        return projects
    
    print("\n" + "="*70)
    print("ORDER PROJECTS")
    print("="*70)
    print("\nCurrent order:")
    for i, project in enumerate(projects, 1):
        print(f"{i}. {project.name}")
    
    print("\nOptions:")
    print("1. Keep current order")
    print("2. Reverse order")
    print("3. Reorder manually")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == '1':
        return projects
    elif choice == '2':
        return list(reversed(projects))
    elif choice == '3':
        return manual_reorder(projects)
    else:
        print("Invalid choice. Keeping current order.")
        return projects


def manual_reorder(projects: List[Project]) -> List[Project]:
    """
    Manually reorder projects by entering new sequence
    
    Args:
        projects: List of projects to reorder
        
    Returns:
        Reordered list of projects
    """
    print("\nEnter the new order as numbers separated by commas")
    print("For example, to put project 3 first, then 1, then 2: enter '3,1,2'")
    
    for i, project in enumerate(projects, 1):
        print(f"{i}. {project.name}")
    
    try:
        order_input = input("\nNew order: ").strip()
        indices = [int(x.strip()) - 1 for x in order_input.split(',')]
        
        # Validate that all indices are present
        if len(indices) != len(projects):
            print(f"Error: You must specify all {len(projects)} projects.")
            return projects
        
        if len(set(indices)) != len(indices):
            print("Error: Cannot use the same project twice.")
            return projects
        
        # Reorder
        reordered = []
        for idx in indices:
            if 0 <= idx < len(projects):
                reordered.append(projects[idx])
            else:
                print(f"Error: Invalid project number {idx + 1}")
                return projects
        
        return reordered
    
    except (ValueError, IndexError):
        print("Invalid input. Keeping original order.")
        return projects


def format_resume_header(full_name: str) -> str:
    """
    Format the resume header with user's name
    
    Args:
        full_name: User's full name
        
    Returns:
        Formatted header string
    """
    header = []
    header.append("=" * 70)
    header.append(full_name.upper().center(70))
    header.append("=" * 70)
    header.append("")
    
    return "\n".join(header)


def format_project_section(project: Project) -> str:
    """
    Format a single project section with header and bullets
    
    Args:
        project: Project object with stored bullets
        
    Returns:
        Formatted project section
    """
    bullets_data = project.bullets
    if not bullets_data:
        return ""
    
    section = []
    section.append(bullets_data['header'])
    section.append("")
    
    for bullet in bullets_data['bullets']:
        section.append(f"• {bullet}")
    
    section.append("")
    
    return "\n".join(section)


def generate_resume_document(full_name: str, projects: List[Project]) -> str:
    """
    Generate complete resume document
    
    Args:
        full_name: User's full name
        projects: Ordered list of projects to include
        
    Returns:
        Complete formatted resume as string
    """
    resume_parts = []
    
    # Header
    resume_parts.append(format_resume_header(full_name))
    
    # Projects section
    resume_parts.append("PROJECTS")
    resume_parts.append("-" * 70)
    resume_parts.append("")
    
    # Add each project
    for project in projects:
        project_section = format_project_section(project)
        if project_section:
            resume_parts.append(project_section)
    
    # Footer
    resume_parts.append("-" * 70)
    resume_parts.append(f"Generated on: {datetime.now().strftime('%B %d, %Y')}")
    
    return "\n".join(resume_parts)


def generate_full_resume() -> None:
    """
    Main function to generate a full resume interactively
    
    Workflow:
    1. Check for projects with bullets
    2. Get user's full name
    3. Let user select projects
    4. Let user order projects
    5. Generate and display resume
    """
    print("\n" + "="*70)
    print("FULL RESUME GENERATOR")
    print("="*70)
    
    # Get projects with bullets
    projects = get_projects_with_bullets()
    
    if not projects:
        print("\nNo projects with bullets found.")
        print("Generate bullets for your projects first before creating a resume.")
        input("\nPress Enter to continue...")
        return
    
    print(f"\nFound {len(projects)} project(s) with bullets.")
    
    # Get user's full name
    print("\n" + "-"*70)
    full_name = input("Enter your full name for the resume header: ").strip()
    
    if not full_name:
        print("Name is required to generate a resume.")
        input("Press Enter to continue...")
        return
    
    # Select projects
    selected_projects = select_projects_for_resume(projects)
    
    if not selected_projects:
        print("\nNo projects selected. Resume generation cancelled.")
        input("Press Enter to continue...")
        return
    
    print(f"\n{len(selected_projects)} project(s) selected.")
    
    # Order projects
    ordered_projects = order_projects(selected_projects)
    
    # Generate resume
    print("\n" + "="*70)
    print("GENERATING RESUME...")
    print("="*70)
    
    resume = generate_resume_document(full_name, ordered_projects)
    
    # Display resume
    print("\n" + "="*70)
    print("YOUR RESUME")
    print("="*70)
    print()
    print(resume)
    print()
    
    # Summary
    total_bullets = sum(len(p.bullets['bullets']) for p in ordered_projects)
    print("="*70)
    print(f"Resume Summary:")
    print(f"  • Projects included: {len(ordered_projects)}")
    print(f"  • Total bullet points: {total_bullets}")
    print("="*70)
    
    input("\nPress Enter to continue...")


if __name__ == "__main__":
    generate_full_resume()