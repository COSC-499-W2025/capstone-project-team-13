import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ["GEMINI_API_KEY"] = "TEST_VALUE"

from src.AI.ai_project_ranker import AIProjectRanker


# ---------------------------
# Helper fake embedding
# ---------------------------
def fake_embed():
    return [0.1, 0.3, 0.5, 0.7]


# ---------------------------
# Basic ranking test
# ---------------------------
def test_ranker_basic():
    ranker = AIProjectRanker()

    projects = [
        {"project_name": "A", "time_spent": 10, "success_score": 50, "contribution_score": 30,
         "skills": ["Python"], "embedding": fake_embed()},
        {"project_name": "B", "time_spent": 2, "success_score": 10, "contribution_score": 10,
         "skills": ["HTML"], "embedding": fake_embed()},
    ]

    result = ranker.rank(projects, top_k=1)

    assert len(result["selected"]) == 1
    assert result["selected"][0]["project_name"] == "A"


# ---------------------------
# Skill matching test
# Ensures skill boosting works
# ---------------------------
def test_skill_matching():
    ranker = AIProjectRanker()

    projects = [
        {"project_name": "ML Project", "skills": ["Python", "ML"], "time_spent": 5,
         "success_score": 20, "contribution_score": 20, "embedding": fake_embed()},
        {"project_name": "Web Project", "skills": ["HTML"], "time_spent": 10,
         "success_score": 50, "contribution_score": 30, "embedding": fake_embed()},
    ]

    result = ranker.rank(projects, target_skills=["ML"], top_k=1)

    assert result["selected"][0]["project_name"] == "ML Project"



# Diversity test
# Ensures diverse skill coverage

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



# NEW: Test semantic similarity
def test_semantic_similarity():
    ranker = AIProjectRanker()

    p1 = {
        "project_name": "Match",
        "embedding": [1, 0],
        "skills": [],
        "time_spent": 1, "success_score": 1, "contribution_score": 1
    }

    p2 = {
        "project_name": "No Match",
        "embedding": [0, 1],
        "skills": [],
        "time_spent": 1, "success_score": 1, "contribution_score": 1
    }

    result = ranker.rank(
        [p1, p2],
        top_k=1,
        target_embedding=[1, 0]
    )

    assert result["selected"][0]["project_name"] == "Match"



#Empty input test
def test_empty_input():
    ranker = AIProjectRanker()
    result = ranker.rank([])
    assert result == {"selected": [], "all_scored": []}


# NEW: Malformed project handling
def test_malformed_project():
    ranker = AIProjectRanker()

    bad_projects = [
        {"project_name": "X"}  # Missing many fields
    ]

    result = ranker.rank(bad_projects, top_k=1)

    # Should still produce a valid result
    assert "selected" in result
    assert len(result["selected"]) >= 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
