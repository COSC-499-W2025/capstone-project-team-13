import os
os.environ["GEMINI_API_KEY"] = "TEST_VALUE"
from src.AI.ai_project_ranker import AIProjectRanker

def fake_embed():
    return [0.1, 0.3, 0.5, 0.7]

def test_ranker_basic():
    ranker = AIProjectRanker()

    projects = [
        {"project_name": "A", "time_spent": 10, "success_score": 50, "contribution_score": 30, "skills": ["Python"], "embedding": fake_embed()},
        {"project_name": "B", "time_spent": 2, "success_score": 10, "contribution_score": 10, "skills": ["HTML"], "embedding": fake_embed()},
    ]

    result = ranker.rank(projects, top_k=1)

    assert len(result["selected"]) == 1
    assert result["selected"][0]["project_name"] == "A"


def test_skill_matching():
    ranker = AIProjectRanker(skill_alpha=0.3)

    projects = [
        {"project_name": "ML Project", "skills": ["Python", "ML"], "time_spent": 5, "success_score": 20, "contribution_score": 20, "embedding": fake_embed()},
        {"project_name": "Web Project", "skills": ["HTML"], "time_spent": 10, "success_score": 50, "contribution_score": 30, "embedding": fake_embed()},
    ]

    result = ranker.rank(projects, target_skills=["ML"], top_k=1)

    assert result["selected"][0]["project_name"] == "ML Project"


def test_diversity():
    ranker = AIProjectRanker(diversity_alpha=0.4)

    projects = [
        {"project_name": "A", "skills": ["Python"]},
        {"project_name": "B", "skills": ["React"]},
        {"project_name": "C", "skills": ["SQL"]},
    ]

    result = ranker.rank(projects, top_k=3)

    assert len(result["selected"]) == 3
    assert len(result["covered_skills"]) == 3
