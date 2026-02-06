"""
Enhanced Deletion - User-facing deletion functions
"""
from src.deletion_manager import DeletionManager
from src.Databases.database import db_manager


def delete_project_enhanced():
    """
    User-facing project deletion with shared file protection.
    """
    manager = DeletionManager()

    # Get project ID
    project_id = input("Enter project ID to delete: ").strip()
    if not project_id.isdigit():
        print("❌ Invalid project ID.")
        return

    project_id = int(project_id)
    
    # Verify project exists
    project = db_manager.get_project(project_id)
    if not project:
        print(f"❌ Project {project_id} not found.")
        return
    
    # Show project info
    print(f"\n📁 Project: {project.name}")
    print(f"   Type: {project.project_type}")
    
    # Check for shared files
    shared_files = manager.get_shared_files(project_id)
    if shared_files:
        print(f"\n⚠️  {len(shared_files)} file(s) are shared with other projects and will be PROTECTED.")
        print("   (Files will NOT be deleted from disk)")

    # Confirm deletion
    confirm = input("\nProceed with deletion? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Deletion cancelled.")
        return

    # Delete
    print("\n🔄 Deleting project...")
    result = manager.delete_project_safely(project_id, delete_shared_files=False)

    # Show results
    if result["project_deleted"]:
        print("✅ Project deleted safely.")
        if result["files_protected"] > 0:
            print(f"   Protected {result['files_protected']} shared file(s)")
    else:
        error = result.get("error", "Unknown error")
        print(f"❌ Failed to delete project: {error}")


def bulk_delete_projects():
    """
    Bulk delete multiple projects by ID with shared file protection.
    """
    manager = DeletionManager()

    ids_input = input("Enter project IDs to delete (comma-separated): ").strip()
    if not ids_input:
        print("No IDs provided. Cancelled.")
        return

    raw_ids = [s.strip() for s in ids_input.split(",") if s.strip()]
    if not raw_ids or not all(s.isdigit() for s in raw_ids):
        print("Invalid input. Please enter numeric IDs separated by commas.")
        return

    project_ids = [int(s) for s in raw_ids]

    print("\nProjects to delete:", ", ".join(str(i) for i in project_ids))
    confirm = input("Proceed with deletion? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Bulk deletion cancelled.")
        return

    deleted = 0
    failed = []
    for pid in project_ids:
        result = manager.delete_project_safely(pid, delete_shared_files=False)
        if result.get("project_deleted"):
            deleted += 1
        else:
            failed.append(pid)

    print(f"\nDeleted {deleted} project(s).")
    if failed:
        print("Failed to delete IDs:", ", ".join(str(i) for i in failed))


def view_shared_files_report():
    """
    Show a report of shared files across projects.
    """
    manager = DeletionManager()
    projects = db_manager.get_all_projects(include_hidden=True)
    if not projects:
        print("No projects found.")
        return

    any_shared = False
    print("\nShared Files Report:")
    print("-" * 60)

    for p in projects:
        shared = manager.get_shared_files(p.id)
        if shared:
            any_shared = True
            print(f"Project {p.id}: {p.name}")
            for path in shared[:10]:
                print(f"  - {path}")
            if len(shared) > 10:
                print(f"  ... and {len(shared) - 10} more")
            print()

    if not any_shared:
        print("No shared files detected.")


def delete_ai_insights():
    """
    Delete AI insights for a single project.
    """
    manager = DeletionManager()
    
    # Get project ID
    project_id = input("Enter project ID: ").strip()
    if not project_id.isdigit():
        print("❌ Invalid project ID.")
        return
    
    project_id = int(project_id)
    
    # Verify project exists
    project = db_manager.get_project(project_id)
    if not project:
        print(f"❌ Project {project_id} not found.")
        return
    
    # Show what will be deleted
    print(f"\n📁 Project: {project.name}")
    has_ai = hasattr(project, 'ai_description') and project.ai_description
    print(f"   AI description: {'Yes' if has_ai else 'No'}")
    
    if not has_ai:
        print("\n✅ No AI insights to delete.")
        return
    
    # Confirm
    confirm = input("\nDelete AI insights? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Deletion cancelled.")
        return
    
    # Delete
    print("\n🔄 Deleting AI insights...")
    result = manager.delete_ai_insights_for_project(project_id)
    
    # Show results
    if result["success"]:
        print("✅ AI insights deleted.")
        print(f"   Cache files deleted: {result['cache_deleted']}")
    else:
        error = result.get("error", "Unknown error")
        print(f"❌ Failed: {error}")
