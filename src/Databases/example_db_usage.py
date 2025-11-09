# src/example_db_usage.py
from src.Databases.database import db_manager
from datetime import datetime, timezone
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
    'file_name': 'main.py',  
    'file_type': '.py',
    'file_size': 2048,
    'file_created': datetime(2024, 1, 15),
    'file_modified': datetime(2024, 9, 20)
})

file2 = db_manager.add_file_to_project({
    'project_id': project.id,
    'file_path': '/home/user/projects/my_project/app.js',
    'file_type': '.js',
    'file_name': 'app.js',  
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

# ============ EXAMPLE 2: Text/Document Project ============

print("\n=== EXAMPLE 2: Text/Document Project ===\n")

# Create a text project
text_project = db_manager.create_project({
    'name': 'Technical Writing Portfolio',
    'file_path': '/home/user/documents/writing_portfolio',
    'description': 'Collection of technical documentation and articles',
    'date_created': datetime(2024, 3, 1),
    'date_modified': datetime(2024, 10, 15),
    'lines_of_code': 0,  # Not applicable for text projects
    'word_count': 15000,  # Total word count across all documents
    'file_count': 8,
    'total_size_bytes': 524288,  # 512 KB
    'project_type': 'text',
    'collaboration_type': 'solo',
    'languages': [],  # Not applicable for text projects
    'frameworks': [],  # Not applicable for text projects
    'skills': ['technical writing', 'research', 'documentation'],
    'tags': ['PDF', 'Markdown', 'Word']  # Document types
})

print(f"✅ Created text project: {text_project.name} (ID: {text_project.id})")
print(f"   - Document types: {', '.join(text_project.tags)}")
print(f"   - Word count: {text_project.word_count:,}")
print(f"   - Skills: {', '.join(text_project.skills)}")

# Add document files
doc1 = db_manager.add_file_to_project({
    'project_id': text_project.id,
    'file_path': '/home/user/documents/writing_portfolio/user_guide.pdf',
    'file_name': 'user_guide.pdf',
    'file_type': 'PDF',
    'file_size': 102400,  # 100 KB
    'relative_path': 'user_guide.pdf',
    'file_created': datetime(2024, 3, 1),
    'file_modified': datetime(2024, 9, 10),
    'lines_of_code': 0  # Not applicable for documents
})

doc2 = db_manager.add_file_to_project({
    'project_id': text_project.id,
    'file_path': '/home/user/documents/writing_portfolio/api_docs.md',
    'file_name': 'api_docs.md',
    'file_type': 'Markdown',
    'file_size': 51200,  # 50 KB
    'relative_path': 'api_docs.md',
    'file_created': datetime(2024, 4, 15),
    'file_modified': datetime(2024, 10, 5),
    'lines_of_code': 0
})

print(f"✅ Added {len(db_manager.get_files_for_project(text_project.id))} documents")

# Add keywords for text project
db_manager.add_keyword({
    'project_id': text_project.id,
    'keyword': 'documentation',
    'score': 0.92,
    'category': 'text'
})

db_manager.add_keyword({
    'project_id': text_project.id,
    'keyword': 'technical communication',
    'score': 0.85,
    'category': 'text'
})

print(f"✅ Added {len(db_manager.get_keywords_for_project(text_project.id))} keywords")


# ============ RETRIEVE AND DISPLAY DATA ============


# ============ Display Statistics ============

print("\n=== Overall Statistics ===\n")
stats = db_manager.get_stats()
for key, value in stats.items():
    print(f"{key}: {value}")