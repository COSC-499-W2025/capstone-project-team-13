# src/example_db_usage.py
from src.Databases.database import db_manager
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ============ DATABASE 1: Store Project Data ============

print("=== DATABASE 1: Project Data ===\n")

# Create a project
project = db_manager.create_project({
    'name': 'My Python Project',
    'file_path': '/home/user/projects/my_project',
    'date_created': datetime(2024, 1, 15),
    'date_modified': datetime(2024, 10, 1),
    'lines_of_code': 5000,
    'file_count': 50,
    'project_type': 'code',
    'languages': ['Python', 'JavaScript'],
    'frameworks': ['Django', 'React']
})

print(f"✅ Created project: {project.name} (ID: {project.id})")

# Add files
file1 = db_manager.add_file_to_project({
    'project_id': project.id,
    'file_path': '/home/user/projects/my_project/main.py',
    'file_type': '.py',
    'file_size': 2048,
    'file_created': datetime(2024, 1, 15),
    'file_modified': datetime(2024, 9, 20)
})

file2 = db_manager.add_file_to_project({
    'project_id': project.id,
    'file_path': '/home/user/projects/my_project/app.js',
    'file_type': '.js',
    'file_size': 1536,
    'file_created': datetime(2024, 2, 10),
    'file_modified': datetime(2024, 9, 25)
})

print(f"✅ Added {len(db_manager.get_files_for_project(project.id))} files")

# Add contributors
contributor1 = db_manager.add_contributor_to_project({
    'project_id': project.id,
    'name': 'Alice Smith',
    'contributor_identifier': 'alice@example.com',
    'commit_count': 120
})

contributor2 = db_manager.add_contributor_to_project({
    'project_id': project.id,
    'name': 'Bob Jones',
    'contributor_identifier': 'bob@example.com',
    'commit_count': 45
})

print(f"✅ Added {len(db_manager.get_contributors_for_project(project.id))} contributors")


# ============ Display Statistics ============

print("\n=== Overall Statistics ===\n")
stats = db_manager.get_stats()
for key, value in stats.items():
    print(f"{key}: {value}")