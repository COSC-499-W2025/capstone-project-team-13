def showcase_projects(projects):
    print("\nAvailable Projects:")
    for p in projects:
        print(f"- {p['id']}: {p['name']}")

    # Step 1: Select projects
    selected_ids = input("\nEnter project IDs to showcase (comma-separated): ")
    selected_ids = [int(pid.strip()) for pid in selected_ids.split(",")]

    attribute_map = {}
    skill_map = {}

    # Step 2: Collect user choices (NO processing yet)
    for project in projects:
        if project["id"] not in selected_ids:
            continue

        print(f"\nCustomizing project: {project['name']}")

        print("Available attributes:", ", ".join(project.keys()))
        attrs = input("Attributes to display (comma-separated): ")
        attribute_map[project["id"]] = [a.strip() for a in attrs.split(",")]

        if "skills" in project:
            print("Available skills:", ", ".join(project["skills"]))
            skills = input("Skills to highlight (comma-separated, or leave blank): ")

            if skills:
                skill_map[project["id"]] = [s.strip() for s in skills.split(",")]

    # Step 3: Ranking choice
    rank_attr = input("\nEnter attribute to re-rank projects by (or press Enter to skip): ")
    rank_attr = rank_attr if rank_attr else None

    final_projects = process_showcase(
        projects,
        selected_ids,
        attribute_map,
        skill_map,
        rank_attr
    )

    print("\nFinal Showcase:")
    for p in final_projects:
        print(p)

    return final_projects
  

def process_showcase(projects, selected_ids, attribute_map, skill_map, rank_attr=None):
    """
    Core logic for project showcasing.
    This function contains NO user input and is fully testable.
    """

    # Select chosen projects
    selected_projects = [p for p in projects if p["id"] in selected_ids]
    final_projects = []

    # Apply attribute & skill filtering
    for project in selected_projects:
        attrs = attribute_map.get(project["id"], project.keys())
        filtered = {k: project[k] for k in attrs if k in project}

        if "skills" in project and project["id"] in skill_map:
            filtered["highlighted_skills"] = [
                s for s in project["skills"]
                if s in skill_map[project["id"]]
            ]

        final_projects.append(filtered)

    # Re-rank projects if requested
    if rank_attr:
        final_projects.sort(
            key=lambda x: x.get(rank_attr, 0),
            reverse=True
        )

    return final_projects

