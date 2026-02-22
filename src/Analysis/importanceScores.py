# src/Analysis/importanceScores.py
# Importance scoring for MEDIA and TEXT projects only.
# Coding projects are handled by a separate module.

from src.Databases.database import db_manager, Project
from datetime import datetime, timezone
import math
from sqlalchemy.orm import joinedload

# ------------------------
#  MEDIA & TEXT SCORING FORMULA
# ------------------------
def calculate_importance_score(project):
    """
    Returns a percentage-based importance score (0-100) for media and text projects.
    Scoring reflects project quality, depth, and completeness.
    
    For TEXT projects: Emphasizes content volume (word_count), keyword richness, and skill diversity
    For MEDIA projects: Emphasizes file variety, software sophistication, and technical depth
    
    Note: Does not use lines_of_code as these are media/text projects.
    """
    
    # If project is detached from session, re-fetch with eager loading
    if project.id:
        try:
            session = db_manager.get_session()
            project = session.query(Project).filter(Project.id == project.id).options(
                joinedload(Project.keywords),
                joinedload(Project.skills),
                joinedload(Project.languages),
                joinedload(Project.tags),
                joinedload(Project.files)
            ).first()
            session.close()
        except Exception:
            # If re-fetch fails, continue with what we have
            pass
    
    # Determine project type and route to appropriate scorer
    project_type = getattr(project, 'project_type', 'text').lower()
    
    if 'media' in project_type or 'visual' in project_type:
        return _score_media_project(project)
    else:  # text or default
        return _score_text_project(project)


def _score_text_project(project):
    """
    Score for TEXT projects.
    Emphasizes: content volume, keyword richness, skill breadth, file structure, and recency.
    """
    # 1. Content Volume (45%) - word_count primary, size-based fallback
    word_count = project.word_count or 0
    total_size_mb = (project.total_size_bytes or 0) / (1024 * 1024)
    # Word scale: 1500 words = 25%, 5000 = 60%, 12000+ = 100%
    word_volume_score = min(word_count / 12000, 1) * 100
    # Piecewise logarithmic size scale:
    # 0-1 MB ramps to ~70%, 1-20 MB ramps to 100%
    if total_size_mb <= 1.0:
        size_volume_score = min(math.log1p(total_size_mb) / math.log1p(1.0), 1) * 70
    else:
        size_volume_score = 70 + min(math.log1p(total_size_mb - 1.0) / math.log1p(19.0), 1) * 30
    # Use the stronger signal (helps when word_count isn't populated)
    content_volume_score = max(word_volume_score, size_volume_score)
    # Content floor for real text collections
    if total_size_mb >= 0.2 or word_count >= 500:
        content_volume_score = max(content_volume_score, 40)

    # 2. Keyword Richness (20%) - indicates depth and topical diversity
    try:
        keyword_count = len(project.keywords) if project.keywords else 0
    except Exception:
        keyword_count = 0
    # Scale: 8 keywords = 30%, 20 = 75%, 35+ = 100%
    keyword_richness_score = min(keyword_count / 35, 1) * 100

    # 3. Skill Diversity (15%) - breadth of expertise demonstrated
    try:
        skill_count = len(project.skills) if project.skills else 0
    except Exception:
        skill_count = 0
    # Scale: 2 skills = 25%, 5 = 60%, 9+ = 100%
    skill_diversity_score = min(skill_count / 9, 1) * 100

    # 4. File Structure (10%) - more distinct files implies organization
    file_count = project.file_count or 0
    # Scale: 2 files = 20%, 6 = 60%, 12+ = 100%
    file_structure_score = min(file_count / 12, 1) * 100

    # 5. Recency (10%) - recent work is slightly favored
    now = datetime.now(timezone.utc)
    date_modified = project.date_modified
    if date_modified:
        if date_modified.tzinfo is None:
            date_modified = date_modified.replace(tzinfo=timezone.utc)
        days_since_update = (now - date_modified).days
        recency_score = max(0, min(1, (730 - days_since_update) / 730)) * 100  # 2-year window
    else:
        recency_score = 0
    
    # Weighted combination
    total_score = (
        content_volume_score * 0.45 +
        keyword_richness_score * 0.20 +
        skill_diversity_score * 0.15 +
        file_structure_score * 0.10 +
        recency_score * 0.10
    )
    
    return round(total_score, 2)


