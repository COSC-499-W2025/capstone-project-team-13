from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import os
import sys
import re

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')
)
sys.path.insert(0, PROJECT_ROOT)

from src.Databases.database import db_manager, Project, Contributor
from src.Analysis.projectcollabtype import identify_project_type
from src.Analysis.indivcontributions import extrapolate_individual_contributions


# -----------------------------
# Suggested Roles
# -----------------------------

ROLE_OPTIONS: List[str] = [
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Team Lead",
    "Project Manager",
    "Researcher",
    "Designer",
    "Tester",
]


# -----------------------------
# Role Tiers Based on Contribution
# -----------------------------

def get_contribution_level(contribution_percent: float, is_collaborative: bool) -> str:
    """
    Get the contribution level prefix based on contribution percentage.
    
    Args:
        contribution_percent: Percentage of contribution (0-100)
        is_collaborative: Whether the project is collaborative
    
    Returns:
        Contribution level (e.g., "Lead", "Senior", "Contributing")
    """
    if not is_collaborative:
        return "Owner"
    
    # Tiered contribution levels for collaborative projects
    if contribution_percent >= 50:
        return "Lead"
    elif contribution_percent >= 25:
        return "Senior"
    elif contribution_percent >= 10:
        return "Contributing"
    elif contribution_percent > 0:
        return "Junior"
    else:
        return "Supporting"


def get_role_from_contribution(contribution_percent: float, is_collaborative: bool, role_type: str = "Developer") -> str:
    """
    Combine contribution level with role type to create full role title.
    
    Args:
        contribution_percent: Percentage of contribution (0-100)
        is_collaborative: Whether the project is collaborative
        role_type: The type of role (e.g., "Backend Developer", "Project Manager")
    
    Returns:
        Complete role title (e.g., "Lead Backend Developer", "Senior Project Manager")
    """
    contribution_level = get_contribution_level(contribution_percent, is_collaborative)
    
    if contribution_level == "Owner":
        return f"Owner / {role_type}"
    else:
        return f"{contribution_level} {role_type}"


# -----------------------------
# User Identification
# -----------------------------

def get_user_identifier(session: Session) -> str:
    """
    Prompt for or retrieve the user's identifier (name, email, or username)
    that matches contributor records in the database.
    """
    print("\n=== User Identification ===")
    print("To calculate your contribution percentage, we need to identify you.")
    print("Enter your name, email, or username as it appears in your Git commits.")
    print("Common formats: 'John Doe', 'john.doe@email.com', 'johndoe', etc.")
    
    while True:
        identifier = input("Your identifier: ").strip()
        if identifier:
            return identifier
        print("Please enter a valid identifier.")


def calculate_user_contribution(session: Session, project: Project, user_identifier: str) -> float:
    """
    Calculate the percentage of work completed by the user based on contributor data.
    Returns a percentage (0.0 to 100.0).
    """
    # Get all contributors for this project
    contributors = session.query(Contributor).filter(
        Contributor.project_id == project.id
    ).all()
    
    if not contributors:
        print("\nNo contributor data found for this project.")
        return 0.0
    
    # Try to find matching contributor by name (case-insensitive, partial match)
    user_contributor = None
    user_identifier_lower = user_identifier.lower()
    
    # First, try exact match
    for contrib in contributors:
        if contrib.name and contrib.name.lower() == user_identifier_lower:
            user_contributor = contrib
            break
        if contrib.contributor_identifier and contrib.contributor_identifier.lower() == user_identifier_lower:
            user_contributor = contrib
            break
    
    # If no exact match, try partial match
    if not user_contributor:
        for contrib in contributors:
            if contrib.name and user_identifier_lower in contrib.name.lower():
                user_contributor = contrib
                break
            if contrib.contributor_identifier and user_identifier_lower in contrib.contributor_identifier.lower():
                user_contributor = contrib
                break
    
    if not user_contributor:
        print(f"\nWarning: No contributor found matching '{user_identifier}'")
        print("Available contributors:")
        for contrib in contributors:
            display_name = contrib.name or contrib.contributor_identifier or "Unknown"
            print(f"  - {display_name} ({contrib.contribution_percent:.1f}%)")
        return 0.0
    
    # Return the stored contribution percentage
    contribution = user_contributor.contribution_percent
    print(f"\nFound contributor: {user_contributor.name or user_contributor.contributor_identifier}")
    print(f"Your contribution: {contribution:.1f}%")
    
    return contribution


