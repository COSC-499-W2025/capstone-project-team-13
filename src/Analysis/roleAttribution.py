from typing import List, Optional
from sqlalchemy.orm import Session
import os
import sys

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')
)
sys.path.insert(0, PROJECT_ROOT)

from src.Databases.database import db_manager, Project
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
# Prompt Logic
# -----------------------------

def prompt_user_role(collaboration_type: Optional[str] = None) -> str:
    print("\n=== Select Your Role on This Project ===")

    if collaboration_type:
        print(f"Detected project type: {collaboration_type}")

        if collaboration_type == "Individual Project":
            print("This appears to be an individual project.")
            print("You likely owned most or all responsibilities.")
        elif collaboration_type == "Collaborative Project":
            print("This appears to be a collaborative project.")
            print("Select the role that best represents your contribution.")

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


def assign_user_role(session: Session, project: Project) -> None:
    """
    Prompt the user and store the role on the project.
    Also detects and stores collaboration type.
    """

    # Detect collaboration type (best-effort)
    collaboration_type = identify_project_type(
        project.file_path,
        project_data={}  # placeholder; richer data can be passed later
    )

    project.collaboration_type = collaboration_type

    role = prompt_user_role(collaboration_type)
    project.user_role = role

    session.add(project)
    session.commit()

    print("\nSaved values:")
    print(f"  Role: {project.user_role}")
    print(f"  Collaboration Type: {project.collaboration_type}")


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

        assign_user_role(session, project)

        session.refresh(project)

        print("\nVerification read-back:")
        print(f"  Role: {project.user_role}")
        print(f"  Collaboration Type: {project.collaboration_type}")

    finally:
        session.close()


# -----------------------------
# Entry Point
# -----------------------------

if __name__ == "__main__":
    manual_test()
