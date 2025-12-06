from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Any, Optional
import math
from copy import deepcopy
from src.AI.ai_service import get_ai_service


class AIProjectRanker:

    def __init__(
        self,
        weights: Dict[str, float] = None,
        skill_alpha: float = 0.25,
        semantic_alpha: float = 0.35,
        diversity_alpha: float = 0.15,
    ):
        # Weighting for normalized metrics
        self.weights = weights or {
            "time": 0.4,
            "success": 0.3,
            "contribution": 0.3
        }

        self.skill_alpha = skill_alpha      # additional boost
        self.semantic_alpha = semantic_alpha
        self.diversity_alpha = diversity_alpha

        # AI service (if embedding logic is used)
        self.ai_service = get_ai_service()

    # ----------------------------------------
    # Helpers
    # ----------------------------------------

    def _min_max(self, vals):
        if not vals:
            return [0] * len(vals)
        lo, hi = min(vals), max(vals)
        if lo == hi:
            return [1] * len(vals)
        return [(v - lo) / (hi - lo) for v in vals]

    def _cosine(self, a, b):
        if not a or not b:
            return 0
        dot = sum(x * y for x, y in zip(a, b))
        mag1 = math.sqrt(sum(x * x for x in a))
        mag2 = math.sqrt(sum(x * x for x in b))
        if mag1 == 0 or mag2 == 0:
            return 0
        return dot / (mag1 * mag2)

    # ----------------------------------------
    # Main Ranking Function
    # ----------------------------------------

    def rank(
        self,
        projects: List[Dict[str, Any]],
        target_skills: Optional[List[str]] = None,
        top_k: int = 3,
        target_embedding: Optional[List[float]] = None
    ):
        if not projects:
            return {"selected": [], "all_scored": []}

        items = deepcopy(projects)

        # Ensure baseline fields
        for p in items:
            p.setdefault("skills", [])
            p.setdefault("time_spent", 0.0)
            p.setdefault("success_score", 0.0)
            p.setdefault("contribution_score", 0.0)
            p.setdefault("lines_of_code", 0)
            p.setdefault("file_count", 0)
            p.setdefault("contributors", [])
            p.setdefault("embedding", None)

        # Infer missing metrics
        for p in items:

            # A) Time spent from LOC
            if p.get("time_spent", 0) == 0:
                loc = p.get("lines_of_code", 0)
                p["time_spent"] = max(1, loc / 500)

            # B) Success score from file_count + LOC
            if p.get("success_score", 0) == 0:
                files = p.get("file_count", 1)
                loc = p.get("lines_of_code", 1)
                p["success_score"] = min(100, (files * 5) + (loc / 200)) / 100

            # C) Contribution score from contributors
            if p.get("contribution_score", 0) == 0:
                contributors = p.get("contributors", [])
                if isinstance(contributors, list) and len(contributors) > 0:
                    p["contribution_score"] = 1 / len(contributors)
                else:
                    p["contribution_score"] = 1.0

        # Normalize metrics
        t_norm = self._min_max([p["time_spent"] for p in items])
        s_norm = self._min_max([p["success_score"] for p in items])
        c_norm = self._min_max([p["contribution_score"] for p in items])

        # Compute scores
        for i, p in enumerate(items):

            # Base weighted score
            base = (
                self.weights["time"] * t_norm[i] +
                self.weights["success"] * s_norm[i] +
                self.weights["contribution"] * c_norm[i]
            )

            # Skill matching
            skill_score = 0
            if target_skills:
                overlap = len(set(p["skills"]) & set(target_skills))
                if overlap > 0:
                    skill_score = 2.0

            # Semantic similarity
            semantic = 0
            if p.get("embedding") and target_embedding:
                semantic = self.semantic_alpha * self._cosine(
                    p["embedding"], target_embedding
                )

            # Final combined score
            p["_rank_score"] = max(0, min(1.5, base + skill_score + semantic))

        # Diversity-aware Top-k
        selected, seen_skills = [], set()
        remaining = sorted(items, key=lambda x: x["_rank_score"], reverse=True)

        for _ in range(min(top_k, len(remaining))):
            best_idx, best_val = None, -999

            for i, p in enumerate(remaining):
                new_skills = set(p["skills"]) - seen_skills
                diversity_bonus = self.diversity_alpha if new_skills else 0
                score = p["_rank_score"] + diversity_bonus

                if score > best_val:
                    best_val = score
                    best_idx = i

            chosen = remaining.pop(best_idx)
            selected.append(chosen)
            seen_skills.update(chosen["skills"])

        # Final output
        return {
            "selected": selected,
            "all_scored": items,
            "covered_skills": sorted(seen_skills),
            "summary": f"Ranked {len(items)} projects using metrics, skills, semantic similarity, and diversity."
        }