def display_contribution_summary(session: Session, project: Project) -> None:
    """
    Display a summary of all contributors and their percentages.
    """
    contributors = session.query(Contributor).filter(
        Contributor.project_id == project.id
    ).order_by(Contributor.contribution_percent.desc()).all()
    
    if not contributors:
        print("\nNo contributor data available.")
        return
    
    print("\n=== Project Contributions ===")
    for contrib in contributors:
        name = contrib.name or contrib.contributor_identifier or "Unknown"
        print(f"  {name}: {contrib.contribution_percent:.1f}%")
        if contrib.commit_count > 0:
            print(f"    Commits: {contrib.commit_count}")
        if contrib.lines_added > 0 or contrib.lines_deleted > 0:
            print(f"    Lines: +{contrib.lines_added} / -{contrib.lines_deleted}")


# -----------------------------
# Prompt Logic
# -----------------------------

def prompt_user_role(collaboration_type: Optional[str] = None, contribution_percent: float = 0.0) -> str:
    print("\n=== Select Your Role on This Project ===")

    if collaboration_type:
        print(f"Detected project type: {collaboration_type}")

        if collaboration_type == "Individual Project":
            print("This appears to be an individual project.")
            print("You likely owned most or all responsibilities.")
        elif collaboration_type == "Collaborative Project":
            print("This appears to be a collaborative project.")
            print("Select the role that best represents your contribution.")    
    if contribution_percent > 0:
        print(f"\nYour contribution to this project: {contribution_percent:.1f}%")
    print()

    for idx, role in enumerate(ROLE_OPTIONS, start=1):
        print(f"{idx}. {role}")
    print("0. Other (type manually)")

    while True:
        choice = input("Select an option: ").strip()

        if choice.isdigit():
            choice = int(choice)

            if choice == 0:
                custom = input("Enter your role: ").strip()
                if custom:
                    return custom

            elif 1 <= choice <= len(ROLE_OPTIONS):
                return ROLE_OPTIONS[choice - 1]

        print("Invalid selection. Please try again.")