def _score_media_project(project):
    """
    Score for MEDIA projects.
    Emphasizes: file volume/size, tool usage, keyword richness, skill diversity, and recency.
    """
    
    # 1. File Complexity & Volume (55%) - more files + larger size = more complex project
    try:
        file_count_actual = len(project.files) if project.files else 0
    except Exception:
        file_count_actual = 0
    file_count = project.file_count or file_count_actual or 0
    total_size_mb = (project.total_size_bytes or 0) / (1024 * 1024)
    
    # Scale: 10 files = 33%, 20 files = 66%, 30+ = 100%
    file_complexity_score = min(file_count / 30, 1) * 100
    
    # Scale: 100 MB = 20%, 300 MB = 60%, 500+ MB = 100%
    size_complexity_score = min(total_size_mb / 500, 1) * 100
    
    complexity_score = (file_complexity_score * 0.7 + size_complexity_score * 0.3)
    
    # 2. Software/Tool Proficiency (20%) - sophisticated tools indicate higher skill level
    try:
        software_count = len(project.languages) if project.languages else 0  # media stores software in languages field
    except Exception:
        software_count = 0
    try:
        tags_count = len(project.tags) if project.tags else 0
    except Exception:
        tags_count = 0
    
    # More tools = higher skill ceiling. Scale: 1 tool = 25%, 3 = 60%, 8+ = 100%
    tool_proficiency_score = min((software_count + tags_count) / 8, 1) * 100
    
    # 3. Keyword Richness (10%) - metadata about the project content
    try:
        keyword_count = len(project.keywords) if project.keywords else 0
    except Exception:
        keyword_count = 0
    # Scale: 3 keywords = 20%, 10 = 60%, 25+ = 100%
    keyword_richness_score = min(keyword_count / 25, 1) * 100
    
    # 4. Skill Diversity (10%) - range of skills needed for project
    try:
        skill_count = len(project.skills) if project.skills else 0
    except Exception:
        skill_count = 0
    # Scale: 1-2 skills = 25%, 3-4 = 60%, 6+ = 100%
    skill_diversity_score = min(skill_count / 6, 1) * 100
    
    # 5. Recency (5%) - less critical for creative work than for text
    now = datetime.now(timezone.utc)
    date_modified = project.date_modified
    if date_modified:
        if date_modified.tzinfo is None:
            date_modified = date_modified.replace(tzinfo=timezone.utc)
        days_since_update = (now - date_modified).days
        recency_score = max(0, min(1, (1095 - days_since_update) / 1095)) * 100  # 3-year window
    else:
        recency_score = 0
    
    # Weighted combination
    total_score = (
        complexity_score * 0.55 +
        tool_proficiency_score * 0.20 +
        keyword_richness_score * 0.10 +
        skill_diversity_score * 0.10 +
        recency_score * 0.05
    )
    
    return round(total_score, 2)


# ------------------------
# APPLY SCORES TO THE DB
# ------------------------
def assign_importance_scores():
    """
    Loads media and text projects with related data eagerly loaded,
    computes quality-based score for each, and saves the score back to the database.
    
    Filters for project_type in ['media', 'text', 'visual_media'].
    """
    session = db_manager.get_session()
    try:
        projects = session.query(Project).filter(
            Project.project_type.in_(['media', 'text', 'visual_media'])
        ).options(
            joinedload(Project.contributors),
            joinedload(Project.files),
            joinedload(Project.keywords),
            joinedload(Project.skills),
            joinedload(Project.languages),
            joinedload(Project.tags)
        ).all()

        if not projects:
            print("No media or text projects found.")
            return []

        results = []

        for p in projects:
            score = calculate_importance_score(p)

            # Save score back into DB as success_score
            p.success_score = score
            session.add(p)

            results.append((p, score))

        session.commit()
        return results
    finally:
        session.close()


if __name__ == "__main__":
    scored = assign_importance_scores()
    for p, s in scored:
        print(f"[{p.id}] {p.name} → {s}")