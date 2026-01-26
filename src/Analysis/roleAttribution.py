from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import os
import sys

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
# Contribution Analysis
# -----------------------------

def calculate_user_contribution(session: Session, project: Project, user_identifier: str) -> float:
    """
    Calculate the percentage of work completed by the user based on contributor data.
    Returns a percentage (0.0 to 100.0).
    """
    contributors = session.query(Contributor).filter(
        Contributor.project_id == project.id
    ).all()
    
    if not contributors:
        return 0.0
    
    user_identifier_lower = user_identifier.lower()
    for contrib in contributors:
        if contrib.name and contrib.name.lower() == user_identifier_lower:
            return contrib.contribution_percent
        if contrib.contributor_identifier and contrib.contributor_identifier.lower() == user_identifier_lower:
            return contrib.contribution_percent
    
    return 0.0


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

    contribution_percent = 0.0
    
    # Try to get contribution from project_data using indivcontributions
    if project_data and project_data.get("files"):
        contributions_result = extrapolate_individual_contributions(project_data)
        contributors_dict = contributions_result.get("contributors", {})
        
        if contributors_dict:
            user_identifier = input("Enter your identifier: ").strip()
            contribution_percent = contributors_dict.get(user_identifier, {}).get("contribution_percent", 0.0)
    
    # Fallback: Check database contributor data
    if contribution_percent == 0.0:
        user_identifier = input("Enter your identifier: ").strip()
        contribution_percent = calculate_user_contribution(session, project, user_identifier)
    
    role_type = input("Enter your role type: ").strip()
    role = get_role_from_contribution(contribution_percent, is_collaborative, role_type)
    
    project.user_role = role
    project.user_contribution_percent = contribution_percent

    session.add(project)
    session.commit()

    print(f"Role assigned: {role}")


def display_project_contributors(session: Session, project: Project) -> None:
    """
    Display all contributors for the selected project.
    """
    contributors = session.query(Contributor).filter(
        Contributor.project_id == project.id
    ).order_by(Contributor.contribution_percent.desc()).all()

    if not contributors:
        print("\nNo contributors found for this project.")
    else:
        print("\n=== Contributors for Project: {} ===".format(project.name))
        for contrib in contributors:
            name = contrib.name or contrib.contributor_identifier or "Unknown"
            print(f"  {name}: {contrib.contribution_percent:.1f}%")
            if contrib.commit_count > 0:
                print(f"    Commits: {contrib.commit_count}")
            if contrib.lines_added > 0 or contrib.lines_deleted > 0:
                print(f"    Lines: +{contrib.lines_added} / -{contrib.lines_deleted}")


def identify_user_role(session: Session, project: Project) -> str:
    """
    Identify the user's role based on their username and contribution percentage.

    Args:
        session: Database session.
        project: The selected project.

    Returns:
        The complete role title.
    """
    # Display contributors for the project
    contributors = session.query(Contributor).filter(
        Contributor.project_id == project.id
    ).order_by(Contributor.contribution_percent.desc()).all()

    if not contributors:
        print("\nNo contributors found for this project. Automatically assigning 'Project Owner' as the role.")
        role = "Project Owner"
        project.user_role = role
        session.add(project)
        session.commit()
        print(f"\nRole assigned: {role}")
        return role

    print("\n=== Contributors for Project: {} ===".format(project.name))
    print("Note: Duplicates may exist based on username or email being used for commits.")
    for idx, contrib in enumerate(contributors, start=1):
        name = contrib.name or contrib.contributor_identifier or "Unknown"
        print(f"{idx}. {name}: {contrib.contribution_percent:.1f}%")

    # Prompt for contributor selection
    while True:
        try:
            choice = int(input("\nInsert number to select user's contributor: ").strip())
            if 1 <= choice <= len(contributors):
                selected_contributor = contributors[choice - 1]
                contribution_percent = selected_contributor.contribution_percent
                break
            else:
                print("Invalid selection. Please choose a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Determine pretext based on contribution percentage
    if contribution_percent >= 65:
        pretext = "Project Owner"
    elif contribution_percent >= 50:
        pretext = "Lead Collaborator"
    elif contribution_percent >= 22.5:
        pretext = "Major Contributor"
    elif contribution_percent >= 10:
        pretext = "Contributor"
    elif contribution_percent > 0:
        pretext = "Junior Contributor"
    else:
        pretext = "Observer"

    # Provide a list of common job titles
    job_titles = [
        "Technical Lead",
        "Backend Developer",
        "Frontend Developer",
        "Full Stack Developer",
        "Project Manager",
        "Designer",
        "Tester",
        "Researcher",
    ]

    print("\n=== Select a Job Title ===")
    for idx, title in enumerate(job_titles, start=1):
        print(f"{idx}. {title}")
    print("0. Manually Type")

    # Allow the user to select a job title
    while True:
        try:
            choice = int(input("\nSelect a job title by number: ").strip())
            if choice == 0:
                job_title = input("Enter your job title: ").strip()
                if job_title:
                    break
            elif 1 <= choice <= len(job_titles):
                job_title = job_titles[choice - 1]
                break
            else:
                print("Invalid selection. Please choose a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Combine pretext and job title into a complete role
    role = f"{pretext} - {job_title}"

    # Allow the user to manually override the generated role
    print(f"\nGenerated Role: {role}")
    manual_override = input("\nWould you like to manually enter a full job title instead? (y/n): ").strip().lower()
    if manual_override == 'y':
        role = input("Enter your full job title: ").strip()

    # Store the role in the database
    project.user_role = role
    session.add(project)
    session.commit()

    print(f"\nRole assigned: {role}")
    return role


def lookup_roles():
    """
    Function to look up roles assigned to projects.
    """
    session = db_manager.get_session()
    try:
        projects = session.query(Project).order_by(Project.name).all()
        if not projects:
            print("No projects found in the database.")
        else:
            print("\n=== Project Roles ===")
            for project in projects:
                role = project.user_role or "No role assigned"
                print(f"{project.name}: {role}")
    finally:
        input("\nPress Enter to continue...")                
        session.close()


# -----------------------------
# Entry Point
# -----------------------------

def test_role_attribution():
    """
    Function to test the roleAttribution functionality.
    """
    session = db_manager.get_session()
    try:
        projects = session.query(Project).order_by(Project.name).all()
        if not projects:
            print("No projects found in the database.")
        else:
            print("\n=== Available Projects ===")
            for idx, project in enumerate(projects, start=1):
                print(f"{idx}. {project.name}")

            while True:
                try:
                    choice = int(input("\nSelect a project by number: ").strip())
                    if 1 <= choice <= len(projects):
                        selected_project = projects[choice - 1]
                        display_project_contributors(session, selected_project)

                        # Identify and assign the user's role
                        identify_user_role(session, selected_project)

                        # Pause to let the user see the role
                        input("\nPress Enter to continue...")
                        break
                    else:
                        print("Invalid selection. Please choose a valid project number.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
    finally:
        session.close()


if __name__ == "__main__":
    test_role_attribution()