def prompt_manual_contribution() -> float:
    """
    Prompt user to manually enter their contribution percentage.
    """
    print("\n=== Manual Contribution Entry ===")
    print("Since Git contributor data is not available, please manually estimate your contribution.")
    print("Enter a value between 0 and 100 (e.g., 50 for 50%)")
    
    while True:
        try:
            value = input("Your contribution percentage: ").strip()
            contribution = float(value)
            if 0 <= contribution <= 100:
                return contribution
            else:
                print("Please enter a value between 0 and 100.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def assign_user_role(session: Session, project: Project, auto_assign: bool = True, project_data: Dict[str, Any] = None) -> None:
    """
    Assign a role to the user based on project type and contribution.
    
    Args:
        session: Database session
        project: Project object
        auto_assign: If True, automatically assign role based on contribution.
                     If False, prompt user for role selection.
        project_data: Optional parsed project data for contribution analysis
    """
    # Use provided project_data or create empty dict
    if project_data is None:
        project_data = {}
    
    # Detect collaboration type
    collaboration_type = identify_project_type(
        project.file_path,
        project_data=project_data
    )

    project.collaboration_type = collaboration_type
    is_collaborative = collaboration_type == "Collaborative Project"

    # Display contribution summary if available
    display_contribution_summary(session, project)

    # Calculate user contribution percentage
    contribution_percent = 0.0
    
    # Try to get contribution from project_data using indivcontributions
    if project_data and project_data.get("files"):
        contributions_result = extrapolate_individual_contributions(project_data)
        contributors_dict = contributions_result.get("contributors", {})
        
        if contributors_dict:
            print("\n=== Contribution Analysis ===")
            for name, stats in sorted(contributors_dict.items(), 
                                     key=lambda x: x[1]["contribution_percent"], 
                                     reverse=True):
                print(f"  {name}: {stats['contribution_percent']:.1f}%")
            
            if not is_collaborative:
                # For individual projects, user is the owner
                contribution_percent = 100.0
            else:
                # For collaborative projects, identify user's contribution
                if len(contributors_dict) == 1:
                    # Only one contributor found, assume it's the user
                    contributor_name = list(contributors_dict.keys())[0]
                    contribution_percent = contributors_dict[contributor_name]["contribution_percent"]
                else:
                    # Multiple contributors, ask user to identify themselves
                    user_identifier = get_user_identifier(session)
                    user_identifier_lower = user_identifier.lower()
                    
                    # Try to match user identifier
                    matched = False
                    for name, stats in contributors_dict.items():
                        if user_identifier_lower in name.lower():
                            contribution_percent = stats["contribution_percent"]
                            matched = True
                            print(f"\nMatched you as: {name} ({contribution_percent:.1f}%)")
                            break
                    
                    if not matched:
                        print(f"\nCould not match '{user_identifier}' to contributors.")
                        manual = input("Would you like to manually enter your contribution? (y/n): ").strip().lower()
                        if manual == 'y':
                            contribution_percent = prompt_manual_contribution()
    
    # Fallback: Check database contributor data
    if contribution_percent == 0.0:
        contributors = session.query(Contributor).filter(
            Contributor.project_id == project.id
        ).all()
        
        has_contributor_data = len(contributors) > 0
        
        if collaboration_type == "Collaborative Project":
            if has_contributor_data:
                print("\nGit contributor data is available for this project.")
                if auto_assign:
                    user_identifier = get_user_identifier(session)
                    contribution_percent = calculate_user_contribution(session, project, user_identifier)
                else:
                    calculate = input("Would you like to identify your contribution from Git data? (y/n): ").strip().lower()
                    if calculate == 'y':
                        user_identifier = get_user_identifier(session)
                        contribution_percent = calculate_user_contribution(session, project, user_identifier)
                    
                # If no match found, offer manual entry
                if contribution_percent == 0.0:
                    manual = input("\nWould you like to manually enter your contribution instead? (y/n): ").strip().lower()
                    if manual == 'y':
                        contribution_percent = prompt_manual_contribution()
            else:
                # No Git data available, offer manual entry
                print("\nNo Git contributor data found for this project.")
                manual = input("Would you like to manually enter your contribution percentage? (y/n): ").strip().lower()
                if manual == 'y':
                    contribution_percent = prompt_manual_contribution()
        elif collaboration_type == "Individual Project":
            contribution_percent = 100.0
            print("\nAs an individual project, your contribution is 100%.")

    # Assign role based on contribution and collaboration type
    if auto_assign:
        # First, get the role type from the user
        role_type = prompt_user_role(collaboration_type, contribution_percent)
        
        # Combine contribution level with role type
        role = get_role_from_contribution(contribution_percent, is_collaborative, role_type)
        
        contribution_level = get_contribution_level(contribution_percent, is_collaborative)
        print(f"\n=== Auto-Assigned Role ===")
        print(f"Based on your {contribution_percent:.1f}% contribution:")
        print(f"Contribution Level: {contribution_level}")
        print(f"Role Type: {role_type}")
        print(f"Complete Role: {role}")
        
        # Optionally allow override
        override = input("\nWould you like to change this role? (y/n): ").strip().lower()
        if override == 'y':
            role_type = prompt_user_role(collaboration_type, contribution_percent)
            role = get_role_from_contribution(contribution_percent, is_collaborative, role_type)
    else:
        # Manual role selection
        role_type = prompt_user_role(collaboration_type, contribution_percent)
        role = get_role_from_contribution(contribution_percent, is_collaborative, role_type)
    
    project.user_role = role
    project.user_contribution_percent = contribution_percent

    session.add(project)
    session.commit()

    print("\nSaved values:")
    print(f"  Role: {project.user_role}")
    print(f"  Collaboration Type: {project.collaboration_type}")
    print(f"  Your Contribution: {project.user_contribution_percent:.1f}%")


# -----------------------------
# Manual Testing
# -----------------------------

def select_project(session: Session) -> Optional[Project]:
    projects = session.query(Project).order_by(Project.name).all()

    if not projects:
        print("No projects found.")
        return None

    print("\n=== Select a Project ===")
    for idx, project in enumerate(projects, start=1):
        print(f"{idx}. {project.name}")

    while True:
        choice = input("Select a project: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                return projects[idx]
        print("Invalid selection. Please try again.")


def manual_test():
    print("\n=== Manual User Role Assignment Test ===")

    session = db_manager.get_session()

    try:
        project = select_project(session)
        if not project:
            return

        print(f"\nSelected project: {project.name}")
        print(f"Current role: {project.user_role}")
        print(f"Current collaboration type: {project.collaboration_type}")
        print(f"Current contribution: {project.user_contribution_percent:.1f}%")

        assign_user_role(session, project)

        session.refresh(project)

        print("\nVerification read-back:")
        print(f"  Role: {project.user_role}")
        print(f"  Collaboration Type: {project.collaboration_type}")
        print(f"  Contribution: {project.user_contribution_percent:.1f}%")

    finally:
        session.close()


# -----------------------------
# Entry Point
# -----------------------------

if __name__ == "__main__":
    manual_test()