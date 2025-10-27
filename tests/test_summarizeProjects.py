import pytest
from src.Analysis.summarizeProjects import summarize_projects

def test_summarize_projects_basic():
    projects = [
        {"project_name": "Proj A", "time_spent": 50, "success_score": 0.8, "contribution_score": 0.9, "skills": ["Python", "Flask"]},
        {"project_name": "Proj B", "time_spent": 20, "success_score": 0.6, "contribution_score": 0.7, "skills": ["HTML", "CSS"]},
        {"project_name": "Proj C", "time_spent": 100, "success_score": 0.9, "contribution_score": 0.95, "skills": ["Python", "Data Analysis"]}
    ]

    result = summarize_projects(projects, top_k=2)

    # Verify shape of output
    assert "selected_projects" in result
    assert "summary" in result
    assert isinstance(result["selected_projects"], list)
    assert len(result["selected_projects"]) <= 2

    # Verify computed values
    for proj in result["selected_projects"]:
        assert 0 <= proj["overall_score"] <= 1

    # Verify narrative includes project count
    assert f"{len(result['selected_projects'])}" in result["summary"]

    
# --- Edge Case Tests ---

def test_empty_project_list():
    """Summarizer should handle an empty list gracefully."""
    result = summarize_projects([])
    assert result["selected_projects"] == []
    assert "no projects" in result["summary"].lower()


def test_single_project():
    """Summarizer should return the single project unchanged."""
    single = [
        {"project_name": "SoloProj", "time_spent": 30, "success_score": 0.8, "contribution_score": 0.85, "skills": ["Python"]},
    ]
    result = summarize_projects(single)
    assert len(result["selected_projects"]) == 1
    assert result["selected_projects"][0]["project_name"] == "SoloProj"


def test_identical_scores():
    """Summarizer should handle identical scores without crashing."""
    projects = [
        {"project_name": "Proj A", "time_spent": 10, "success_score": 0.8, "contribution_score": 0.8, "skills": ["Python"]},
        {"project_name": "Proj B", "time_spent": 10, "success_score": 0.8, "contribution_score": 0.8, "skills": ["HTML"]},
    ]
    result = summarize_projects(projects, top_k=2)
    assert len(result["selected_projects"]) == 2
    assert all(0 <= p["overall_score"] <= 1 for p in result["selected_projects"])


# --- Diversity Test ---

def test_diversity_selection_prefers_unique_skills():
    """Summarizer should prioritize projects with diverse skills."""
    projects = [
        {"project_name": "Proj A", "time_spent": 40, "success_score": 0.9, "contribution_score": 0.9, "skills": ["Python", "ML"]},
        {"project_name": "Proj B", "time_spent": 50, "success_score": 0.88, "contribution_score": 0.85, "skills": ["Python", "Flask"]},
        {"project_name": "Proj C", "time_spent": 60, "success_score": 0.92, "contribution_score": 0.9, "skills": ["React", "UI"]},
    ]

    result = summarize_projects(projects, top_k=2)
    selected = result["selected_projects"]
    all_skills = set(skill for p in selected for skill in p["skills"])

    assert len(selected) <= 2
    assert len(all_skills) > 2, "Expected diverse skill sets in selected projects"
