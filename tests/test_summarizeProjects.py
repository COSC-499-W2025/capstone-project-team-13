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
