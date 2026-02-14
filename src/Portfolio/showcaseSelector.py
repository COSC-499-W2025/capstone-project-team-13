"""
Allow users to interactively select which projects to showcase in portfolio.
By default, all projects are shown. Users can exclude specific projects.
"""

from typing import List, Tuple
from src.Databases.database import db_manager, Project


def list_projects_with_showcase_status() -> List[Tuple[Project, bool]]:
    """
    Get all projects with their showcase status.
    
    Returns:
        List of tuples: (project, is_showcased_bool)
        is_showcased = True if is_featured=True OR is_hidden=False (default show all)
    """
    projects = db_manager.get_all_projects(include_hidden=True) 
    
    # By default all projects are showcased unless explicitly hidden
    return [
        (project, not bool(project.is_hidden))
        for project in projects
    ]


def display_showcase_menu(projects_with_status: List[Tuple[Project, bool]]) -> None:
    """Display projects with showcase indicators"""
    print("\n" + "="*70)
    print("SELECT PROJECTS FOR PORTFOLIO SHOWCASE")
    print("="*70)
    print("\nLegend: [✓] = Showcased  [ ] = Hidden")
    print("-"*70)
    
    if not projects_with_status:
        print("No projects found in database.")
        return
    
    for i, (project, is_showcased) in enumerate(projects_with_status, 1):
        indicator = "[✓]" if is_showcased else "[ ]"
        project_type = project.project_type or "unknown"
        name = project.name[:50] + "..." if len(project.name) > 50 else project.name
        print(f"{i:2}. {indicator} {name} ({project_type})")
    
    print()


def toggle_project_showcase(project: Project) -> None:
    """Toggle showcase status for a single project"""
    # Always fetch fresh state from database before toggling
    session = db_manager.get_session()
    try:
        current_project = session.query(Project).filter(Project.id == project.id).first()
        if not current_project:
            print(f"\n❌ Project not found")
            return
        
        current_hidden = bool(current_project.is_hidden)
        new_hidden = not current_hidden
        
        # Update in same session
        current_project.is_hidden = new_hidden
        session.commit()
        
        status = "hidden from" if new_hidden else "added to"
        print(f"\n✓ '{project.name}' {status} showcase")
    finally:
        session.close()


def select_projects_interactive() -> None:
    """
    Interactive project selection menu.
    Allows toggling individual projects or bulk operations.
    """
    while True:
        projects_with_status = list_projects_with_showcase_status()
        
        if not projects_with_status:
            print("\nNo projects available.")
            input("\nPress Enter to continue...")
            return
        
        display_showcase_menu(projects_with_status)
        
        print("Options:")
        print("  [number] - Toggle project showcase status")
        print("  'all'    - Show all projects")
        print("  'none'   - Hide all projects")
        print("  'done'   - Save and exit")
        print()
        
        choice = input("Enter choice: ").strip().lower()
        
        if choice == 'done':
            showcased_count = sum(1 for _, is_showcased in projects_with_status if is_showcased)
            print(f"\n✅ Saved! {showcased_count} project(s) will be showcased in portfolio.")
            input("\nPress Enter to continue...")
            return
        
        elif choice == 'all':
            for project, _ in projects_with_status:
                db_manager.update_project(project.id, {"is_hidden": False})
            print("\n✓ All projects set to showcase")
            continue
        
        elif choice == 'none':
            for project, _ in projects_with_status:
                db_manager.update_project(project.id, {"is_hidden": True})
            print("\n✓ All projects hidden from showcase")
            continue
        
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(projects_with_status):
                project, _ = projects_with_status[idx]
                toggle_project_showcase(project)
            else:
                print("\n❌ Invalid project number")
        else:
            print("\n❌ Invalid choice. Please try again.")


def get_showcased_projects() -> List[Project]:
    """
    Get all projects that should be shown in portfolio.
    
    Returns:
        List of Project objects where is_hidden=False
    """
    all_projects = db_manager.get_all_projects(include_hidden=True)  # Get ALL projects first
    return [p for p in all_projects if not bool(p.is_hidden)]  # Then filter to showcased only


def run_showcase_selector():
    """Main entry point for showcase selection"""
    select_projects_interactive()


if __name__ == "__main__":
    run_showcase_selector()