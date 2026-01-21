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


def assign_user_role(session: Session, project: Project) -> None:
    """
    Prompt the user and store the role on the project.
    Also detects and stores collaboration type and user contribution percentage.
    """

    # Detect collaboration type (best-effort)
    collaboration_type = identify_project_type(
        project.file_path,
        project_data={}  # placeholder; richer data can be passed later
    )

    project.collaboration_type = collaboration_type

    # Display contribution summary if available
    display_contribution_summary(session, project)

    # Calculate user contribution percentage
    contribution_percent = 0.0
    
    # Check if contributor data exists
    contributors = session.query(Contributor).filter(
        Contributor.project_id == project.id
    ).all()
    
    has_contributor_data = len(contributors) > 0
    
    if collaboration_type == "Collaborative Project":
        if has_contributor_data:
            print("\nGit contributor data is available for this project.")
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
                # User declined Git matching, offer manual entry
                manual = input("Would you like to manually enter your contribution percentage? (y/n): ").strip().lower()
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

    # Prompt for role with contribution context
    role = prompt_user_role(collaboration_type, contribution_percent)
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