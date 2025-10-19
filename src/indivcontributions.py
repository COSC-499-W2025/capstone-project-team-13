from collections import defaultdict

def extrapolate_individual_contributions(project_data: dict) -> dict:
    """
    Estimate contribution percentages for each contributor in a parsed project.
    Works across all file types (code, design, documentation, etc.).
    """
    contributors = defaultdict(lambda: {"files": 0, "lines": 0, "score": 0})

    for file in project_data.get("files", []):
        owner = file.get("owner")
        if owner:
            contributors[owner]["files"] += 1
            contributors[owner]["lines"] += file.get("lines", 0)

        for editor in file.get("editors", []):
            contributors[editor]["files"] += 0.5  # smaller weight for edits
            contributors[editor]["lines"] += file.get("lines", 0) * 0.3

    # Compute normalized contribution scores
    total_lines = sum(v["lines"] for v in contributors.values()) or 1
    for name, stats in contributors.items():
        stats["contribution_percent"] = round((stats["lines"] / total_lines) * 100, 1)

    return {"contributors": contributors}

