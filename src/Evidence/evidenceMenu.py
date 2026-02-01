"""
Evidence Menu - Interactive interface for managing evidence
Allows users to view, add, edit, and delete evidence for projects
"""

from typing import Optional
from src.Evidence.evidenceManager import evidence_manager
from src.Databases.database import db_manager


def clear_screen():
    """Clear console screen"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def select_project() -> Optional[int]:
    """
    Allow user to select a project from database
    
    Returns:
        Project ID or None if cancelled
    """
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("❌ No projects found in database.")
        print("   Please upload a project first.")
        return None
    
    print("Select a project:\n")
    for i, project in enumerate(projects, 1):
        print(f"{i}. {project.name}")
        if project.project_type:
            print(f"   Type: {project.project_type}")
        if project.file_path:
            print(f"   Path: {project.file_path}")
        print()
    
    print("0. Cancel")
    
    choice = input("\nEnter project number: ").strip()
    
    if choice == '0':
        return None
    
    try:
        index = int(choice) - 1
        if 0 <= index < len(projects):
            return projects[index].id
        else:
            print("❌ Invalid selection.")
            return None
    except ValueError:
        print("❌ Invalid input.")
        return None


def view_evidence_menu():
    """View evidence for a project"""
    clear_screen()
    print_header("View Project Evidence")
    
    project_id = select_project()
    if not project_id:
        return
    
    project = db_manager.get_project(project_id)
    print(f"\n📊 Evidence for: {project.name}")
    print("=" * 70)
    
    summary = evidence_manager.get_summary(project_id)
    print(summary)
    
    input("\n\nPress Enter to continue...")


def add_metric_menu():
    """Add a manual metric to a project"""
    clear_screen()
    print_header("Add Manual Metric")
    
    project_id = select_project()
    if not project_id:
        return
    
    project = db_manager.get_project(project_id)
    print(f"\nAdding metric to: {project.name}")
    print("-" * 70)
    
    print("\nExamples of metrics:")
    print("  - users: Number of active users")
    print("  - revenue: Revenue generated ($)")
    print("  - performance_improvement: Performance increase (%)")
    print("  - uptime: System uptime (%)")
    print("  - response_time: Average response time (ms)")
    print()
    
    metric_name = input("Metric name: ").strip()
    if not metric_name:
        print("❌ Metric name cannot be empty.")
        input("Press Enter to continue...")
        return
    
    metric_value = input("Metric value: ").strip()
    if not metric_value:
        print("❌ Metric value cannot be empty.")
        input("Press Enter to continue...")
        return
    
    # Try to convert to number if possible
    try:
        if '.' in metric_value:
            metric_value = float(metric_value)
        else:
            metric_value = int(metric_value)
    except ValueError:
        # Keep as string
        pass
    
    description = input("Description (optional): ").strip()
    
    success = evidence_manager.add_manual_metric(
        project_id, metric_name, metric_value, description
    )
    
    if success:
        print(f"\n✅ Metric '{metric_name}' added successfully!")
    else:
        print(f"\n❌ Failed to add metric.")
    
    input("\nPress Enter to continue...")


def add_feedback_menu():
    """Add feedback/testimonial to a project"""
    clear_screen()
    print_header("Add Feedback/Testimonial")
    
    project_id = select_project()
    if not project_id:
        return
    
    project = db_manager.get_project(project_id)
    print(f"\nAdding feedback to: {project.name}")
    print("-" * 70)
    
    print("\nEnter feedback text (press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    
    feedback_text = '\n'.join(lines)
    
    if not feedback_text.strip():
        print("❌ Feedback cannot be empty.")
        input("Press Enter to continue...")
        return
    
    source = input("\nFeedback source (e.g., 'Client', 'Professor'): ").strip()
    
    rating_input = input("Rating (1-5, optional): ").strip()
    rating = None
    if rating_input:
        try:
            rating = int(rating_input)
            if not 1 <= rating <= 5:
                print("⚠️  Rating must be between 1 and 5. Ignoring rating.")
                rating = None
        except ValueError:
            print("⚠️  Invalid rating. Ignoring.")
    
    success = evidence_manager.add_feedback(
        project_id, feedback_text, source, rating
    )
    
    if success:
        print(f"\n✅ Feedback added successfully!")
    else:
        print(f"\n❌ Failed to add feedback.")
    
    input("\nPress Enter to continue...")


def add_achievement_menu():
    """Add achievement/award to a project"""
    clear_screen()
    print_header("Add Achievement/Award")
    
    project_id = select_project()
    if not project_id:
        return
    
    project = db_manager.get_project(project_id)
    print(f"\nAdding achievement to: {project.name}")
    print("-" * 70)
    
    print("\nExamples of achievements:")
    print("  - Won 1st place at hackathon")
    print("  - Featured on company blog")
    print("  - Received A+ grade")
    print("  - Selected for production deployment")
    print()
    
    achievement = input("Achievement description: ").strip()
    if not achievement:
        print("❌ Achievement cannot be empty.")
        input("Press Enter to continue...")
        return
    
    date = input("Date (YYYY-MM-DD, optional): ").strip()
    
    success = evidence_manager.add_achievement(
        project_id, achievement, date if date else None
    )
    
    if success:
        print(f"\n✅ Achievement added successfully!")
    else:
        print(f"\n❌ Failed to add achievement.")
    
    input("\nPress Enter to continue...")


def extract_auto_evidence_menu():
    """Automatically extract evidence from project files"""
    clear_screen()
    print_header("Automatically Extract Evidence")
    
    project_id = select_project()
    if not project_id:
        return
    
    project = db_manager.get_project(project_id)
    print(f"\nExtracting evidence from: {project.name}")
    print(f"Project path: {project.file_path}")
    print("-" * 70)
    
    print("\n🔍 Scanning project files for evidence...")
    print("   Looking for:")
    print("   - README badges (CI/CD, coverage, quality)")
    print("   - Test coverage reports")
    print("   - Git statistics")
    print("   - Documentation metrics")
    print()
    
    try:
        evidence = evidence_manager.extract_and_store_evidence(project, project.file_path)
        
        if evidence:
            print("✅ Evidence extracted successfully!\n")
            print("Found evidence:")
            for key, value in evidence.items():
                print(f"  - {key}: {value}")
        else:
            print("⚠️  No evidence found in project files.")
            print("   You can add evidence manually using the other menu options.")
    
    except Exception as e:
        print(f"❌ Error extracting evidence: {e}")
    
    input("\n\nPress Enter to continue...")


def clear_evidence_menu():
    """Clear all evidence for a project"""
    clear_screen()
    print_header("Clear Project Evidence")
    
    project_id = select_project()
    if not project_id:
        return
    
    project = db_manager.get_project(project_id)
    print(f"\n⚠️  WARNING: This will delete ALL evidence for: {project.name}")
    print("=" * 70)
    
    # Show current evidence
    summary = evidence_manager.get_summary(project_id)
    print("\nCurrent evidence:")
    print(summary)
    
    confirm = input("\n\nAre you sure you want to delete all evidence? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        success = evidence_manager.clear_evidence(project_id)
        if success:
            print("\n✅ Evidence cleared successfully.")
        else:
            print("\n❌ Failed to clear evidence.")
    else:
        print("\n❌ Cancelled.")
    
    input("\nPress Enter to continue...")


def evidence_main_menu():
    """Main evidence management menu"""
    while True:
        clear_screen()
        print_header("Evidence Management")
        
        print("Manage evidence of success for your projects:")
        print()
        print("1. View Evidence for Project")
        print("2. Automatically Extract Evidence")
        print("3. Add Manual Metric")
        print("4. Add Feedback/Testimonial")
        print("5. Add Achievement/Award")
        print("6. Clear Evidence for Project")
        print("7. Back to Main Menu")
        print()
        
        choice = input("Enter your choice (1-7): ").strip()
        
        if choice == '1':
            view_evidence_menu()
        elif choice == '2':
            extract_auto_evidence_menu()
        elif choice == '3':
            add_metric_menu()
        elif choice == '4':
            add_feedback_menu()
        elif choice == '5':
            add_achievement_menu()
        elif choice == '6':
            clear_evidence_menu()
        elif choice == '7':
            print("\nReturning to main menu...")
            return
        else:
            print("❌ Invalid choice. Please enter 1-7.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    print("Testing Evidence Menu")
    evidence_main_menu()
